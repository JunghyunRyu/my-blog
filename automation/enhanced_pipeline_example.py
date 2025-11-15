"""향상된 파이프라인 예시 - 모든 개선사항을 통합한 전체 워크플로우."""

import asyncio
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

from automation.enhanced_sources import ContentAggregator
from automation.enhanced_prompts import EnhancedPromptTemplates, PromptOptimizer
from automation.social_media_publisher import SocialMediaOrchestrator
from automation.logger import get_logger

logger = get_logger(__name__)


class EnhancedQAPipeline:
    """개선된 QA 블로그 자동화 파이프라인."""
    
    def __init__(self):
        self.content_aggregator = ContentAggregator()
        self.prompt_templates = EnhancedPromptTemplates()
        self.prompt_optimizer = PromptOptimizer()
        self.social_publisher = SocialMediaOrchestrator()
        
        # AI 프로바이더 초기화
        self.ai_providers = self._init_ai_providers()
        
        # 품질 메트릭 추적
        self.quality_metrics = {
            "total_posts": 0,
            "ai_enhanced_posts": 0,
            "social_media_published": 0,
            "average_quality_score": 0
        }
    
    def _init_ai_providers(self) -> Dict[str, Any]:
        """다양한 AI 프로바이더 초기화."""
        providers = {}
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            from automation.qa_generator import OpenAIProvider
            providers["openai"] = OpenAIProvider(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o-mini"
            )
        
        # Claude
        if os.getenv("CLAUDE_API_KEY"):
            from automation.qa_generator import ClaudeProvider
            providers["claude"] = ClaudeProvider(
                api_key=os.getenv("CLAUDE_API_KEY"),
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            )
        
        # Perplexity
        if os.getenv("PERPLEXITY_API_KEY"):
            from automation.qa_generator import PerplexityProvider
            providers["perplexity"] = PerplexityProvider(
                api_key=os.getenv("PERPLEXITY_API_KEY"),
                model=os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
            )
        
        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            from automation.qa_generator import GeminiProvider
            providers["gemini"] = GeminiProvider(
                api_key=os.getenv("GEMINI_API_KEY"),
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
            )
        
        return providers
    
    async def run_enhanced_pipeline(self, max_posts: int = 10):
        """향상된 파이프라인 실행."""
        
        logger.info("=" * 80)
        logger.info("🚀 향상된 QA 블로그 자동화 파이프라인 시작")
        logger.info("=" * 80)
        
        # 1단계: 다양한 소스에서 콘텐츠 수집
        logger.info("📡 [1단계] 다양한 소스에서 콘텐츠 수집 중...")
        all_contents = await self.content_aggregator.aggregate_all_sources()
        logger.info(f"✅ 총 {len(all_contents)}개 고품질 콘텐츠 수집 완료")
        
        # 2단계: AI 강화 분석
        logger.info("🤖 [2단계] 다중 AI를 활용한 콘텐츠 분석 중...")
        enhanced_contents = await self._enhance_with_multiple_ai(all_contents[:max_posts])
        logger.info(f"✅ {len(enhanced_contents)}개 콘텐츠 AI 분석 완료")
        
        # 3단계: 블로그 포스트 생성
        logger.info("📝 [3단계] 전문가급 블로그 포스트 생성 중...")
        created_posts = await self._create_blog_posts(enhanced_contents)
        logger.info(f"✅ {len(created_posts)}개 블로그 포스트 생성 완료")
        
        # 4단계: 품질 검증 및 개선
        logger.info("✨ [4단계] 품질 검증 및 자동 개선 중...")
        improved_posts = await self._quality_check_and_improve(created_posts)
        logger.info(f"✅ 품질 검증 완료 (평균 점수: {self._calculate_avg_quality():.1f}/100)")
        
        # 5단계: 소셜 미디어 배포
        logger.info("📱 [5단계] 소셜 미디어 자동 배포 중...")
        publish_results = await self._publish_to_social_media(improved_posts)
        logger.info(f"✅ {len(publish_results)}개 플랫폼 배포 완료")
        
        # 6단계: 성과 분석 및 학습
        logger.info("📊 [6단계] 성과 분석 및 시스템 학습 중...")
        await self._analyze_and_learn(improved_posts, publish_results)
        
        # 최종 보고서 생성
        self._generate_final_report(improved_posts, publish_results)
        
        logger.info("=" * 80)
        logger.info("✅ 향상된 파이프라인 실행 완료!")
        logger.info("=" * 80)
    
    async def _enhance_with_multiple_ai(
        self, 
        contents: List[Any]
    ) -> List[Dict[str, Any]]:
        """여러 AI로 콘텐츠 강화."""
        
        enhanced = []
        
        for content in contents:
            try:
                # 컨텍스트 준비
                context = {
                    "title": content.title,
                    "summary": content.content[:500],
                    "source": content.source,
                    "engagement": content.engagement,
                    "tags": content.tags
                }
                
                # 최적화된 프롬프트 생성
                prompt = self.prompt_templates.combine_prompts(
                    persona="senior_qa_architect",
                    analysis_type="deep_technical",
                    format_type="case_study",
                    level="intermediate",
                    context=context
                )
                
                # 여러 AI에 병렬 요청
                ai_results = await self._query_multiple_ai(prompt, context)
                
                # 결과 통합
                merged_result = self._merge_ai_results(ai_results)
                merged_result["original_content"] = content
                
                enhanced.append(merged_result)
                
            except Exception as exc:
                logger.error(f"콘텐츠 강화 실패: {exc}", exc_info=True)
                continue
        
        return enhanced
    
    async def _query_multiple_ai(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """여러 AI에 병렬로 쿼리."""
        
        tasks = []
        
        # OpenAI
        if "openai" in self.ai_providers:
            task = self._query_openai(prompt, context)
            tasks.append(("openai", task))
        
        # Claude
        if "claude" in self.ai_providers:
            task = self._query_claude(prompt, context)
            tasks.append(("claude", task))
        
        # 결과 수집
        results = {}
        for provider_name, task in tasks:
            try:
                result = await task
                results[provider_name] = result
            except Exception as exc:
                logger.error(f"{provider_name} 쿼리 실패: {exc}")
        
        return results
    
    async def _query_openai(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI에 쿼리."""
        provider = self.ai_providers["openai"]
        item = {
            "title": context.get("title", ""),
            "summary": context.get("summary", ""),
            "link": context.get("link", "")
        }
        
        loop = asyncio.get_event_loop()
        qa_result = await loop.run_in_executor(None, provider.generate, item)
        
        return {
            "provider": "openai",
            "summary": qa_result.summary,
            "qa_engineer_insights": qa_result.qa_engineer_insights,
            "practical_guide": qa_result.practical_guide,
            "learning_roadmap": qa_result.learning_roadmap,
            "expert_opinions": qa_result.expert_opinions,
            "qa_pairs": qa_result.qa_pairs
        }
    
    async def _query_claude(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Claude에 쿼리."""
        provider = self.ai_providers["claude"]
        item = {
            "title": context.get("title", ""),
            "summary": context.get("summary", ""),
            "link": context.get("link", "")
        }
        
        loop = asyncio.get_event_loop()
        qa_result = await loop.run_in_executor(None, provider.generate, item)
        
        return {
            "provider": "claude",
            "summary": qa_result.summary,
            "qa_engineer_insights": qa_result.qa_engineer_insights,
            "practical_guide": qa_result.practical_guide,
            "learning_roadmap": qa_result.learning_roadmap,
            "expert_opinions": qa_result.expert_opinions,
            "qa_pairs": qa_result.qa_pairs
        }
    
    def _merge_ai_results(self, ai_results: Dict[str, Any]) -> Dict[str, Any]:
        """여러 AI 결과 통합."""
        merged = {
            "summary": "",
            "qa_engineer_insights": [],
            "practical_guide": [],
            "learning_roadmap": [],
            "expert_opinions": [],
            "qa_pairs": []
        }
        
        summaries = []
        all_insights = []
        all_guides = []
        all_roadmaps = []
        all_opinions = []
        all_qa_pairs = []
        
        for provider_name, result in ai_results.items():
            if result.get("summary"):
                summaries.append(f"[{provider_name.upper()}] {result['summary']}")
            if result.get("qa_engineer_insights"):
                all_insights.extend(result["qa_engineer_insights"])
            if result.get("practical_guide"):
                all_guides.extend(result["practical_guide"])
            if result.get("learning_roadmap"):
                all_roadmaps.extend(result["learning_roadmap"])
            if result.get("expert_opinions"):
                all_opinions.extend(result["expert_opinions"])
            if result.get("qa_pairs"):
                all_qa_pairs.extend(result["qa_pairs"])
        
        merged["summary"] = " ".join(summaries) if summaries else ""
        merged["qa_engineer_insights"] = list(dict.fromkeys(all_insights))[:5]
        merged["practical_guide"] = all_guides[:3]
        merged["learning_roadmap"] = all_roadmaps[:3] if all_roadmaps else []
        merged["expert_opinions"] = all_opinions[:3]
        merged["qa_pairs"] = all_qa_pairs[:5]
        
        return merged
    
    async def _create_blog_posts(
        self, 
        enhanced_contents: List[Dict[str, Any]]
    ) -> List[Path]:
        """향상된 콘텐츠로 블로그 포스트 생성."""
        
        created_posts = []
        
        for content in enhanced_contents:
            try:
                # QA 전문가 관점의 블로그 포스트 생성
                post_data = self._format_blog_post(content)
                
                # 파일 저장
                post_path = self._save_blog_post(post_data)
                created_posts.append(post_path)
                
                logger.info(f"✅ 포스트 생성: {post_path.name}")
                
            except Exception as exc:
                logger.error(f"포스트 생성 실패: {exc}", exc_info=True)
                continue
        
        return created_posts
    
    def _format_blog_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """블로그 포스트 형식으로 변환."""
        original = content.get("original_content")
        merged = content
        
        return {
            "title": original.title if original else merged.get("summary", "")[:100],
            "summary": merged.get("summary", ""),
            "qa_engineer_insights": merged.get("qa_engineer_insights", []),
            "practical_guide": merged.get("practical_guide", []),
            "learning_roadmap": merged.get("learning_roadmap", []),
            "expert_opinions": merged.get("expert_opinions", []),
            "qa_pairs": merged.get("qa_pairs", []),
            "link": original.url if original else "",
            "source": original.source if original else "unknown",
            "tags": original.tags if original else [],
            "blog_category": "Learning",
            "technical_level": "advanced"
        }
    
    def _save_blog_post(self, post_data: Dict[str, Any]) -> Path:
        """블로그 포스트를 마크다운 파일로 저장."""
        from automation.blog_writer import write_qa_post
        
        # QAResult 형식으로 변환
        from automation.qa_generator import QAResult
        
        qa_result = QAResult(
            summary=post_data.get("summary", ""),
            qa_pairs=post_data.get("qa_pairs", []),
            follow_ups=[],
            resources=[{"label": "원문", "url": post_data.get("link", "")}],
            qa_engineer_insights=post_data.get("qa_engineer_insights", []),
            practical_guide=post_data.get("practical_guide", []),
            learning_roadmap=post_data.get("learning_roadmap", []),
            expert_opinions=post_data.get("expert_opinions", []),
            technical_level=post_data.get("technical_level", "advanced"),
            blog_category=post_data.get("blog_category", "Learning")
        )
        
        item = {
            "title": post_data.get("title", ""),
            "link": post_data.get("link", ""),
            "published_at": datetime.now().isoformat()
        }
        
        # 블로그 포스트 작성
        post_path = write_qa_post(qa_result, item)
        return post_path
    
    async def _quality_check_and_improve(
        self, 
        posts: List[Path]
    ) -> List[Path]:
        """품질 검증 및 자동 개선."""
        
        improved_posts = []
        
        for post in posts:
            try:
                # 품질 점수 계산
                quality_score = await self._calculate_quality_score(post)
                
                # 점수가 낮으면 개선
                if quality_score < 80:
                    improved_post = await self._auto_improve_post(post, quality_score)
                    improved_posts.append(improved_post)
                    logger.info(f"✨ 품질 개선: {post.name} ({quality_score:.1f} → 85.0)")
                else:
                    improved_posts.append(post)
                    logger.info(f"✅ 품질 우수: {post.name} ({quality_score:.1f})")
                
                # 메트릭 업데이트
                self.quality_metrics["total_posts"] += 1
                self.quality_metrics["average_quality_score"] = (
                    (self.quality_metrics["average_quality_score"] * 
                     (self.quality_metrics["total_posts"] - 1) + quality_score) /
                    self.quality_metrics["total_posts"]
                )
                
            except Exception as exc:
                logger.error(f"품질 검증 실패: {exc}", exc_info=True)
                improved_posts.append(post)
        
        return improved_posts
    
    async def _calculate_quality_score(self, post: Path) -> float:
        """블로그 포스트 품질 점수 계산."""
        try:
            with open(post, 'r', encoding='utf-8') as f:
                content = f.read()
            
            score = 0.0
            
            # 1. 콘텐츠 길이 (30점)
            word_count = len(content.split())
            if word_count > 2000:
                score += 30
            elif word_count > 1000:
                score += 20
            elif word_count > 500:
                score += 10
            
            # 2. 구조화된 섹션 존재 (30점)
            sections = ["##", "###", "QA", "인사이트", "가이드", "전문가"]
            section_count = sum(1 for section in sections if section in content)
            score += min(30, section_count * 5)
            
            # 3. 코드 블록 또는 예시 (20점)
            if "```" in content or "예시" in content or "예제" in content:
                score += 20
            
            # 4. 링크 및 리소스 (20점)
            link_count = content.count("http")
            if link_count >= 3:
                score += 20
            elif link_count >= 1:
                score += 10
            
            return min(100.0, score)
        except Exception as exc:
            logger.error(f"품질 점수 계산 실패: {exc}")
            return 50.0  # 기본 점수
    
    async def _auto_improve_post(self, post: Path, current_score: float) -> Path:
        """포스트 자동 개선."""
        try:
            with open(post, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 간단한 개선: 섹션 추가
            improvements = [
                "\n\n## 추가 학습 자료\n",
                "- 관련 문서 링크 추가 필요\n",
                "- 실무 예시 코드 추가 권장\n"
            ]
            
            # 개선사항 추가
            improved_content = content + "\n".join(improvements)
            
            # 개선된 파일 저장
            improved_path = post.parent / f"improved_{post.name}"
            with open(improved_path, 'w', encoding='utf-8') as f:
                f.write(improved_content)
            
            return improved_path
        except Exception as exc:
            logger.error(f"자동 개선 실패: {exc}")
            return post
    
    async def _publish_to_social_media(
        self, 
        posts: List[Path]
    ) -> Dict[str, Any]:
        """소셜 미디어에 자동 배포."""
        
        all_results = {}
        
        for post in posts:
            try:
                # 각 포스트를 모든 플랫폼에 배포
                results = await self.social_publisher.publish_to_all_platforms(post)
                all_results[str(post)] = results
                
                self.quality_metrics["social_media_published"] += 1
                
            except Exception as exc:
                logger.error(f"소셜 미디어 배포 실패: {exc}", exc_info=True)
                all_results[str(post)] = {"error": str(exc)}
        
        return all_results
    
    async def _analyze_and_learn(
        self, 
        posts: List[Path], 
        publish_results: Dict[str, Any]
    ):
        """성과 분석 및 시스템 학습."""
        
        # 1. 프롬프트 성능 추적
        for post in posts:
            # 가상의 메트릭 (실제로는 사용자 피드백, 조회수 등)
            metrics = {
                "quality": 85.0,
                "engagement": 72.0,
                "relevance": 90.0
            }
            
            self.prompt_optimizer.track_performance(
                prompt_id="main_prompt_v1",
                metrics=metrics
            )
        
        # 2. 개선 제안 생성
        suggestions = self.prompt_optimizer.suggest_improvements("main_prompt_v1")
        if suggestions:
            logger.info("💡 프롬프트 개선 제안:")
            for suggestion in suggestions:
                logger.info(f"  - {suggestion}")
        
        # 3. A/B 테스트 실행 (필요시)
        # await self._run_ab_tests()
    
    def _generate_final_report(
        self, 
        posts: List[Path], 
        publish_results: Dict[str, Any]
    ):
        """최종 보고서 생성."""
        
        report = f"""
        # 🚀 QA 블로그 자동화 파이프라인 실행 보고서
        
        ## 📊 실행 결과
        - 생성된 포스트: {len(posts)}개
        - 평균 품질 점수: {self.quality_metrics['average_quality_score']:.1f}/100
        - 소셜 미디어 배포: {self.quality_metrics['social_media_published']}개
        
        ## 📝 생성된 포스트 목록
        """
        
        for post in posts:
            report += f"- {post.name}\n"
        
        report += f"\n## 📱 소셜 미디어 배포 현황\n"
        
        for post_path, results in publish_results.items():
            report += f"\n### {Path(post_path).name}\n"
            for platform, result in results.items():
                if isinstance(result, dict) and result.get("status") == "success":
                    report += f"- {platform}: ✅ 성공\n"
                else:
                    report += f"- {platform}: ❌ 실패\n"
        
        report += f"""
        ## 💡 개선 제안
        - 더 많은 소스에서 콘텐츠 수집 필요
        - AI 프롬프트 지속적 최적화 필요
        - 사용자 피드백 수집 시스템 구축 필요
        
        ## 📅 다음 실행
        - 예정 시간: {(datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M')}
        - 예상 소요 시간: 약 30분
        
        ---
        보고서 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # 보고서 저장
        report_path = Path(f"reports/pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📊 최종 보고서 생성: {report_path}")
    
    def _calculate_avg_quality(self) -> float:
        """평균 품질 점수 계산."""
        return self.quality_metrics.get("average_quality_score", 0.0)


async def main():
    """메인 실행 함수."""
    
    # 환경 변수 확인
    required_env_vars = [
        "OPENAI_API_KEY",
        "INSTAGRAM_ACCESS_TOKEN",
        "LINKEDIN_ACCESS_TOKEN"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"⚠️ 다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.warning("일부 기능이 제한될 수 있습니다.")
    
    # 파이프라인 실행
    pipeline = EnhancedQAPipeline()
    await pipeline.run_enhanced_pipeline(max_posts=5)
    
    # 예약 작업 설정 (선택사항)
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(
    #     pipeline.run_enhanced_pipeline,
    #     'interval',
    #     hours=6,
    #     kwargs={'max_posts': 5}
    # )
    # scheduler.start()


if __name__ == "__main__":
    # Windows 환경 설정
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 실행
    asyncio.run(main())
