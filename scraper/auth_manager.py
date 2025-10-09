import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright
from .config import Config

class AuthManager:
    """구글 OAuth 로그인 및 세션 관리 클래스"""
    
    def __init__(self):
        self.config = Config()
        self.config.validate()
    
    async def setup_initial_login(self):
        """
        최초 1회 수동 로그인 세션 저장
        구글 OAuth 로그인을 수동으로 완료한 후 세션 상태를 저장합니다.
        """
        print("🔐 코드깎는노인 초기 로그인 설정을 시작합니다...")
        print("브라우저가 열리면 수동으로 구글 계정 로그인을 완료해주세요.")
        print("⚠️  로그인 완료 후 강의 목록이나 대시보드 페이지가 보이면 Enter를 눌러주세요.")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 수동 로그인을 위해 브라우저 표시
                args=[
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-blink-features=AutomationControlled',
                    '--no-first-run',
                    '--disable-default-apps'
                ]
            )
            
            context = await browser.new_context(
                user_agent=self.config.USER_AGENT,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 로그인 페이지로 이동
                print(f"📍 로그인 페이지로 이동: {self.config.LOGIN_URL}")
                await page.goto(self.config.LOGIN_URL, wait_until='domcontentloaded', timeout=self.config.TIMEOUT)
                
                # 페이지 로드 대기
                await page.wait_for_timeout(2000)
                
                print("👆 브라우저에서 구글 계정으로 로그인해주세요...")
                print("   1. '구글로 로그인' 또는 '구글 계정으로 계속하기' 버튼 클릭")
                print("   2. 구글 계정 정보 입력")
                print("   3. 2단계 인증이 있다면 완료")
                print("   4. 로그인이 완료되어 사이트 메인 페이지가 보이면 Enter 키를 눌러주세요!")
                
                # 사용자 입력 대기
                input("   ✋ 로그인 완료 후 Enter를 눌러주세요: ")
                
                # 현재 URL 확인으로 로그인 상태 검증
                current_url = page.url
                print(f"현재 URL: {current_url}")
                
                # 로그인 성공 여부 확인
                is_logged_in = await self._verify_login_status(page)
                
                if not is_logged_in:
                    print("⚠️ 로그인이 완료되지 않았을 수 있습니다.")
                    retry = input("다시 시도하시겠습니까? (y/N): ")
                    if retry.lower() != 'y':
                        return False
                    
                    # 추가 대기 시간 제공
                    print("추가로 30초 더 기다립니다. 로그인을 완료해주세요...")
                    await page.wait_for_timeout(30000)
                    
                    is_logged_in = await self._verify_login_status(page)
                    if not is_logged_in:
                        print("❌ 로그인 확인에 실패했습니다.")
                        return False
                
                # 세션 상태 저장
                storage_dir = os.path.dirname(self.config.STORAGE_STATE_PATH)
                os.makedirs(storage_dir, exist_ok=True)
                
                await context.storage_state(path=self.config.STORAGE_STATE_PATH)
                
                # 저장된 세션 정보 확인
                with open(self.config.STORAGE_STATE_PATH, 'r', encoding='utf-8') as f:
                    storage_data = json.load(f)
                    cookie_count = len(storage_data.get('cookies', []))
                    local_storage_count = len(storage_data.get('origins', []))
                
                print(f"✅ 로그인 세션이 저장되었습니다!")
                print(f"   📁 저장 위치: {self.config.STORAGE_STATE_PATH}")
                print(f"   🍪 쿠키 개수: {cookie_count}개")
                print(f"   💾 로컬 스토리지 항목: {local_storage_count}개")
                print(f"   ⏰ 저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                return True
                
            except Exception as e:
                print(f"❌ 로그인 설정 중 오류 발생: {e}")
                return False
            finally:
                await browser.close()
    
    async def _verify_login_status(self, page):
        """로그인 상태 확인"""
        try:
            # 로그인 상태를 확인할 수 있는 여러 방법 시도
            
            # 1. URL 패턴으로 확인
            current_url = page.url
            if any(pattern in current_url for pattern in ['login', 'signin', 'auth']):
                return False
            
            # 2. 페이지 내용으로 확인
            login_indicators = await page.evaluate("""
                () => {
                    // 로그인 관련 텍스트나 버튼이 있는지 확인
                    const loginTexts = ['로그인', '구글로', 'Sign in', 'Login'];
                    const bodyText = document.body.innerText;
                    
                    for (const text of loginTexts) {
                        if (bodyText.includes(text)) {
                            return false;
                        }
                    }
                    
                    // 로그인 후에만 나타나는 요소들 확인
                    const loggedInIndicators = [
                        'a[href*="logout"]',
                        'a[href*="profile"]',
                        'a[href*="mypage"]',
                        '[class*="user"]',
                        '[class*="member"]'
                    ];
                    
                    for (const selector of loggedInIndicators) {
                        if (document.querySelector(selector)) {
                            return true;
                        }
                    }
                    
                    return bodyText.length > 1000; // 충분한 콘텐츠가 있으면 로그인 상태로 가정
                }
            """)
            
            return login_indicators
            
        except Exception as e:
            print(f"로그인 상태 확인 중 오류: {e}")
            return True  # 오류 시 로그인된 것으로 가정
    
    async def create_authenticated_context(self, playwright_instance):
        """
        저장된 세션으로 인증된 브라우저 컨텍스트 생성
        """
        if not os.path.exists(self.config.STORAGE_STATE_PATH):
            raise FileNotFoundError(
                f"저장된 세션 파일이 없습니다: {self.config.STORAGE_STATE_PATH}\n"
                "먼저 'python main.py --setup-auth' 명령으로 로그인 설정을 완료해주세요."
            )
        
        # 저장된 세션 파일의 유효성 확인
        try:
            with open(self.config.STORAGE_STATE_PATH, 'r', encoding='utf-8') as f:
                storage_data = json.load(f)
                if not storage_data.get('cookies'):
                    raise ValueError("저장된 세션에 쿠키 정보가 없습니다.")
        except json.JSONDecodeError:
            raise ValueError("저장된 세션 파일이 손상되었습니다.")
        
        browser = await playwright_instance.chromium.launch(
            headless=self.config.HEADLESS,
            args=[
                '--disable-web-security',
                '--disable-blink-features=AutomationControlled',
                '--no-first-run',
                '--disable-default-apps'
            ]
        )
        
        context = await browser.new_context(
            storage_state=self.config.STORAGE_STATE_PATH,
            user_agent=self.config.USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        
        return browser, context
    
    async def verify_session_validity(self):
        """저장된 세션의 유효성 검증"""
        print("🔍 저장된 세션의 유효성을 확인합니다...")
        
        async with async_playwright() as p:
            try:
                browser, context = await self.create_authenticated_context(p)
                page = await context.new_page()
                
                # 테스트 페이지로 이동
                await page.goto(self.config.BASE_URL, timeout=self.config.TIMEOUT)
                await page.wait_for_timeout(2000)
                
                # 로그인 상태 확인
                is_valid = await self._verify_login_status(page)
                
                await browser.close()
                
                if is_valid:
                    print("✅ 저장된 세션이 유효합니다.")
                else:
                    print("❌ 저장된 세션이 만료되었거나 유효하지 않습니다.")
                    print("   'python main.py --setup-auth' 명령으로 다시 로그인해주세요.")
                
                return is_valid
                
            except Exception as e:
                print(f"❌ 세션 확인 중 오류 발생: {e}")
                return False
