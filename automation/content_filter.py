"""GeekNews 콘텐츠 필터링 및 분류 모듈.

기사의 인기도, AI 관련성, 트렌드 여부를 판단하여 우선순위를 결정합니다.
"""
from __future__ import annotations

import re
import typing as t
from dataclasses import dataclass
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from automation.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ContentMetrics:
    """콘텐츠 메트릭."""
    
    votes: int = 0
    comments: int = 0
    is_ai_related: bool = False
    is_trending: bool = False
    priority_score: float = 0.0
    categories: list[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []


class ContentFilter:
    """GeekNews 콘텐츠 필터링 및 우선순위 결정."""
    
    # AI 관련 키워드 (QA 자동화 포함)
    AI_KEYWORDS = [
        "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
        "llm", "gpt", "claude", "gemini", "openai", "anthropic", "neural network",
        "transformer", "자연어처리", "nlp", "컴퓨터비전", "computer vision",
        "강화학습", "reinforcement learning", "생성형", "generative",
        # QA 자동화 관련
        "테스트 자동화", "test automation", "qa automation", "test automation framework",
        "ai testing", "ai-driven testing", "ai-powered qa", "qa ai", "testing ai",
        "automated testing", "testing automation", "test automation tool",
        "qa workflow automation", "qa process automation", "intelligent testing",
        "smart testing", "ai test generation", "ml testing", "ai qa",
        # 테스팅 도구/프레임워크
        "playwright", "selenium", "cypress", "pytest", "testng", "junit",
        "appium", "robot framework", "karate", "rest assured", "postman automation",
        "테스팅", "testing framework", "test tool", "qa tool"
    ]
    
    # 트렌딩 기술 키워드
    TRENDING_KEYWORDS = [
        "kubernetes", "k8s", "docker", "devops", "cicd", "ci/cd",
        "react", "vue", "next.js", "typescript", "rust", "golang", "go",
        "microservices", "serverless", "cloud", "aws", "azure", "gcp",
        "api", "rest", "graphql", "websocket", "grpc"
    ]
    
    # QA/테스팅 관련 키워드 (자동화 중심)
    QA_KEYWORDS = [
        "qa", "quality assurance", "test", "testing", "automation", "automated",
        "unit test", "integration test", "e2e", "end-to-end", "api test", "ui test",
        "performance", "load test", "stress test", "security test", "regression test",
        "테스트", "품질", "자동화", "성능", "부하", "테스트 케이스", "테스트 시나리오",
        # QA 자동화 관련
        "test automation", "qa automation", "testing automation", "automated qa",
        "ci/cd testing", "continuous testing", "shift-left testing", "shift-right testing",
        "devops testing", "test orchestration", "test execution", "test reporting",
        "test analytics", "test metrics", "test coverage", "code coverage",
        # AI 기반 QA 자동화
        "ai testing", "ml testing", "ai qa", "intelligent testing", "smart qa",
        "ai test generation", "automated test creation", "test data generation",
        "visual testing", "visual regression", "screenshot testing"
    ]
    
    def __init__(
        self, 
        min_votes: int = 10,
        min_comments: int = 0,
        enable_scraping: bool = False
    ):
        self.min_votes = min_votes
        self.min_comments = min_comments
        self.enable_scraping = enable_scraping
    
    def analyze(self, item: t.Mapping[str, t.Any]) -> ContentMetrics:
        """기사를 분석하여 메트릭을 계산한다."""
        title = item.get("title", "")
        summary = item.get("summary", "")
        url = item.get("link", "")
        
        metrics = ContentMetrics()
        
        # 1. 인기도 수집 (웹 스크래핑 필요시)
        if self.enable_scraping and url:
            metrics.votes, metrics.comments = self._scrape_metrics(url)
        
        # 2. AI 관련성 판단
        metrics.is_ai_related = self._is_ai_related(title, summary)
        
        # 3. 트렌드 여부 판단
        metrics.is_trending = self._is_trending(title, summary)
        
        # 4. 카테고리 분류
        metrics.categories = self._categorize(title, summary)
        
        # 5. 우선순위 점수 계산
        metrics.priority_score = self._calculate_priority(metrics, title, summary)
        
        return metrics
    
    def _scrape_metrics(self, url: str) -> tuple[int, int]:
        """GeekNews 페이지에서 투표수와 댓글 수를 스크래핑한다."""
        if not REQUESTS_AVAILABLE:
            return 0, 0
        
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=10
            )
            response.raise_for_status()
            html = response.text
            
            # 투표수 추출 (예: <span class="vote_count">123</span>)
            votes = 0
            vote_match = re.search(r'vote[_-]?count["\'>:]\s*(\d+)', html, re.IGNORECASE)
            if vote_match:
                votes = int(vote_match.group(1))
            else:
                # 다른 패턴 시도
                vote_match = re.search(r'(\d+)\s*vote', html, re.IGNORECASE)
                if vote_match:
                    votes = int(vote_match.group(1))
            
            # 댓글 수 추출
            comments = 0
            comment_match = re.search(r'comment[_-]?count["\'>:]\s*(\d+)', html, re.IGNORECASE)
            if comment_match:
                comments = int(comment_match.group(1))
            else:
                comment_match = re.search(r'(\d+)\s*comment', html, re.IGNORECASE)
                if comment_match:
                    comments = int(comment_match.group(1))
            
            return votes, comments
            
        except Exception as exc:
            logger.warning(f"메트릭 스크래핑 중 오류 ({url}): {exc}", exc_info=True)
            return 0, 0
    
    def _is_ai_related(self, title: str, summary: str) -> bool:
        """AI 관련 기사인지 판단한다."""
        text = f"{title} {summary}".lower()
        
        for keyword in self.AI_KEYWORDS:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _is_trending(self, title: str, summary: str) -> bool:
        """트렌딩 기술 관련 기사인지 판단한다."""
        text = f"{title} {summary}".lower()
        
        for keyword in self.TRENDING_KEYWORDS:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _categorize(self, title: str, summary: str) -> list[str]:
        """기사를 카테고리로 분류한다."""
        text = f"{title} {summary}".lower()
        categories: list[str] = []
        
        # Daily Life 키워드 우선 확인 (QA와 관련 없으면 Daily Life로 분류)
        daily_life_keywords = [
            "파티", "파티를", "주식", "투자", "리뷰", "소감", "일상",
            "party", "stock", "investment", "review", "daily", "생일",
            "birthday", "21가지", "21 facts"
        ]
        has_daily_life_keyword = any(keyword in text for keyword in daily_life_keywords)
        has_qa_keyword = any(kw in text for kw in ["test", "qa", "testing", "automation", "quality"])
        
        # Daily Life 키워드가 있고 QA 키워드가 없으면 Daily Life로 분류
        if has_daily_life_keyword and not has_qa_keyword:
            categories.append("Daily Life")
            return categories
        
        # AI 카테고리
        if self._is_ai_related(title, summary):
            categories.append("AI")
        
        # QA/Testing 카테고리 (명확한 QA 키워드가 있을 때만)
        qa_score = 0
        for keyword in self.QA_KEYWORDS:
            if keyword.lower() in text:
                qa_score += 1
                if qa_score >= 2:  # 최소 2개 이상의 QA 키워드가 있어야 QA 카테고리
                    categories.append("QA")
                    break
        
        # 개발/프로그래밍 (QA 카테고리가 없을 때만)
        if "QA" not in categories:
            dev_keywords = ["programming", "developer", "코딩", "개발", "framework", "library"]
            for keyword in dev_keywords:
                if keyword.lower() in text:
                    categories.append("Development")
                    break
        
        # DevOps
        devops_keywords = ["devops", "kubernetes", "docker", "ci/cd", "deployment"]
        for keyword in devops_keywords:
            if keyword.lower() in text:
                categories.append("DevOps")
                break
        
        # 기본 카테고리
        if not categories:
            categories.append("Technology")
        
        return categories
    
    def _calculate_priority(
        self, 
        metrics: ContentMetrics, 
        title: str, 
        summary: str
    ) -> float:
        """우선순위 점수를 계산한다 (0-100)."""
        score = 0.0
        text = f"{title} {summary}".lower()
        
        # 1. AI 관련성 (40점)
        if metrics.is_ai_related:
            score += 40
        
        # 2. QA 자동화 관련성 추가 점수 (AI 관련이면서 QA도 관련된 경우)
        if metrics.is_ai_related and "QA" in metrics.categories:
            # AI + QA 자동화는 추가 10점
            score += 10
        elif "QA" in metrics.categories:
            # QA 관련성 (30점으로 증가 - 자동화 관련 키워드가 있으면 추가 점수)
            qa_automation_keywords = ["automation", "automated", "자동화", "ci/cd", "continuous", "test", "testing"]
            if any(keyword in text for keyword in qa_automation_keywords):
                score += 30  # QA 자동화는 높은 점수
            else:
                score += 20  # 일반 QA는 20점
        
        # Daily Life 키워드가 있으면 QA 점수 크게 감점
        daily_life_keywords = ["파티", "주식", "투자", "리뷰", "소감", "생일", "party", "stock", "investment"]
        if any(keyword in text for keyword in daily_life_keywords):
            if "test" not in text and "qa" not in text and "testing" not in text:
                score -= 50  # QA 관련성 크게 감점
        
        # 3. 투표수 기반 인기도 (30점)
        if metrics.votes >= self.min_votes:
            # 투표수에 비례하여 점수 부여 (최대 30점)
            vote_score = min(30, (metrics.votes / 50) * 30)
            score += vote_score
        
        # 4. 댓글 수 (10점)
        if metrics.comments > 0:
            comment_score = min(10, (metrics.comments / 20) * 10)
            score += comment_score
        
        # 5. 트렌드 여부 (10점)
        if metrics.is_trending:
            score += 10
        
        return min(100.0, score)
    
    def should_process(self, metrics: ContentMetrics) -> bool:
        """기사를 처리할지 여부를 결정한다."""
        # AI 관련 항목은 무조건 포함 (QA 자동화 포함)
        if metrics.is_ai_related:
            return True
        
        # QA 관련 항목도 포함 (QA 블로그이므로)
        if "QA" in metrics.categories:
            return True
        
        # 인기도 기준 충족
        if metrics.votes >= self.min_votes:
            return True
        
        # 트렌드이면서 일정 이상의 점수
        if metrics.is_trending and metrics.priority_score >= 20:
            return True
        
        # 투표수 정보가 없는 경우 (RSS 피드에서 투표수 정보가 없을 수 있음)
        # 우선순위 점수가 일정 이상이면 처리 (QA 자동화는 더 낮은 기준)
        if metrics.votes == 0:
            # QA 자동화는 30점 이상이면 처리 (기준 상향), 일반 항목은 15점 이상
            if "QA" in metrics.categories:
                if metrics.priority_score >= 30:  # 10 → 30으로 상향
                    return True
            elif metrics.priority_score >= 15:
                return True
        
        return False
    
    def filter_and_sort(
        self, 
        items: list[t.Mapping[str, t.Any]], 
        max_items: int = 10
    ) -> list[tuple[t.Mapping[str, t.Any], ContentMetrics]]:
        """기사 목록을 필터링하고 우선순위 순으로 정렬한다."""
        analyzed: list[tuple[t.Mapping[str, t.Any], ContentMetrics]] = []
        
        for item in items:
            metrics = self.analyze(item)
            if self.should_process(metrics):
                analyzed.append((item, metrics))
        
        # 우선순위 점수 기준 내림차순 정렬
        analyzed.sort(key=lambda x: x[1].priority_score, reverse=True)
        
        # AI 관련 항목은 최소 1개 이상 포함 보장
        ai_items = [x for x in analyzed if x[1].is_ai_related]
        non_ai_items = [x for x in analyzed if not x[1].is_ai_related]
        
        result: list[tuple[t.Mapping[str, t.Any], ContentMetrics]] = []
        
        # AI 관련 항목 먼저 추가 (최대 절반)
        ai_quota = max(1, max_items // 2)
        result.extend(ai_items[:ai_quota])
        
        # 나머지 슬롯에 다른 항목 추가
        remaining_slots = max_items - len(result)
        result.extend(non_ai_items[:remaining_slots])
        
        return result[:max_items]


# 사용 예시
if __name__ == "__main__":
    filter_engine = ContentFilter(min_votes=10, enable_scraping=False)
    
    sample_items = [
        {
            "title": "OpenAI GPT-4 Turbo 출시",
            "summary": "OpenAI가 새로운 GPT-4 Turbo 모델을 발표했습니다.",
            "link": "https://news.hada.io/topic?id=1"
        },
        {
            "title": "Kubernetes 1.29 릴리스",
            "summary": "Kubernetes 최신 버전이 출시되었습니다.",
            "link": "https://news.hada.io/topic?id=2"
        },
        {
            "title": "일반 기사",
            "summary": "일반적인 기술 뉴스입니다.",
            "link": "https://news.hada.io/topic?id=3"
        }
    ]
    
    results = filter_engine.filter_and_sort(sample_items, max_items=5)
    
    logger.info("필터링 및 정렬 결과:")
    for item, metrics in results:
        logger.info(f"  제목: {item['title']}")
        logger.info(f"  우선순위: {metrics.priority_score:.1f}")
        logger.info(f"  AI 관련: {metrics.is_ai_related}")
        logger.info(f"  카테고리: {', '.join(metrics.categories)}")
        logger.info("")

