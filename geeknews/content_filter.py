"""GeekNews 콘텐츠 필터링 및 분류 모듈.

기사의 인기도, AI 관련성, 트렌드 여부를 판단하여 우선순위를 결정합니다.
"""
from __future__ import annotations

import re
import typing as t
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ContentMetrics:
    """콘텐츠 메트릭."""
    
    votes: int = 0
    comments: int = 0
    is_ai_related: bool = False
    is_trending: bool = False
    priority_score: float = 0.0
    categories: list[str] = None
    target_category: str = "learning"  # "learning" 또는 "qa-engineer"
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []
    
    def get_star_rating(self) -> str:
        """우선순위 점수를 별점으로 변환한다.
        
        Returns:
            별점 문자열 (⭐⭐⭐ ~ ⭐⭐⭐⭐⭐)
        """
        if self.priority_score >= 80:
            return "⭐⭐⭐⭐⭐"  # 별 5개 - 모두가 알아야 할 매우 중요한 내용
        elif self.priority_score >= 60:
            return "⭐⭐⭐⭐"  # 별 4개 - 고급 엔지니어들이 알아야 할 내용
        elif self.priority_score >= 40:
            return "⭐⭐⭐"  # 별 3개 - 선택적으로 알면 좋은 내용
        else:
            return "⭐⭐⭐"  # 기본 3개


class ContentFilter:
    """GeekNews 콘텐츠 필터링 및 우선순위 결정."""
    
    # AI 관련 키워드
    AI_KEYWORDS = [
        "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
        "llm", "gpt", "claude", "gemini", "openai", "anthropic", "neural network",
        "transformer", "자연어처리", "nlp", "컴퓨터비전", "computer vision",
        "강화학습", "reinforcement learning", "생성형", "generative",
        "테스트 자동화", "test automation", "qa automation", "playwright",
        "selenium", "cypress", "pytest", "테스팅", "testing framework"
    ]
    
    # 트렌딩 기술 키워드
    TRENDING_KEYWORDS = [
        "kubernetes", "k8s", "docker", "devops", "cicd", "ci/cd",
        "react", "vue", "next.js", "typescript", "rust", "golang", "go",
        "microservices", "serverless", "cloud", "aws", "azure", "gcp",
        "api", "rest", "graphql", "websocket", "grpc"
    ]
    
    # QA/테스팅 관련 키워드
    QA_KEYWORDS = [
        "qa", "quality assurance", "test", "testing", "automation",
        "unit test", "integration test", "e2e", "end-to-end",
        "performance", "load test", "stress test", "security test",
        "테스트", "품질", "자동화", "성능", "부하"
    ]
    
    # 고급 기술 키워드 (Learning 카테고리)
    ADVANCED_KEYWORDS = [
        "research", "paper", "breakthrough", "innovation", "architecture",
        "deep dive", "advanced", "enterprise", "scale", "distributed",
        "algorithm", "theory", "optimization", "framework design",
        "연구", "논문", "혁신", "아키텍처", "분산", "알고리즘"
    ]
    
    # 실무 중심 키워드 (QA Engineer 카테고리)
    PRACTICAL_QA_KEYWORDS = [
        "tutorial", "guide", "how to", "best practice", "tips",
        "practical", "hands-on", "tool", "workflow", "process",
        "playwright", "selenium", "cypress", "jenkins", "github actions",
        "가이드", "튜토리얼", "실무", "도구", "프로세스"
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
        
        # 5. 타겟 카테고리 결정 (Learning vs QA Engineer)
        metrics.target_category = self._determine_target_category(title, summary, metrics.categories)
        
        # 6. 우선순위 점수 계산
        metrics.priority_score = self._calculate_priority(metrics, title, summary)
        
        return metrics
    
    def _scrape_metrics(self, url: str) -> tuple[int, int]:
        """GeekNews 페이지에서 투표수와 댓글 수를 스크래핑한다.
        
        참고: GeekNews는 투표수를 정적 HTML에 포함하지 않아 스크래핑이 제한적입니다.
        댓글 수는 JSON-LD 형식으로 포함되어 있습니다.
        """
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode("utf-8", errors="ignore")
            
            votes = 0
            comments = 0
            
            # 댓글 수 추출 (JSON-LD에서)
            comment_match = re.search(r'"commentCount":\s*(\d+)', html)
            if comment_match:
                comments = int(comment_match.group(1))
            
            return votes, comments
            
        except Exception as exc:
            # 스크래핑 실패 시 조용히 0 반환
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
        
        # AI 카테고리
        if self._is_ai_related(title, summary):
            categories.append("AI")
        
        # QA/Testing 카테고리
        for keyword in self.QA_KEYWORDS:
            if keyword.lower() in text:
                categories.append("QA")
                break
        
        # 개발/프로그래밍
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
    
    def _determine_target_category(self, title: str, summary: str, categories: list[str]) -> str:
        """기사를 Learning 또는 QA Engineer 카테고리로 분류한다.
        
        분류 기준:
        - 고급 기술 (신기술, 연구, 아키텍처) → "learning"
        - 실무 중심 (QA 도구, 테스팅 기법, 실무 가이드) → "qa-engineer"
        - 기본값: 기술 관련은 "learning", QA 키워드 포함 시 "qa-engineer"
        
        Args:
            title: 기사 제목
            summary: 기사 요약
            categories: 기존에 분류된 카테고리 목록
        
        Returns:
            "learning" 또는 "qa-engineer"
        """
        text = f"{title} {summary}".lower()
        
        # 1. 실무 중심 QA 키워드가 많으면 QA Engineer
        practical_qa_count = sum(1 for keyword in self.PRACTICAL_QA_KEYWORDS if keyword.lower() in text)
        
        # 2. QA 카테고리가 있으면서 실무 키워드가 있으면 QA Engineer
        if "QA" in categories and practical_qa_count > 0:
            return "qa-engineer"
        
        # 3. QA 키워드가 강하게 나타나면 (2개 이상) QA Engineer
        qa_keyword_count = sum(1 for keyword in self.QA_KEYWORDS if keyword.lower() in text)
        if qa_keyword_count >= 2:
            return "qa-engineer"
        
        # 4. 고급 기술 키워드가 있으면 Learning
        advanced_count = sum(1 for keyword in self.ADVANCED_KEYWORDS if keyword.lower() in text)
        if advanced_count > 0:
            return "learning"
        
        # 5. AI 관련이면 Learning (기본적으로 고급 기술로 간주)
        if self._is_ai_related(title, summary):
            # 단, QA 테스팅 관련 AI이면 QA Engineer
            if qa_keyword_count > 0:
                return "qa-engineer"
            return "learning"
        
        # 6. 기본값: Learning
        return "learning"
    
    def _calculate_priority(
        self, 
        metrics: ContentMetrics, 
        title: str, 
        summary: str
    ) -> float:
        """우선순위 점수를 계산한다 (0-100)."""
        score = 0.0
        
        # 1. AI 관련성 (30점) - AI 콘텐츠 독점 방지
        if metrics.is_ai_related:
            score += 30
        
        # 2. 투표수 기반 인기도 (30점)
        if metrics.votes >= self.min_votes:
            # 투표수에 비례하여 점수 부여 (최대 30점)
            vote_score = min(30, (metrics.votes / 50) * 30)
            score += vote_score
        
        # 3. 댓글 수 (10점)
        if metrics.comments > 0:
            comment_score = min(10, (metrics.comments / 20) * 10)
            score += comment_score
        
        # 4. 트렌드 여부 (20점) - 트렌드 콘텐츠 비중 증가
        if metrics.is_trending:
            score += 20
        
        # 5. QA 관련성 (20점) - QA 콘텐츠 비중 증가
        if "QA" in metrics.categories:
            score += 20
        
        return min(100.0, score)
    
    def should_process(self, metrics: ContentMetrics) -> bool:
        """기사를 처리할지 여부를 결정한다."""
        # 우선순위 점수가 20점 미만이면 필터링 (키워드 기반 필터링)
        if metrics.priority_score < 20:
            return False
        
        # AI 관련 항목은 무조건 포함
        if metrics.is_ai_related:
            return True
        
        # 트렌드 항목 포함
        if metrics.is_trending:
            return True
        
        # QA 관련 항목 포함
        if "QA" in metrics.categories:
            return True
        
        # 인기도 기준 충족 (스크래핑 활성화 시만 의미있음)
        if metrics.votes >= self.min_votes:
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
    
    print("필터링 및 정렬 결과:")
    for item, metrics in results:
        print(f"  제목: {item['title']}")
        print(f"  우선순위: {metrics.priority_score:.1f}")
        print(f"  AI 관련: {metrics.is_ai_related}")
        print(f"  카테고리: {', '.join(metrics.categories)}")
        print()

