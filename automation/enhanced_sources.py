"""다양한 데이터 소스에서 QA 관련 콘텐츠를 수집하는 향상된 모듈."""

import json
import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp

from automation.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EnhancedContent:
    """향상된 콘텐츠 데이터 구조."""
    
    source: str  # reddit, hackernews, devto, medium, linkedin, twitter
    title: str
    url: str
    content: str
    author: str
    engagement: Dict[str, int]  # likes, comments, shares
    tags: List[str]
    published_at: datetime
    metadata: Dict[str, Any]


class RedditCollector:
    """Reddit에서 QA/Testing 관련 포스트 수집."""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "QA-Blog-Automation/1.0")
        self.subreddits = [
            "softwaretesting",
            "QualityAssurance", 
            "testautomation",
            "selenium",
            "playwright",
            "softwareengineering",
            "programming"
        ]
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """Reddit OAuth2 액세스 토큰 획득."""
        if self._access_token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return self._access_token
        
        auth_url = "https://www.reddit.com/api/v1/access_token"
        auth_data = {
            "grant_type": "client_credentials"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                auth_url,
                data=auth_data,
                auth=aiohttp.BasicAuth(self.client_id, self.client_secret),
                headers={"User-Agent": self.user_agent}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Reddit 인증 실패: {response.status} - {error_text}")
                
                data = await response.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
                return self._access_token
    
    async def collect(self, limit: int = 50) -> List[EnhancedContent]:
        """Reddit에서 인기 QA 포스트 수집."""
        try:
            access_token = await self._get_access_token()
            all_posts = []
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"bearer {access_token}",
                    "User-Agent": self.user_agent
                }
                
                # 각 subreddit에서 hot/top 포스트 수집
                for subreddit in self.subreddits:
                    try:
                        # hot 포스트 수집
                        url = f"https://oauth.reddit.com/r/{subreddit}/hot.json?limit=25"
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                posts = data.get("data", {}).get("children", [])
                                all_posts.extend(posts)
                        
                        # top 포스트 수집
                        url = f"https://oauth.reddit.com/r/{subreddit}/top.json?limit=25&t=week"
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json()
                                posts = data.get("data", {}).get("children", [])
                                all_posts.extend(posts)
                        
                        await asyncio.sleep(0.5)  # Rate limit 방지
                    except Exception as exc:
                        logger.warning(f"Subreddit {subreddit} 수집 실패: {exc}")
                        continue
            
            # 중복 제거 (같은 post ID)
            seen_ids = set()
            unique_posts = []
            for post in all_posts:
                post_id = post.get("data", {}).get("id")
                if post_id and post_id not in seen_ids:
                    seen_ids.add(post_id)
                    unique_posts.append(post)
            
            # EnhancedContent로 변환
            contents = []
            for post in unique_posts[:limit]:
                try:
                    post_data = post.get("data", {})
                    content = self._parse_reddit_post(post_data)
                    if content:
                        contents.append(content)
                except Exception as exc:
                    logger.warning(f"Reddit 포스트 파싱 실패: {exc}")
                    continue
            
            logger.info(f"Reddit에서 {len(contents)}개 포스트 수집 완료")
            return contents
            
        except Exception as exc:
            logger.error(f"Reddit 수집 중 오류: {exc}", exc_info=True)
            return []
    
    def _parse_reddit_post(self, post_data: Dict[str, Any]) -> Optional[EnhancedContent]:
        """Reddit 포스트 데이터를 EnhancedContent로 변환."""
        try:
            title = post_data.get("title", "")
            if not title:
                return None
            
            # selftext 또는 url에서 콘텐츠 추출
            content = post_data.get("selftext", "")
            url = post_data.get("url", "")
            
            # URL만 있고 selftext가 없으면 URL을 사용
            if not content and url:
                content = f"링크: {url}"
            
            # 작성 시간 파싱
            created_utc = post_data.get("created_utc", 0)
            if created_utc:
                published_at = datetime.fromtimestamp(created_utc, tz=datetime.now().astimezone().tzinfo)
            else:
                published_at = datetime.now()
            
            # Engagement 메트릭
            engagement = {
                "likes": post_data.get("ups", 0),
                "comments": post_data.get("num_comments", 0),
                "shares": 0  # Reddit에는 shares가 없음
            }
            
            # 태그 (subreddit 이름 사용)
            tags = [post_data.get("subreddit", "")]
            
            # 메타데이터
            metadata = {
                "subreddit": post_data.get("subreddit", ""),
                "score": post_data.get("score", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "permalink": f"https://reddit.com{post_data.get('permalink', '')}"
            }
            
            return EnhancedContent(
                source="reddit",
                title=title,
                url=url or metadata.get("permalink", ""),
                content=content[:2000],  # 최대 2000자
                author=post_data.get("author", "unknown"),
                engagement=engagement,
                tags=tags,
                published_at=published_at,
                metadata=metadata
            )
        except Exception as exc:
            logger.warning(f"Reddit 포스트 파싱 중 오류: {exc}")
            return None


class DevToCollector:
    """Dev.to에서 QA 관련 아티클 수집."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://dev.to/api"
        
    async def collect(self, tags: List[str] = None) -> List[EnhancedContent]:
        """Dev.to에서 QA/Testing 태그 아티클 수집."""
        if not tags:
            tags = ["testing", "qa", "automation", "testautomation", "e2e"]
        
        try:
            async with aiohttp.ClientSession() as session:
                articles = []
                for tag in tags:
                    try:
                        url = f"{self.base_url}/articles?tag={tag}&top=7"
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                data = await response.json()
                                articles.extend(data)
                            else:
                                logger.warning(f"Dev.to API 호출 실패 (태그: {tag}, 상태: {response.status})")
                        await asyncio.sleep(0.3)  # Rate limit 방지
                    except Exception as exc:
                        logger.warning(f"Dev.to 태그 {tag} 수집 실패: {exc}")
                        continue
                
                return self._parse_articles(articles)
        except Exception as exc:
            logger.error(f"Dev.to 수집 중 오류: {exc}", exc_info=True)
            return []
    
    def _parse_articles(self, articles: List[Dict[str, Any]]) -> List[EnhancedContent]:
        """Dev.to 아티클 리스트를 EnhancedContent로 변환."""
        contents = []
        
        for article in articles:
            try:
                content = self._parse_article(article)
                if content:
                    contents.append(content)
            except Exception as exc:
                logger.warning(f"Dev.to 아티클 파싱 실패: {exc}")
                continue
        
        logger.info(f"Dev.to에서 {len(contents)}개 아티클 수집 완료")
        return contents
    
    def _parse_article(self, article: Dict[str, Any]) -> Optional[EnhancedContent]:
        """Dev.to 아티클을 EnhancedContent로 변환."""
        try:
            title = article.get("title", "")
            if not title:
                return None
            
            # 작성 시간 파싱
            published_str = article.get("published_at")
            if published_str:
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except:
                    published_at = datetime.now()
            else:
                published_at = datetime.now()
            
            # Engagement 메트릭
            engagement = {
                "likes": article.get("positive_reactions_count", 0),
                "comments": article.get("comments_count", 0),
                "shares": 0
            }
            
            # 태그
            tags = article.get("tag_list", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",")]
            
            # 메타데이터
            metadata = {
                "article_id": article.get("id"),
                "reading_time": article.get("reading_time_minutes", 0),
                "user": article.get("user", {}).get("username", ""),
                "organization": article.get("organization", {}).get("name", "") if article.get("organization") else ""
            }
            
            return EnhancedContent(
                source="devto",
                title=title,
                url=article.get("url", ""),
                content=article.get("description", "")[:2000],  # 최대 2000자
                author=metadata.get("user", "unknown"),
                engagement=engagement,
                tags=tags,
                published_at=published_at,
                metadata=metadata
            )
        except Exception as exc:
            logger.warning(f"Dev.to 아티클 파싱 중 오류: {exc}")
            return None


class MediumCollector:
    """Medium에서 QA 관련 고품질 아티클 수집."""
    
    def __init__(self):
        self.publications = [
            "airbnb-engineering",
            "netflix-techblog",
            "uber-engineering",
            "googledevelopers"
        ]
        self.tags = ["software-testing", "test-automation", "quality-assurance"]
    
    async def collect(self) -> List[EnhancedContent]:
        """Medium의 주요 기술 블로그에서 QA 콘텐츠 수집."""
        # Medium RSS 또는 웹 스크래핑으로 수집
        # 대기업 엔지니어링 팀의 실제 사례 중심
        pass


class LinkedInCollector:
    """LinkedIn에서 QA 전문가들의 인사이트 수집."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.qa_influencers = [
            # QA 분야 인플루언서 리스트
        ]
    
    async def collect_posts(self) -> List[EnhancedContent]:
        """LinkedIn 포스트에서 QA 인사이트 수집."""
        # LinkedIn API로 QA 전문가들의 포스트 수집
        # 업계 트렌드, 채용 동향, 스킬 요구사항 파악
        pass


class TwitterCollector:
    """Twitter/X에서 실시간 QA 트렌드 수집."""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.qa_hashtags = [
            "#TestAutomation",
            "#QualityAssurance",
            "#SoftwareTesting",
            "#TestingCommunity",
            "#QAEngineers"
        ]
    
    async def collect_trending(self) -> List[EnhancedContent]:
        """Twitter에서 QA 관련 트렌딩 토픽 수집."""
        # Twitter API v2로 실시간 트렌드 수집
        # 최신 도구 릴리스, 컨퍼런스 소식 등
        pass


class StackOverflowCollector:
    """Stack Overflow에서 실제 QA 문제와 해결책 수집."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_url = "https://api.stackexchange.com/2.3"
        self.qa_tags = ["selenium", "cypress", "playwright", "pytest", "testng"]
        self.api_key = api_key or os.getenv("STACKOVERFLOW_API_KEY")
    
    async def collect_top_questions(self, days: int = 7) -> List[EnhancedContent]:
        """최근 인기 QA 관련 질문과 답변 수집."""
        try:
            all_questions = []
            from_date = int((datetime.now() - timedelta(days=days)).timestamp())
            
            async with aiohttp.ClientSession() as session:
                for tag in self.qa_tags:
                    try:
                        params = {
                            "order": "desc",
                            "sort": "votes",
                            "tagged": tag,
                            "site": "stackoverflow",
                            "pagesize": 20,
                            "fromdate": from_date,
                            "filter": "withbody"
                        }
                        
                        if self.api_key:
                            params["key"] = self.api_key
                        
                        url = f"{self.api_url}/questions"
                        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                data = await response.json()
                                questions = data.get("items", [])
                                all_questions.extend(questions)
                            else:
                                error_text = await response.text()
                                logger.warning(f"Stack Overflow API 호출 실패 (태그: {tag}, 상태: {response.status}): {error_text}")
                        
                        await asyncio.sleep(0.3)  # Rate limit 방지
                    except Exception as exc:
                        logger.warning(f"Stack Overflow 태그 {tag} 수집 실패: {exc}")
                        continue
            
            # 중복 제거 (같은 question_id)
            seen_ids = set()
            unique_questions = []
            for question in all_questions:
                q_id = question.get("question_id")
                if q_id and q_id not in seen_ids:
                    seen_ids.add(q_id)
                    unique_questions.append(question)
            
            # EnhancedContent로 변환
            contents = []
            for question in unique_questions:
                try:
                    content = self._parse_question(question)
                    if content:
                        contents.append(content)
                except Exception as exc:
                    logger.warning(f"Stack Overflow 질문 파싱 실패: {exc}")
                    continue
            
            logger.info(f"Stack Overflow에서 {len(contents)}개 질문 수집 완료")
            return contents
            
        except Exception as exc:
            logger.error(f"Stack Overflow 수집 중 오류: {exc}", exc_info=True)
            return []
    
    def _parse_question(self, question: Dict[str, Any]) -> Optional[EnhancedContent]:
        """Stack Overflow 질문을 EnhancedContent로 변환."""
        try:
            title = question.get("title", "")
            if not title:
                return None
            
            # 작성 시간 파싱
            creation_date = question.get("creation_date", 0)
            if creation_date:
                published_at = datetime.fromtimestamp(creation_date, tz=datetime.now().astimezone().tzinfo)
            else:
                published_at = datetime.now()
            
            # Engagement 메트릭
            engagement = {
                "likes": question.get("score", 0),
                "comments": question.get("comment_count", 0),
                "shares": 0
            }
            
            # 태그
            tags = question.get("tags", [])
            
            # 메타데이터
            metadata = {
                "question_id": question.get("question_id"),
                "view_count": question.get("view_count", 0),
                "answer_count": question.get("answer_count", 0),
                "is_answered": question.get("is_answered", False),
                "owner": question.get("owner", {}).get("display_name", "unknown")
            }
            
            # 본문 (body)에서 HTML 태그 제거
            body = question.get("body", "")
            if body:
                # 간단한 HTML 태그 제거
                body = re.sub(r'<[^>]+>', '', body)
                body = body[:2000]  # 최대 2000자
            else:
                body = f"질문: {title}"
            
            return EnhancedContent(
                source="stackoverflow",
                title=title,
                url=question.get("link", ""),
                content=body,
                author=metadata.get("owner", "unknown"),
                engagement=engagement,
                tags=tags,
                published_at=published_at,
                metadata=metadata
            )
        except Exception as exc:
            logger.warning(f"Stack Overflow 질문 파싱 중 오류: {exc}")
            return None


class AIEnhancedAnalyzer:
    """여러 AI를 활용한 콘텐츠 분석 및 강화."""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.claude_key = os.getenv("CLAUDE_API_KEY")
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Provider 인스턴스 생성
        self.providers = {}
        if self.openai_key:
            from automation.qa_generator import OpenAIProvider
            self.providers["openai"] = OpenAIProvider(
                api_key=self.openai_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            )
        if self.claude_key:
            from automation.qa_generator import ClaudeProvider
            self.providers["claude"] = ClaudeProvider(
                api_key=self.claude_key,
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            )
        if self.perplexity_key:
            from automation.qa_generator import PerplexityProvider
            self.providers["perplexity"] = PerplexityProvider(
                api_key=self.perplexity_key,
                model=os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
            )
        if self.gemini_key:
            from automation.qa_generator import GeminiProvider
            self.providers["gemini"] = GeminiProvider(
                api_key=self.gemini_key,
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
            )
    
    async def analyze_with_multiple_ai(
        self, 
        content: EnhancedContent
    ) -> Dict[str, Any]:
        """여러 AI로 콘텐츠를 분석하여 다각도 인사이트 생성."""
        
        # EnhancedContent를 FeedItem 형식으로 변환
        item = {
            "title": content.title,
            "summary": content.content,
            "link": content.url,
            "published_at": content.published_at.isoformat() if isinstance(content.published_at, datetime) else ""
        }
        
        tasks = []
        provider_names = []
        
        # 각 Provider로 분석 실행
        if "openai" in self.providers:
            tasks.append(self._analyze_with_provider("openai", item))
            provider_names.append("openai")
        
        if "claude" in self.providers:
            tasks.append(self._analyze_with_provider("claude", item))
            provider_names.append("claude")
        
        if "perplexity" in self.providers:
            tasks.append(self._analyze_with_provider("perplexity", item))
            provider_names.append("perplexity")
        
        if "gemini" in self.providers:
            tasks.append(self._analyze_with_provider("gemini", item))
            provider_names.append("gemini")
        
        if not tasks:
            logger.warning("사용 가능한 AI Provider가 없습니다.")
            return self._create_empty_insights()
        
        # 병렬로 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과를 딕셔너리로 변환
        results_dict = {}
        for name, result in zip(provider_names, results):
            if isinstance(result, Exception):
                logger.error(f"{name} 분석 중 오류: {result}", exc_info=True)
                results_dict[name] = None
            else:
                results_dict[name] = result
        
        return self._merge_insights(results_dict)
    
    async def _analyze_with_provider(self, provider_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """특정 Provider로 분석 실행."""
        try:
            provider = self.providers[provider_name]
            
            # 동기 함수를 비동기로 실행
            loop = asyncio.get_event_loop()
            qa_result = await loop.run_in_executor(None, provider.generate, item)
            
            # QAResult를 딕셔너리로 변환
            return {
                "provider": provider_name,
                "summary": qa_result.summary,
                "qa_engineer_insights": qa_result.qa_engineer_insights,
                "practical_guide": qa_result.practical_guide,
                "learning_roadmap": qa_result.learning_roadmap,
                "expert_opinions": qa_result.expert_opinions,
                "qa_pairs": qa_result.qa_pairs,
                "technical_level": qa_result.technical_level,
                "blog_category": qa_result.blog_category
            }
        except Exception as exc:
            logger.error(f"{provider_name} 분석 실패: {exc}", exc_info=True)
            raise
    
    def _merge_insights(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """여러 AI의 분석 결과를 통합."""
        merged = {
            "practical_guide": [],
            "technical_analysis": [],
            "latest_trends": [],
            "visual_insights": [],
            "expert_consensus": [],
            "qa_engineer_insights": [],
            "learning_roadmap": [],
            "expert_opinions": [],
            "qa_pairs": [],
            "summary": "",
            "technical_level": "advanced",
            "blog_category": "Learning"
        }
        
        # 각 AI의 강점을 살려 통합
        summaries = []
        all_insights = []
        all_guides = []
        all_roadmaps = []
        all_opinions = []
        all_qa_pairs = []
        
        # OpenAI: 실무 가이드 중심
        if results.get("openai"):
            openai_result = results["openai"]
            if openai_result.get("summary"):
                summaries.append(f"[OpenAI 실무 관점] {openai_result['summary']}")
            if openai_result.get("practical_guide"):
                all_guides.extend(openai_result["practical_guide"])
            if openai_result.get("qa_engineer_insights"):
                all_insights.extend(openai_result["qa_engineer_insights"])
        
        # Claude: 기술 분석 중심
        if results.get("claude"):
            claude_result = results["claude"]
            if claude_result.get("summary"):
                summaries.append(f"[Claude 기술 분석] {claude_result['summary']}")
            if claude_result.get("expert_opinions"):
                all_opinions.extend(claude_result["expert_opinions"])
            technical_analysis = {
                "provider": "claude",
                "insights": claude_result.get("qa_engineer_insights", []),
                "technical_level": claude_result.get("technical_level", "advanced")
            }
            merged["technical_analysis"].append(technical_analysis)
        
        # Perplexity: 최신 트렌드 중심
        if results.get("perplexity"):
            perplexity_result = results["perplexity"]
            if perplexity_result.get("summary"):
                summaries.append(f"[Perplexity 최신 정보] {perplexity_result['summary']}")
            latest_trends = {
                "provider": "perplexity",
                "insights": perplexity_result.get("qa_engineer_insights", []),
                "resources": perplexity_result.get("qa_pairs", [])
            }
            merged["latest_trends"].append(latest_trends)
        
        # Gemini: 멀티모달 인사이트
        if results.get("gemini"):
            gemini_result = results["gemini"]
            if gemini_result.get("summary"):
                summaries.append(f"[Gemini 멀티모달] {gemini_result['summary']}")
            visual_insights = {
                "provider": "gemini",
                "insights": gemini_result.get("qa_engineer_insights", []),
                "practical_guide": gemini_result.get("practical_guide", [])
            }
            merged["visual_insights"].append(visual_insights)
        
        # 통합
        merged["summary"] = " ".join(summaries) if summaries else ""
        merged["qa_engineer_insights"] = list(dict.fromkeys(all_insights))[:5]  # 중복 제거, 최대 5개
        merged["practical_guide"] = all_guides[:3]  # 최대 3개
        merged["learning_roadmap"] = all_roadmaps[:3] if all_roadmaps else []
        merged["expert_opinions"] = all_opinions[:3]  # 최대 3개
        merged["qa_pairs"] = all_qa_pairs[:5]  # 최대 5개
        
        # 기술 수준 및 카테고리 결정 (대부분의 Provider가 동의한 값 사용)
        technical_levels = [r.get("technical_level", "advanced") for r in results.values() if r]
        if technical_levels:
            merged["technical_level"] = max(set(technical_levels), key=technical_levels.count)
        
        categories = [r.get("blog_category", "Learning") for r in results.values() if r]
        if categories:
            merged["blog_category"] = max(set(categories), key=categories.count)
        
        # 전문가 합의 (모든 Provider의 공통 인사이트)
        if len(results) > 1:
            common_insights = self._find_common_insights(results)
            merged["expert_consensus"] = common_insights
        
        return merged
    
    def _find_common_insights(self, results: Dict[str, Dict[str, Any]]) -> List[str]:
        """여러 Provider의 공통 인사이트 찾기."""
        all_insights = []
        for result in results.values():
            if result and result.get("qa_engineer_insights"):
                all_insights.extend(result["qa_engineer_insights"])
        
        # 간단한 키워드 기반 중복 찾기 (실제로는 더 정교한 방법 필요)
        from collections import Counter
        insight_keywords = []
        for insight in all_insights:
            # 첫 50자만 사용하여 유사성 판단
            insight_keywords.append(insight[:50].lower())
        
        keyword_counts = Counter(insight_keywords)
        common = [kw for kw, count in keyword_counts.items() if count >= 2]
        
        return common[:3]  # 최대 3개
    
    def _create_empty_insights(self) -> Dict[str, Any]:
        """빈 인사이트 딕셔너리 생성."""
        return {
            "practical_guide": [],
            "technical_analysis": [],
            "latest_trends": [],
            "visual_insights": [],
            "expert_consensus": [],
            "qa_engineer_insights": [],
            "learning_roadmap": [],
            "expert_opinions": [],
            "qa_pairs": [],
            "summary": "",
            "technical_level": "advanced",
            "blog_category": "Learning"
        }


class ContentAggregator:
    """모든 소스에서 수집한 콘텐츠를 통합 관리."""
    
    def __init__(self):
        self.collectors = {
            "reddit": RedditCollector,
            "devto": DevToCollector,
            "medium": MediumCollector,
            "linkedin": LinkedInCollector,
            "twitter": TwitterCollector,
            "stackoverflow": StackOverflowCollector
        }
        self.analyzer = AIEnhancedAnalyzer()
    
    async def aggregate_all_sources(self) -> List[EnhancedContent]:
        """모든 소스에서 콘텐츠 수집 및 통합."""
        all_contents = []
        
        # 병렬로 모든 소스에서 수집
        tasks = []
        for name, collector_class in self.collectors.items():
            if self._is_collector_configured(name):
                collector = self._initialize_collector(name, collector_class)
                if collector:
                    tasks.append(self._collect_with_error_handling(name, collector))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"콘텐츠 수집 중 예외 발생: {result}", exc_info=True)
            elif result:
                all_contents.extend(result)
        
        # 중복 제거 및 품질 필터링
        return self._filter_quality_content(all_contents)
    
    def _is_collector_configured(self, name: str) -> bool:
        """수집기가 설정되어 있는지 확인."""
        if name == "reddit":
            return bool(os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))
        elif name == "devto":
            # Dev.to는 API 키가 없어도 사용 가능
            return True
        elif name == "medium":
            # Medium은 RSS 피드 사용 가능
            return True
        elif name == "linkedin":
            return bool(os.getenv("LINKEDIN_ACCESS_TOKEN"))
        elif name == "twitter":
            return bool(os.getenv("TWITTER_BEARER_TOKEN"))
        elif name == "stackoverflow":
            # Stack Overflow는 API 키 없이도 사용 가능 (제한적)
            return True
        return False
    
    def _initialize_collector(self, name: str, collector_class: type) -> Optional[Any]:
        """수집기 인스턴스 생성."""
        try:
            if name == "reddit":
                client_id = os.getenv("REDDIT_CLIENT_ID")
                client_secret = os.getenv("REDDIT_CLIENT_SECRET")
                user_agent = os.getenv("REDDIT_USER_AGENT")
                if client_id and client_secret:
                    return collector_class(client_id, client_secret, user_agent)
            elif name == "devto":
                api_key = os.getenv("DEVTO_API_KEY")
                return collector_class(api_key)
            elif name == "medium":
                return collector_class()
            elif name == "linkedin":
                access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
                if access_token:
                    return collector_class(access_token)
            elif name == "twitter":
                bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
                if bearer_token:
                    return collector_class(bearer_token)
            elif name == "stackoverflow":
                api_key = os.getenv("STACKOVERFLOW_API_KEY")
                return collector_class(api_key)
        except Exception as exc:
            logger.error(f"{name} 수집기 초기화 실패: {exc}", exc_info=True)
        return None
    
    async def _collect_with_error_handling(self, name: str, collector: Any) -> List[EnhancedContent]:
        """에러 핸들링과 함께 콘텐츠 수집."""
        try:
            if name == "reddit":
                return await collector.collect(limit=50)
            elif name == "devto":
                return await collector.collect()
            elif name == "medium":
                return await collector.collect()
            elif name == "linkedin":
                return await collector.collect_posts()
            elif name == "twitter":
                return await collector.collect_trending()
            elif name == "stackoverflow":
                return await collector.collect_top_questions(days=7)
            else:
                logger.warning(f"알 수 없는 수집기: {name}")
                return []
        except Exception as exc:
            logger.error(f"{name} 수집 중 오류: {exc}", exc_info=True)
            return []
    
    def _filter_quality_content(
        self, 
        contents: List[EnhancedContent]
    ) -> List[EnhancedContent]:
        """고품질 콘텐츠만 필터링."""
        filtered = []
        
        for content in contents:
            # 품질 점수 계산
            quality_score = self._calculate_quality_score(content)
            
            if quality_score >= 70:  # 70점 이상만
                content.metadata["quality_score"] = quality_score
                filtered.append(content)
        
        # 품질 점수로 정렬
        filtered.sort(
            key=lambda x: x.metadata.get("quality_score", 0), 
            reverse=True
        )
        
        return filtered[:50]  # 상위 50개만
    
    def _calculate_quality_score(self, content: EnhancedContent) -> float:
        """콘텐츠 품질 점수 계산."""
        score = 0.0
        
        # 1. 참여도 (30점)
        engagement = content.engagement
        if engagement.get("likes", 0) > 100:
            score += 20
        elif engagement.get("likes", 0) > 50:
            score += 10
        
        if engagement.get("comments", 0) > 20:
            score += 10
        elif engagement.get("comments", 0) > 10:
            score += 5
        
        # 2. 콘텐츠 길이와 깊이 (20점)
        word_count = len(content.content.split())
        if word_count > 1000:
            score += 20
        elif word_count > 500:
            score += 10
        
        # 3. 최신성 (20점)
        # 타임존 문제 해결
        now = datetime.now(content.published_at.tzinfo) if content.published_at.tzinfo else datetime.now()
        published = content.published_at if content.published_at.tzinfo else content.published_at.replace(tzinfo=None)
        if published.tzinfo and not now.tzinfo:
            now = now.replace(tzinfo=published.tzinfo)
        elif not published.tzinfo and now.tzinfo:
            published = published.replace(tzinfo=now.tzinfo)
        days_old = (now - published).days
        if days_old <= 7:
            score += 20
        elif days_old <= 30:
            score += 10
        
        # 4. QA 관련성 (30점)
        qa_keywords = ["test", "qa", "quality", "automation", "selenium", "cypress", "playwright"]
        keyword_count = sum(1 for kw in qa_keywords if kw in content.title.lower() or kw in content.content.lower())
        score += min(30, keyword_count * 5)
        
        return score
