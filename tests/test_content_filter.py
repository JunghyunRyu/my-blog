"""콘텐츠 필터링 모듈 테스트."""
from __future__ import annotations

import pytest
from automation.content_filter import ContentFilter, ContentMetrics


class TestContentFilter:
    """ContentFilter 클래스 테스트."""
    
    def test_init(self):
        """초기화 테스트."""
        filter_obj = ContentFilter(min_votes=5, min_comments=2, enable_scraping=False)
        assert filter_obj.min_votes == 5
        assert filter_obj.min_comments == 2
        assert filter_obj.enable_scraping is False
    
    def test_is_ai_related(self):
        """AI 관련성 판단 테스트."""
        filter_obj = ContentFilter()
        
        # AI 관련 기사
        assert filter_obj._is_ai_related("OpenAI GPT-4 출시", "AI 모델 발표")
        assert filter_obj._is_ai_related("머신러닝 튜토리얼", "ML 기초")
        assert filter_obj._is_ai_related("테스트 자동화 도구", "Playwright 소개")
        
        # AI 관련 없는 기사
        assert not filter_obj._is_ai_related("일반 뉴스", "일반적인 내용")
        assert not filter_obj._is_ai_related("요리 레시피", "맛있는 음식")
    
    def test_is_trending(self):
        """트렌드 여부 판단 테스트."""
        filter_obj = ContentFilter()
        
        # 트렌딩 기술 관련
        assert filter_obj._is_trending("Kubernetes 가이드", "K8s 튜토리얼")
        assert filter_obj._is_trending("Docker 컨테이너", "컨테이너 기술")
        assert filter_obj._is_trending("React 18 신기능", "프론트엔드 프레임워크")
        
        # 트렌드 아닌 기사
        assert not filter_obj._is_trending("오래된 기술", "레거시 시스템")
    
    def test_categorize(self):
        """카테고리 분류 테스트."""
        filter_obj = ContentFilter()
        
        # AI 관련 카테고리
        categories = filter_obj._categorize("GPT-4 출시", "AI 모델")
        assert "ai" in categories or len(categories) > 0
        
        # QA 관련 카테고리
        categories = filter_obj._categorize("테스트 자동화", "QA 도구")
        assert "qa" in categories or len(categories) > 0
    
    def test_analyze(self, sample_feed_item):
        """분석 메서드 테스트."""
        filter_obj = ContentFilter(enable_scraping=False)
        
        # AI 관련 기사로 수정
        item = sample_feed_item.copy()
        item["title"] = "OpenAI GPT-4 출시"
        item["summary"] = "AI 모델 발표"
        
        metrics = filter_obj.analyze(item)
        
        assert isinstance(metrics, ContentMetrics)
        assert isinstance(metrics.is_ai_related, bool)
        assert isinstance(metrics.is_trending, bool)
        assert isinstance(metrics.priority_score, float)
        assert isinstance(metrics.categories, list)
    
    def test_calculate_priority(self):
        """우선순위 점수 계산 테스트."""
        filter_obj = ContentFilter()
        
        # AI 관련 기사는 높은 점수
        metrics_ai = ContentMetrics(
            votes=10,
            comments=5,
            is_ai_related=True,
            is_trending=True,
            categories=["ai", "qa"]
        )
        score_ai = filter_obj._calculate_priority(metrics_ai, "AI 기사", "AI 내용")
        
        # 일반 기사는 낮은 점수
        metrics_normal = ContentMetrics(
            votes=10,
            comments=5,
            is_ai_related=False,
            is_trending=False,
            categories=[]
        )
        score_normal = filter_obj._calculate_priority(metrics_normal, "일반 기사", "일반 내용")
        
        assert score_ai >= score_normal
    
    def test_filter_and_sort(self, sample_feed_item):
        """필터링 및 정렬 테스트."""
        filter_obj = ContentFilter(min_votes=0, enable_scraping=False)
        
        items = [
            sample_feed_item.copy(),
            {**sample_feed_item, "title": "AI 기사", "summary": "AI 내용", "guid": "guid-2"},
            {**sample_feed_item, "title": "일반 기사", "summary": "일반 내용", "guid": "guid-3"},
        ]
        
        results = filter_obj.filter_and_sort(items, max_items=10)
        
        assert isinstance(results, list)
        assert len(results) <= len(items)
        
        # 결과는 (item, metrics) 튜플 리스트
        for item, metrics in results:
            assert isinstance(metrics, ContentMetrics)
            assert "title" in item
    
    def test_filter_and_sort_max_items(self, sample_feed_item):
        """최대 항목 수 제한 테스트."""
        filter_obj = ContentFilter(min_votes=0, enable_scraping=False)
        
        items = [sample_feed_item.copy() for _ in range(10)]
        for i, item in enumerate(items):
            item["guid"] = f"guid-{i}"
        
        results = filter_obj.filter_and_sort(items, max_items=5)
        
        assert len(results) <= 5


class TestContentMetrics:
    """ContentMetrics 데이터클래스 테스트."""
    
    def test_default_values(self):
        """기본값 테스트."""
        metrics = ContentMetrics()
        
        assert metrics.votes == 0
        assert metrics.comments == 0
        assert metrics.is_ai_related is False
        assert metrics.is_trending is False
        assert metrics.priority_score == 0.0
        assert metrics.categories == []
    
    def test_custom_values(self):
        """사용자 정의 값 테스트."""
        metrics = ContentMetrics(
            votes=100,
            comments=50,
            is_ai_related=True,
            is_trending=True,
            priority_score=85.5,
            categories=["ai", "qa"]
        )
        
        assert metrics.votes == 100
        assert metrics.comments == 50
        assert metrics.is_ai_related is True
        assert metrics.is_trending is True
        assert metrics.priority_score == 85.5
        assert metrics.categories == ["ai", "qa"]

