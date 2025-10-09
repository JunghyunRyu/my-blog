import asyncio
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import aiofiles
from playwright.async_api import async_playwright, Page, Response
from .config import Config
from .auth_manager import AuthManager

class CokacScraper:
    """코드깎는노인 사이트 트랜스크립트 스크래퍼"""
    
    def __init__(self):
        self.config = Config()
        self.auth_manager = AuthManager()
        self.transcript_data = []
        self.api_responses = []
        
    async def scrape_lecture(self, lecture_url: str) -> List[Dict[str, Any]]:
        """
        강의 페이지의 트랜스크립트 스크래핑
        
        Args:
            lecture_url: 스크래핑할 강의 URL
            
        Returns:
            추출된 트랜스크립트 데이터 리스트
        """
        print(f"🎯 강의 스크래핑 시작: {lecture_url}")
        
        # URL 유효성 검사
        if not self._is_valid_cokac_url(lecture_url):
            print(f"❌ 유효하지 않은 코드깎는노인 URL입니다: {lecture_url}")
            return []
        
        async with async_playwright() as p:
            try:
                browser, context = await self.auth_manager.create_authenticated_context(p)
                page = await context.new_page()
                
                # 네트워크 응답 후킹 설정
                await self._setup_network_interceptor(page)
                
                # 강의 페이지 접속
                print(f"📡 페이지 접속 중...")
                await page.goto(lecture_url, wait_until='domcontentloaded', timeout=self.config.TIMEOUT)
                
                # 페이지 로드 완료 대기
                await page.wait_for_timeout(3000)
                
                # 페이지 접근 권한 확인
                if await self._check_access_denied(page):
                    print("❌ 페이지 접근 권한이 없습니다. 로그인 상태를 확인해주세요.")
                    return []
                
                # 트랜스크립트 영역 확인
                has_transcript = await self._check_transcript_availability(page)
                if not has_transcript:
                    print("⚠️ 이 강의에는 트랜스크립트가 없는 것 같습니다.")
                    return []
                
                print("📜 트랜스크립트 로딩을 시작합니다...")
                
                # 스마트 스크롤로 모든 트랜스크립트 로드
                await self._smart_scroll_and_load(page)
                
                # 2초 대기 (지연 로딩 완료)
                await page.wait_for_timeout(2000)
                
                # DOM에서 트랜스크립트 추출
                transcript_data = await self._extract_transcript_from_dom(page)
                
                # API 응답에서도 데이터 추출 시도
                api_transcript_data = await self._process_api_responses()
                
                # 두 소스의 데이터 병합 및 정제
                final_data = self._merge_transcript_data(transcript_data, api_transcript_data)
                
                # 결과 저장
                if final_data:
                    await self._save_transcript_data(lecture_url, final_data)
                    print(f"✅ 스크래핑 완료: {len(final_data)}개의 트랜스크립트 추출")
                else:
                    print("⚠️ 추출된 트랜스크립트가 없습니다.")
                
                return final_data
                
            except Exception as e:
                print(f"❌ 스크래핑 중 오류 발생: {e}")
                print(f"오류 상세: {type(e).__name__}")
                return []
            finally:
                if 'browser' in locals():
                    await browser.close()
    
    def _is_valid_cokac_url(self, url: str) -> bool:
        """코드깎는노인 사이트 URL 유효성 검사"""
        return url.startswith(self.config.BASE_URL)
    
    async def _setup_network_interceptor(self, page: Page):
        """네트워크 응답 후킹으로 API 데이터 캡처"""
        async def handle_response(response: Response):
            url = response.url
            # 트랜스크립트, 자막, 캡션 관련 API 응답 감지
            if any(keyword in url.lower() for keyword in [
                'transcript', 'caption', 'subtitle', 'cue', 'srt', 'vtt',
                'text', 'script', '자막', '스크립트'
            ]):
                try:
                    if response.ok and response.headers.get('content-type', '').startswith(('application/json', 'text/')):
                        print(f"📡 API 응답 캡처: {url}")
                        
                        # JSON 응답 처리
                        if 'json' in response.headers.get('content-type', ''):
                            data = await response.json()
                        else:
                            data = await response.text()
                        
                        self.api_responses.append({
                            'source': 'api',
                            'url': url,
                            'data': data,
                            'content_type': response.headers.get('content-type', ''),
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    print(f"API 응답 처리 중 오류: {e}")
        
        page.on('response', handle_response)
    
    async def _check_access_denied(self, page: Page) -> bool:
        """페이지 접근 권한 확인"""
        try:
            # 일반적인 접근 거부 패턴 확인
            access_denied_indicators = [
                '로그인이 필요합니다',
                '접근 권한이 없습니다',
                '권한이 없습니다',
                'Access Denied',
                'Unauthorized',
                '403',
                '401'
            ]
            
            page_text = await page.evaluate("() => document.body.innerText")
            return any(indicator in page_text for indicator in access_denied_indicators)
            
        except Exception:
            return False
    
    async def _check_transcript_availability(self, page: Page) -> bool:
        """트랜스크립트 사용 가능 여부 확인"""
        try:
            # 트랜스크립트 관련 요소 존재 확인
            transcript_selectors = [
                self.config.TRANSCRIPT_SELECTOR,
                self.config.TRANSCRIPT_CONTAINER,
                '[class*="transcript"]',
                '[class*="caption"]',
                '[class*="subtitle"]',
                '[data-testid*="transcript"]'
            ]
            
            for selector in transcript_selectors:
                element = await page.query_selector(selector)
                if element:
                    return True
            
            # 텍스트 기반 확인
            page_text = await page.evaluate("() => document.body.innerText")
            transcript_keywords = ['transcript', '자막', '스크립트', '대본']
            
            return any(keyword in page_text.lower() for keyword in transcript_keywords)
            
        except Exception:
            return True  # 확인 실패 시 시도해보기
    
    async def _smart_scroll_and_load(self, page: Page):
        """스마트 스크롤로 지연 로딩 컨텐츠 모두 로드"""
        print("📜 트랜스크립트 전체 로딩을 위한 스마트 스크롤 시작...")
        
        scroll_script = f"""
            async () => {{
                const scrollStep = {self.config.SCROLL_STEP};
                const scrollDelay = {self.config.SCROLL_DELAY};
                const maxScrolls = {self.config.MAX_SCROLL_ATTEMPTS};
                const idleThreshold = {self.config.IDLE_THRESHOLD};
                
                // 스크롤 가능한 컨테이너 찾기
                const containers = [
                    document.querySelector('{self.config.TRANSCRIPT_CONTAINER}'),
                    document.querySelector('[class*="video-player"]'),
                    document.scrollingElement,
                    document.body
                ].filter(el => el);
                
                const container = containers[0];
                
                let previousHeight = 0;
                let previousTranscriptCount = 0;
                let unchangedCount = 0;
                let scrollCount = 0;
                
                console.log('스크롤 시작, 컨테이너:', container?.tagName);
                
                while (unchangedCount < idleThreshold && scrollCount < maxScrolls) {{
                    // 스크롤 실행
                    container.scrollBy(0, scrollStep);
                    await new Promise(resolve => setTimeout(resolve, scrollDelay));
                    
                    // 변화 감지
                    const currentHeight = container.scrollHeight || document.body.scrollHeight;
                    const currentTranscriptCount = document.querySelectorAll('{self.config.TRANSCRIPT_SELECTOR}').length;
                    
                    // 높이나 트랜스크립트 개수 변화 확인
                    if (currentHeight === previousHeight && currentTranscriptCount === previousTranscriptCount) {{
                        unchangedCount++;
                    }} else {{
                        unchangedCount = 0;
                        previousHeight = currentHeight;
                        previousTranscriptCount = currentTranscriptCount;
                    }}
                    
                    scrollCount++;
                    
                    // 진행 상황 로그
                    if (scrollCount % 10 === 0) {{
                        console.log(`스크롤 진행: ${{scrollCount}}/${{maxScrolls}}, 트랜스크립트: ${{currentTranscriptCount}}개`);
                    }}
                    
                    // 맨 아래 도달 확인
                    if (container.scrollTop + container.clientHeight >= container.scrollHeight - 100) {{
                        console.log('스크롤 끝에 도달');
                        break;
                    }}
                }}
                
                console.log(`스크롤 완료: 총 ${{scrollCount}}회, 최종 트랜스크립트: ${{previousTranscriptCount}}개`);
                return {{ scrollCount, transcriptCount: previousTranscriptCount }};
            }}
        """
        
        result = await page.evaluate(scroll_script)
        print(f"   📊 스크롤 결과: {result.get('scrollCount', 0)}회, 트랜스크립트: {result.get('transcriptCount', 0)}개")
        
        # 최종 안전 대기
        await page.wait_for_timeout(1000)
    
    async def _extract_transcript_from_dom(self, page: Page) -> List[Dict[str, Any]]:
        """DOM에서 트랜스크립트 텍스트 추출"""
        print("🔍 DOM에서 트랜스크립트 추출 중...")
        
        extraction_script = f"""
            () => {{
                const transcriptElements = document.querySelectorAll('{self.config.TRANSCRIPT_SELECTOR}');
                const results = [];
                
                console.log(`트랜스크립트 요소 발견: ${{transcriptElements.length}}개`);
                
                transcriptElements.forEach((element, index) => {{
                    const text = element.textContent?.trim();
                    if (text && text.length > 0) {{
                        // 타임스탬프 찾기
                        let timestamp = '';
                        let timestampElement = null;
                        
                        // 여러 방법으로 타임스탬프 요소 찾기
                        const parent = element.closest('div, li, span, article, section');
                        if (parent) {{
                            // 형제 요소에서 찾기
                            timestampElement = parent.querySelector('{self.config.TIMESTAMP_SELECTOR}');
                            if (!timestampElement) {{
                                // 클래스명으로 찾기
                                timestampElement = parent.querySelector('[class*="time"], [class*="stamp"], [class*="duration"]');
                            }}
                            if (!timestampElement) {{
                                // 데이터 속성으로 찾기
                                timestampElement = parent.querySelector('[data-time], [data-timestamp], [data-start]');
                            }}
                        }}
                        
                        if (timestampElement) {{
                            timestamp = timestampElement.textContent?.trim() || 
                                       timestampElement.getAttribute('data-time') || 
                                       timestampElement.getAttribute('data-timestamp') || '';
                        }}
                        
                        // 추가 메타데이터 수집
                        const elementData = {{
                            index: index,
                            text: text,
                            timestamp: timestamp,
                            element_class: element.className || '',
                            parent_class: parent?.className || '',
                            char_length: text.length,
                            word_count: text.split(/\\s+/).length
                        }};
                        
                        results.push(elementData);
                    }}
                }});
                
                console.log(`유효한 트랜스크립트 추출: ${{results.length}}개`);
                return results;
            }}
        """
        
        transcript_data = await page.evaluate(extraction_script)
        
        print(f"   📝 DOM에서 {len(transcript_data)}개의 트랜스크립트 추출")
        
        return transcript_data
    
    async def _process_api_responses(self) -> List[Dict[str, Any]]:
        """캡처된 API 응답에서 트랜스크립트 데이터 추출"""
        processed_data = []
        
        for response in self.api_responses:
            try:
                data = response['data']
                
                # JSON 데이터 처리
                if isinstance(data, dict):
                    # 일반적인 트랜스크립트 API 구조 처리
                    if 'cues' in data:
                        for i, cue in enumerate(data['cues']):
                            processed_data.append({
                                'index': i,
                                'text': cue.get('text', '').strip(),
                                'timestamp': cue.get('start', '') or cue.get('time', ''),
                                'source': 'api_cues'
                            })
                    elif 'items' in data:
                        for i, item in enumerate(data['items']):
                            processed_data.append({
                                'index': i,
                                'text': item.get('text', '').strip(),
                                'timestamp': item.get('timestamp', '') or item.get('time', ''),
                                'source': 'api_items'
                            })
                    elif 'transcript' in data:
                        transcript = data['transcript']
                        if isinstance(transcript, list):
                            for i, item in enumerate(transcript):
                                processed_data.append({
                                    'index': i,
                                    'text': item.get('text', '').strip(),
                                    'timestamp': item.get('timestamp', '') or item.get('time', ''),
                                    'source': 'api_transcript'
                                })
                
                # 텍스트 데이터 처리 (SRT, VTT 등)
                elif isinstance(data, str):
                    if '.srt' in response['url'] or 'WEBVTT' in data:
                        parsed = self._parse_subtitle_format(data)
                        processed_data.extend(parsed)
                        
            except Exception as e:
                print(f"API 응답 처리 중 오류: {e}")
        
        print(f"   🌐 API에서 {len(processed_data)}개의 트랜스크립트 추출")
        return processed_data
    
    def _parse_subtitle_format(self, content: str) -> List[Dict[str, Any]]:
        """SRT, VTT 등 자막 형식 파싱"""
        results = []
        
        # SRT 형식 파싱
        if '-->' in content:
            blocks = re.split(r'\n\s*\n', content.strip())
            for i, block in enumerate(blocks):
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 타임스탬프 라인 찾기
                    timestamp_line = None
                    text_lines = []
                    
                    for line in lines:
                        if '-->' in line:
                            timestamp_line = line
                        elif line.strip() and not line.strip().isdigit():
                            text_lines.append(line.strip())
                    
                    if timestamp_line and text_lines:
                        results.append({
                            'index': i,
                            'text': ' '.join(text_lines),
                            'timestamp': timestamp_line.split('-->')[0].strip(),
                            'source': 'subtitle_file'
                        })
        
        return results
    
    def _merge_transcript_data(self, dom_data: List[Dict], api_data: List[Dict]) -> List[Dict[str, Any]]:
        """DOM과 API에서 추출한 데이터를 병합하고 정제"""
        
        # DOM 데이터를 기본으로 사용
        merged_data = dom_data.copy()
        
        # API 데이터가 더 많거나 더 정확하다면 교체
        if len(api_data) > len(dom_data) * 1.1:  # 10% 이상 많으면
            print("   🔄 API 데이터가 더 풍부하여 API 데이터를 주로 사용합니다.")
            merged_data = api_data
            
            # DOM 데이터의 유용한 정보 병합
            for dom_item in dom_data:
                matching_api_item = None
                for api_item in api_data:
                    if self._is_similar_text(dom_item['text'], api_item['text']):
                        matching_api_item = api_item
                        break
                
                if matching_api_item:
                    # 더 나은 정보가 있으면 업데이트
                    if not matching_api_item.get('timestamp') and dom_item.get('timestamp'):
                        matching_api_item['timestamp'] = dom_item['timestamp']
        
        # 중복 제거 및 정제
        unique_data = []
        seen_texts = set()
        
        for item in merged_data:
            text = item['text'].strip()
            if text and text not in seen_texts and len(text) > 5:  # 너무 짧은 텍스트 제외
                seen_texts.add(text)
                
                # 데이터 정제
                cleaned_item = {
                    'index': len(unique_data),
                    'text': text,
                    'timestamp': self._format_timestamp(item.get('timestamp', '')),
                    'source': item.get('source', 'dom'),
                    'length': len(text),
                    'word_count': len(text.split())
                }
                
                unique_data.append(cleaned_item)
        
        # 인덱스 순서로 정렬 (가능한 경우)
        try:
            unique_data.sort(key=lambda x: x.get('original_index', x['index']))
        except:
            pass
        
        print(f"   🔧 데이터 정제 완료: {len(merged_data)} → {len(unique_data)}개")
        return unique_data
    
    def _is_similar_text(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """두 텍스트의 유사성 판단"""
        if not text1 or not text2:
            return False
        
        # 간단한 유사성 계산 (실제로는 더 정교한 알고리즘 사용 가능)
        text1_clean = re.sub(r'[^\w\s]', '', text1.lower())
        text2_clean = re.sub(r'[^\w\s]', '', text2.lower())
        
        if text1_clean == text2_clean:
            return True
        
        # 부분 문자열 포함 관계 확인
        if len(text1_clean) > len(text2_clean):
            return text2_clean in text1_clean
        else:
            return text1_clean in text2_clean
    
    def _format_timestamp(self, timestamp: str) -> str:
        """타임스탬프 형식 통일"""
        if not timestamp:
            return ""
        
        # 다양한 타임스탬프 형식을 통일된 형식으로 변환
        timestamp = timestamp.strip()
        
        # 이미 올바른 형식이면 그대로 반환
        if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', timestamp):
            return timestamp
        
        # 초 단위 숫자를 시:분:초로 변환
        if timestamp.replace('.', '').isdigit():
            try:
                seconds = float(timestamp)
                minutes = int(seconds // 60)
                seconds = int(seconds % 60)
                return f"{minutes:02d}:{seconds:02d}"
            except:
                pass
        
        return timestamp
    
    async def _save_transcript_data(self, lecture_url: str, transcript_data: List[Dict[str, Any]]):
        """트랜스크립트 데이터를 파일로 저장"""
        
        # 출력 디렉토리 생성
        os.makedirs(self.config.OUTPUT_PATH, exist_ok=True)
        
        # 파일명 생성 (URL에서 강의 ID 추출)
        lecture_id = self._extract_lecture_id(lecture_url)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON 형태로 저장
        json_filename = f"{self.config.OUTPUT_PATH}/transcript_{lecture_id}_{timestamp}.json"
        json_data = {
            'lecture_url': lecture_url,
            'lecture_id': lecture_id,
            'scraped_at': datetime.now().isoformat(),
            'transcript_count': len(transcript_data),
            'total_characters': sum(item['length'] for item in transcript_data),
            'total_words': sum(item['word_count'] for item in transcript_data),
            'sources_used': list(set(item['source'] for item in transcript_data)),
            'transcripts': transcript_data,
            'raw_api_responses': len(self.api_responses),
            'config_used': {
                'headless': self.config.HEADLESS,
                'timeout': self.config.TIMEOUT,
                'scroll_delay': self.config.SCROLL_DELAY
            }
        }
        
        async with aiofiles.open(json_filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(json_data, ensure_ascii=False, indent=2))
        
        # 읽기 쉬운 텍스트 형태로도 저장
        txt_filename = f"{self.config.OUTPUT_PATH}/transcript_{lecture_id}_{timestamp}.txt"
        async with aiofiles.open(txt_filename, 'w', encoding='utf-8') as f:
            await f.write(f"강의 URL: {lecture_url}\n")
            await f.write(f"강의 ID: {lecture_id}\n")
            await f.write(f"스크래핑 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}\n")
            await f.write(f"총 트랜스크립트: {len(transcript_data)}개\n")
            await f.write(f"총 글자 수: {sum(item['length'] for item in transcript_data):,}자\n")
            await f.write(f"총 단어 수: {sum(item['word_count'] for item in transcript_data):,}개\n")
            await f.write("=" * 80 + "\n\n")
            
            for i, item in enumerate(transcript_data, 1):
                timestamp_str = f"[{item['timestamp']}] " if item['timestamp'] else ""
                line = f"{i:3d}. {timestamp_str}{item['text']}\n"
                await f.write(line)
                
                # 긴 텍스트인 경우 줄바꿈 추가
                if item['length'] > 100:
                    await f.write("\n")
        
        print(f"💾 데이터 저장 완료:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📝 TXT: {txt_filename}")
        print(f"   📊 총 {len(transcript_data)}개 트랜스크립트, {sum(item['length'] for item in transcript_data):,}자")
    
    def _extract_lecture_id(self, url: str) -> str:
        """URL에서 강의 ID 추출"""
        # URL에서 숫자 ID 패턴 추출
        match = re.search(r'/(\w+/)?(\d+)/?$', url)
        if match:
            return match.group(2)
        
        # 대체 패턴들
        patterns = [
            r'/lec\w*(\d+)',
            r'/lecture[/_](\d+)',
            r'/course[/_](\d+)',
            r'[/_](\d+)/?$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # ID를 찾을 수 없으면 URL의 마지막 부분 사용
        return url.split('/')[-1] or 'unknown'

