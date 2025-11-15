"""소셜 미디어 자동 게시 및 배포 시스템."""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import re

from automation.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SocialMediaPost:
    """소셜 미디어 포스트 데이터 구조."""
    
    platform: str  # instagram, linkedin, twitter, facebook
    title: str
    content: str
    hashtags: List[str]
    media_urls: List[str]
    link: str
    scheduled_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class InstagramPublisher:
    """Instagram 자동 게시 관리."""
    
    def __init__(self, access_token: str, business_account_id: str):
        self.access_token = access_token
        self.business_account_id = business_account_id
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    async def create_carousel_post(
        self, 
        blog_post: Dict[str, Any],
        images: List[str]
    ) -> Dict[str, Any]:
        """블로그 포스트를 Instagram 캐러셀로 변환."""
        
        # 1. 이미지 생성 (Canva API 또는 Pillow 사용)
        carousel_images = await self._generate_carousel_images(blog_post)
        
        # 2. 캡션 생성
        caption = self._create_instagram_caption(blog_post)
        
        # 3. 미디어 컨테이너 생성
        media_containers = []
        for image_url in carousel_images:
            container = await self._create_media_container(image_url)
            media_containers.append(container["id"])
        
        # 4. 캐러셀 포스트 생성
        carousel_data = {
            "media_type": "CAROUSEL",
            "children": media_containers,
            "caption": caption
        }
        
        # 5. 포스트 게시
        response = await self._publish_media(carousel_data)
        
        logger.info(f"Instagram 캐러셀 게시 완료: {response.get('id')}")
        return response
    
    def _create_instagram_caption(self, blog_post: Dict[str, Any]) -> str:
        """Instagram용 캡션 생성."""
        
        # QA 인사이트 요약 (3줄)
        insights = blog_post.get("qa_engineer_insights", [])[:3]
        
        caption_parts = [
            f"🔍 {blog_post.get('title', '')}",
            "",
            "✨ 핵심 인사이트:",
        ]
        
        for i, insight in enumerate(insights, 1):
            # 인사이트를 150자로 요약
            summary = self._summarize_text(insight, max_length=150)
            caption_parts.append(f"{i}️⃣ {summary}")
        
        # 해시태그 추가
        hashtags = self._generate_hashtags(blog_post)
        caption_parts.extend([
            "",
            "📖 전체 내용은 프로필 링크에서 확인하세요!",
            "",
            " ".join(hashtags)
        ])
        
        return "\n".join(caption_parts)
    
    def _generate_hashtags(self, blog_post: Dict[str, Any]) -> List[str]:
        """관련 해시태그 생성."""
        
        base_hashtags = [
            "#QAEngineer", "#소프트웨어테스팅", "#테스트자동화",
            "#QualityAssurance", "#개발자", "#테크블로그"
        ]
        
        # 카테고리별 해시태그
        category = blog_post.get("blog_category", "")
        if category == "QA Engineer":
            base_hashtags.extend(["#QA전문가", "#테스팅전략"])
        elif category == "Learning":
            base_hashtags.extend(["#기술학습", "#개발공부"])
        
        # AI 관련 해시태그
        if "AI" in blog_post.get("tags", []):
            base_hashtags.extend(["#AI테스팅", "#머신러닝QA"])
        
        return base_hashtags[:30]  # Instagram 제한
    
    async def _generate_carousel_images(
        self, 
        blog_post: Dict[str, Any]
    ) -> List[str]:
        """블로그 내용을 캐러셀 이미지로 변환."""
        
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        images = []
        
        # 1. 타이틀 이미지
        title_image = self._create_title_slide(
            blog_post.get("title", ""),
            blog_post.get("summary", "")
        )
        images.append(title_image)
        
        # 2. 핵심 인사이트 이미지들 (최대 3개)
        insights = blog_post.get("qa_engineer_insights", [])[:3]
        for i, insight in enumerate(insights, 1):
            insight_image = self._create_insight_slide(
                f"인사이트 {i}",
                insight
            )
            images.append(insight_image)
        
        # 3. 실무 가이드 이미지
        if blog_post.get("practical_guide"):
            guide = blog_post["practical_guide"][0]
            guide_image = self._create_guide_slide(
                guide.get("title", ""),
                guide.get("steps", [])
            )
            images.append(guide_image)
        
        # 4. CTA 이미지
        cta_image = self._create_cta_slide(blog_post.get("link", ""))
        images.append(cta_image)
        
        # 이미지를 임시 저장하고 URL 반환
        image_urls = []
        for i, img in enumerate(images):
            path = f"temp/instagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.png"
            img.save(path)
            # 실제로는 이미지를 S3 등에 업로드하고 URL 반환
            image_urls.append(path)
        
        return image_urls
    
    def _create_title_slide(self, title: str, summary: str) -> Image:
        """타이틀 슬라이드 생성."""
        # 1080x1080 Instagram 정사각형
        img = Image.new('RGB', (1080, 1080), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 (실제로는 한글 폰트 필요)
        try:
            title_font = ImageFont.truetype("NanumGothicBold.ttf", 60)
            body_font = ImageFont.truetype("NanumGothic.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # 타이틀 그리기
        wrapped_title = textwrap.fill(title, width=20)
        draw.multiline_text(
            (540, 300), 
            wrapped_title, 
            fill='white', 
            font=title_font, 
            anchor='mm',
            align='center'
        )
        
        # 요약 그리기
        wrapped_summary = textwrap.fill(summary[:150], width=35)
        draw.multiline_text(
            (540, 600),
            wrapped_summary,
            fill='#cccccc',
            font=body_font,
            anchor='mm',
            align='center'
        )
        
        # 브랜드 로고/워터마크
        draw.text(
            (540, 980),
            "@your_qa_blog",
            fill='#666666',
            font=body_font,
            anchor='mm'
        )
        
        return img
    
    def _create_insight_slide(self, title: str, insight: str) -> Image:
        """인사이트 슬라이드 생성."""
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        img = Image.new('RGB', (1080, 1080), color='#2d3561')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("NanumGothicBold.ttf", 50)
            body_font = ImageFont.truetype("NanumGothic.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # 제목 그리기
        draw.text((540, 150), title, fill='white', font=title_font, anchor='mm')
        
        # 인사이트 내용 그리기
        wrapped_text = textwrap.fill(insight[:300], width=30)
        draw.multiline_text(
            (540, 500),
            wrapped_text,
            fill='#e0e0e0',
            font=body_font,
            anchor='mm',
            align='center'
        )
        
        return img
    
    def _create_guide_slide(self, title: str, steps: List[str]) -> Image:
        """가이드 슬라이드 생성."""
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        img = Image.new('RGB', (1080, 1080), color='#1e3a5f')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("NanumGothicBold.ttf", 50)
            body_font = ImageFont.truetype("NanumGothic.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # 제목 그리기
        draw.text((540, 100), title, fill='white', font=title_font, anchor='mm')
        
        # 단계별 내용 그리기
        y_pos = 250
        for i, step in enumerate(steps[:5], 1):  # 최대 5개
            step_text = f"{i}. {step[:80]}"
            draw.text((100, y_pos), step_text, fill='#cccccc', font=body_font)
            y_pos += 150
        
        return img
    
    def _create_cta_slide(self, link: str) -> Image:
        """CTA 슬라이드 생성."""
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1080, 1080), color='#0f3460')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("NanumGothicBold.ttf", 60)
            body_font = ImageFont.truetype("NanumGothic.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        # CTA 텍스트
        draw.text((540, 400), "전체 내용 보기", fill='white', font=title_font, anchor='mm')
        draw.text((540, 500), link[:50], fill='#4a9eff', font=body_font, anchor='mm')
        draw.text((540, 600), "프로필 링크에서 확인하세요!", fill='#cccccc', font=body_font, anchor='mm')
        
        return img
    
    async def _create_media_container(self, image_url: str) -> Dict[str, Any]:
        """Instagram 미디어 컨테이너 생성."""
        import aiohttp
        
        url = f"{self.base_url}/{self.business_account_id}/media"
        params = {
            "image_url": image_url,
            "caption": "",
            "access_token": self.access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Instagram 미디어 컨테이너 생성 실패: {response.status} - {error_text}")
                return await response.json()
    
    async def _publish_media(self, carousel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Instagram 미디어 게시."""
        import aiohttp
        
        url = f"{self.base_url}/{self.business_account_id}/media"
        params = {
            "media_type": carousel_data.get("media_type", "CAROUSEL"),
            "children": ",".join(carousel_data.get("children", [])),
            "caption": carousel_data.get("caption", ""),
            "access_token": self.access_token
        }
        
        async with aiohttp.ClientSession() as session:
            # 미디어 컨테이너 생성
            async with session.post(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Instagram 미디어 생성 실패: {response.status} - {error_text}")
                creation_response = await response.json()
                creation_id = creation_response.get("id")
            
            # 실제 게시
            publish_url = f"{self.base_url}/{self.business_account_id}/media_publish"
            publish_params = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            
            async with session.post(publish_url, params=publish_params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Instagram 게시 실패: {response.status} - {error_text}")
                return await response.json()
    
    def _summarize_text(self, text: str, max_length: int) -> str:
        """텍스트를 지정된 길이로 요약."""
        if len(text) <= max_length:
            return text
        
        # 문장 단위로 자르기
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) < max_length - 3:
                summary += sentence + ". "
            else:
                break
        
        if not summary:
            summary = text[:max_length-3]
        
        return summary.strip() + "..."


class LinkedInPublisher:
    """LinkedIn 자동 게시 관리."""
    
    def __init__(self, access_token: str, person_urn: str):
        self.access_token = access_token
        self.person_urn = person_urn
        self.api_url = "https://api.linkedin.com/v2"
    
    async def create_article_post(
        self, 
        blog_post: Dict[str, Any]
    ) -> Dict[str, Any]:
        """블로그 포스트를 LinkedIn 아티클로 변환."""
        
        # LinkedIn 포스트 내용 생성
        content = self._create_linkedin_content(blog_post)
        
        # 포스트 데이터 구성
        post_data = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "description": {
                            "text": blog_post.get("summary", "")
                        },
                        "media": blog_post.get("link", ""),
                        "title": {
                            "text": blog_post.get("title", "")
                        }
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # API 호출
        response = await self._post_to_linkedin(post_data)
        
        logger.info(f"LinkedIn 포스트 게시 완료: {response.get('id')}")
        return response
    
    def _create_linkedin_content(self, blog_post: Dict[str, Any]) -> str:
        """LinkedIn용 전문적인 콘텐츠 생성."""
        
        content_parts = [
            f"🚀 {blog_post.get('title', '')}",
            "",
            "QA 엔지니어분들께 공유하고 싶은 인사이트입니다.",
            ""
        ]
        
        # 핵심 포인트 3가지
        insights = blog_post.get("qa_engineer_insights", [])[:3]
        if insights:
            content_parts.append("💡 핵심 인사이트:")
            for i, insight in enumerate(insights, 1):
                summary = self._summarize_text(insight, max_length=200)
                content_parts.append(f"{i}. {summary}")
            content_parts.append("")
        
        # 실무 적용 포인트
        if blog_post.get("practical_guide"):
            guide = blog_post["practical_guide"][0]
            content_parts.extend([
                "🛠️ 바로 적용 가능한 실무 가이드:",
                guide.get("title", ""),
                ""
            ])
        
        # 전문가 의견 인용
        if blog_post.get("expert_opinions"):
            opinion = blog_post["expert_opinions"][0]
            content_parts.extend([
                f"💭 {opinion.get('perspective', '')} 관점:",
                f'"{self._summarize_text(opinion.get("opinion", ""), max_length=150)}"',
                ""
            ])
        
        # CTA
        content_parts.extend([
            "📖 전체 내용과 상세한 구현 가이드는 아래 링크에서 확인하세요!",
            "",
            "여러분의 경험과 의견을 댓글로 공유해주시면 감사하겠습니다. 🙏",
            "",
            "#QualityAssurance #SoftwareTesting #TestAutomation #QAEngineer #테스트자동화"
        ])
        
        return "\n".join(content_parts)
    
    def _summarize_text(self, text: str, max_length: int) -> str:
        """텍스트를 지정된 길이로 요약."""
        if len(text) <= max_length:
            return text
        
        # 문장 단위로 자르기
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) < max_length - 3:
                summary += sentence + ". "
            else:
                break
        
        if not summary:
            summary = text[:max_length-3]
        
        return summary.strip() + "..."
    
    async def _post_to_linkedin(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """LinkedIn API로 포스트 게시."""
        import aiohttp
        
        url = f"{self.api_url}/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=post_data, headers=headers) as response:
                if response.status not in (200, 201):
                    error_text = await response.text()
                    raise RuntimeError(f"LinkedIn 포스트 게시 실패: {response.status} - {error_text}")
                return await response.json()


class TwitterPublisher:
    """Twitter/X 자동 게시 관리."""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.api_url = "https://api.twitter.com/2"
    
    async def create_thread(
        self, 
        blog_post: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """블로그 포스트를 Twitter 스레드로 변환."""
        
        tweets = []
        
        # 1. 메인 트윗
        main_tweet = self._create_main_tweet(blog_post)
        tweets.append(main_tweet)
        
        # 2. 인사이트 트윗들
        insights = blog_post.get("qa_engineer_insights", [])[:3]
        for i, insight in enumerate(insights, 1):
            insight_tweet = f"{i}/ {self._summarize_text(insight, max_length=250)}"
            tweets.append(insight_tweet)
        
        # 3. 실무 팁 트윗
        if blog_post.get("practical_guide"):
            guide = blog_post["practical_guide"][0]
            tip_tweet = f"💡 실무 팁: {guide.get('title', '')}\n\n즉시 적용 가능한 방법을 블로그에서 확인하세요!"
            tweets.append(tip_tweet)
        
        # 4. CTA 트윗
        cta_tweet = f"🔗 전체 내용 보기: {blog_post.get('link', '')}\n\n#QAEngineer #TestAutomation"
        tweets.append(cta_tweet)
        
        # 스레드로 연결하여 게시
        posted_tweets = await self._post_thread(tweets)
        
        logger.info(f"Twitter 스레드 게시 완료: {len(posted_tweets)}개 트윗")
        return posted_tweets
    
    def _create_main_tweet(self, blog_post: Dict[str, Any]) -> str:
        """메인 트윗 생성."""
        title = blog_post.get("title", "")
        
        # 이모지로 시선 끌기
        emoji_map = {
            "AI": "🤖",
            "자동화": "⚡",
            "테스트": "🧪",
            "품질": "✨"
        }
        
        emoji = "🔍"  # 기본 이모지
        for keyword, em in emoji_map.items():
            if keyword in title:
                emoji = em
                break
        
        tweet = f"{emoji} {title}\n\nQA 엔지니어가 꼭 알아야 할 내용을 정리했습니다.\n\n스레드에서 핵심 인사이트를 확인하세요! 👇"
        
        return tweet[:280]  # Twitter 글자 수 제한
    
    async def _post_thread(self, tweets: List[str]) -> List[Dict[str, Any]]:
        """Twitter 스레드 게시."""
        import aiohttp
        
        posted_tweets = []
        previous_tweet_id = None
        
        url = f"{self.api_url}/tweets"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            for i, tweet_text in enumerate(tweets):
                payload = {"text": tweet_text}
                
                # 첫 번째 트윗이 아니면 reply_to 추가
                if previous_tweet_id:
                    payload["reply"] = {"in_reply_to_tweet_id": previous_tweet_id}
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status not in (200, 201):
                        error_text = await response.text()
                        logger.error(f"Twitter 트윗 {i+1} 게시 실패: {response.status} - {error_text}")
                        continue
                    
                    result = await response.json()
                    tweet_id = result.get("data", {}).get("id")
                    if tweet_id:
                        previous_tweet_id = tweet_id
                        posted_tweets.append(result)
                    
                    # Rate limit 방지
                    await asyncio.sleep(1)
        
        return posted_tweets
    
    def _summarize_text(self, text: str, max_length: int) -> str:
        """텍스트를 지정된 길이로 요약."""
        if len(text) <= max_length:
            return text
        
        # 문장 단위로 자르기
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) < max_length - 3:
                summary += sentence + ". "
            else:
                break
        
        if not summary:
            summary = text[:max_length-3]
        
        return summary.strip() + "..."


class SocialMediaOrchestrator:
    """모든 소셜 미디어 플랫폼 통합 관리."""
    
    def __init__(self):
        self.platforms = {}
        self._init_platforms()
        self.schedule_queue = []
    
    def _init_platforms(self):
        """플랫폼별 퍼블리셔 초기화."""
        
        # Instagram
        if os.getenv("INSTAGRAM_ACCESS_TOKEN"):
            self.platforms["instagram"] = InstagramPublisher(
                access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                business_account_id=os.getenv("INSTAGRAM_BUSINESS_ID")
            )
        
        # LinkedIn
        if os.getenv("LINKEDIN_ACCESS_TOKEN"):
            self.platforms["linkedin"] = LinkedInPublisher(
                access_token=os.getenv("LINKEDIN_ACCESS_TOKEN"),
                person_urn=os.getenv("LINKEDIN_PERSON_URN")
            )
        
        # Twitter
        if os.getenv("TWITTER_BEARER_TOKEN"):
            self.platforms["twitter"] = TwitterPublisher(
                bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
            )
    
    async def publish_to_all_platforms(
        self, 
        blog_post_path: Path
    ) -> Dict[str, Any]:
        """모든 플랫폼에 게시."""
        
        # 블로그 포스트 읽기
        blog_post = self._parse_blog_post(blog_post_path)
        
        results = {}
        
        # 각 플랫폼에 병렬로 게시
        tasks = []
        
        if "instagram" in self.platforms:
            tasks.append(self._publish_to_instagram(blog_post))
        
        if "linkedin" in self.platforms:
            tasks.append(self._publish_to_linkedin(blog_post))
        
        if "twitter" in self.platforms:
            tasks.append(self._publish_to_twitter(blog_post))
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 정리
        for platform, result in zip(self.platforms.keys(), platform_results):
            if isinstance(result, Exception):
                results[platform] = {"status": "error", "message": str(result)}
                logger.error(f"{platform} 게시 실패: {result}")
            else:
                results[platform] = {"status": "success", "data": result}
        
        # 게시 통계 저장
        self._save_publishing_stats(blog_post_path, results)
        
        return results
    
    async def _publish_to_instagram(self, blog_post: Dict[str, Any]) -> Dict[str, Any]:
        """Instagram에 게시."""
        publisher = self.platforms["instagram"]
        return await publisher.create_carousel_post(blog_post, [])
    
    async def _publish_to_linkedin(self, blog_post: Dict[str, Any]) -> Dict[str, Any]:
        """LinkedIn에 게시."""
        publisher = self.platforms["linkedin"]
        return await publisher.create_article_post(blog_post)
    
    async def _publish_to_twitter(self, blog_post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Twitter에 게시."""
        publisher = self.platforms["twitter"]
        return await publisher.create_thread(blog_post)
    
    def schedule_post(
        self, 
        blog_post_path: Path, 
        platforms: List[str], 
        publish_time: datetime
    ) -> str:
        """게시 예약."""
        
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.schedule_queue.append({
            "id": schedule_id,
            "blog_post_path": blog_post_path,
            "platforms": platforms,
            "publish_time": publish_time,
            "status": "scheduled"
        })
        
        logger.info(f"게시 예약됨: {schedule_id} at {publish_time}")
        return schedule_id
    
    async def process_scheduled_posts(self):
        """예약된 게시물 처리."""
        
        while True:
            now = datetime.now()
            
            for schedule in self.schedule_queue:
                if (schedule["status"] == "scheduled" and 
                    schedule["publish_time"] <= now):
                    
                    logger.info(f"예약 게시 실행: {schedule['id']}")
                    
                    try:
                        results = await self.publish_to_all_platforms(
                            schedule["blog_post_path"]
                        )
                        schedule["status"] = "completed"
                        schedule["results"] = results
                    except Exception as exc:
                        schedule["status"] = "failed"
                        schedule["error"] = str(exc)
                        logger.error(f"예약 게시 실패: {exc}")
            
            # 1분마다 체크
            await asyncio.sleep(60)
    
    def _parse_blog_post(self, blog_post_path: Path) -> Dict[str, Any]:
        """블로그 포스트 파일 파싱."""
        
        with open(blog_post_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Front matter와 본문 분리
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front_matter = parts[1].strip()
            body = parts[2].strip()
        else:
            front_matter = ""
            body = content
        
        # Front matter 파싱 (간단한 YAML 파싱)
        metadata = {}
        for line in front_matter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"')
        
        # QA 관련 섹션 추출
        qa_data = self._extract_qa_sections(body)
        
        return {
            **metadata,
            **qa_data,
            "content": body,
            "link": f"https://your-blog.com/posts/{blog_post_path.stem}"
        }
    
    def _extract_qa_sections(self, body: str) -> Dict[str, Any]:
        """본문에서 QA 관련 섹션 추출."""
        
        sections = {}
        
        # 정규식으로 섹션 추출
        patterns = {
            "qa_engineer_insights": r"## QA Engineer가 알아야 할 핵심 내용\n(.*?)(?=\n##|$)",
            "practical_guide": r"## 실무 적용 가이드\n(.*?)(?=\n##|$)",
            "expert_opinions": r"## 전문가 의견\n(.*?)(?=\n##|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, body, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # 리스트 아이템 추출
                items = re.findall(r'[-*]\s+(.+?)(?=\n[-*]|\n\n|$)', content, re.DOTALL)
                sections[key] = [item.strip() for item in items]
        
        return sections
    
    def _save_publishing_stats(
        self, 
        blog_post_path: Path, 
        results: Dict[str, Any]
    ):
        """게시 통계 저장."""
        
        stats_file = Path("data/social_media_stats.json")
        
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                stats = json.load(f)
        else:
            stats = {"posts": []}
        
        stats["posts"].append({
            "blog_post": str(blog_post_path),
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        # 최근 100개만 유지
        stats["posts"] = stats["posts"][-100:]
        
        stats_file.parent.mkdir(exist_ok=True)
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)


# 사용 예시
if __name__ == "__main__":
    async def main():
        # 오케스트레이터 초기화
        orchestrator = SocialMediaOrchestrator()
        
        # 최신 블로그 포스트 찾기
        posts_dir = Path("_posts")
        latest_post = max(posts_dir.glob("**/*.md"), key=os.path.getmtime)
        
        # 모든 플랫폼에 게시
        results = await orchestrator.publish_to_all_platforms(latest_post)
        
        print(f"게시 결과: {json.dumps(results, indent=2, ensure_ascii=False)}")
        
        # 또는 예약 게시
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=9, minute=0, second=0)
        
        schedule_id = orchestrator.schedule_post(
            latest_post,
            ["instagram", "linkedin", "twitter"],
            tomorrow
        )
        
        print(f"예약 ID: {schedule_id}")
    
    # 실행
    asyncio.run(main())
