"""enhanced_sources 모듈 테스트."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import os

from automation.enhanced_sources import (
    RedditCollector,
    DevToCollector,
    StackOverflowCollector,
    ContentAggregator,
    EnhancedContent
)


class TestRedditCollector:
    """RedditCollector 테스트."""
    
    @pytest.mark.asyncio
    async def test_get_access_token(self):
        """액세스 토큰 획득 테스트."""
        collector = RedditCollector("test_client_id", "test_client_secret")
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={
                "access_token": "test_token",
                "expires_in": 3600
            })
            
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            
            token = await collector._get_access_token()
            assert token == "test_token"
            assert collector._access_token == "test_token"
    
    @pytest.mark.asyncio
    async def test_parse_reddit_post(self):
        """Reddit 포스트 파싱 테스트."""
        collector = RedditCollector("test_id", "test_secret")
        
        post_data = {
            "title": "Test Post",
            "selftext": "Test content",
            "url": "https://example.com",
            "created_utc": 1609459200,  # 2021-01-01
            "ups": 100,
            "num_comments": 20,
            "subreddit": "softwaretesting",
            "author": "testuser",
            "score": 100,
            "upvote_ratio": 0.95,
            "permalink": "/r/softwaretesting/test"
        }
        
        content = collector._parse_reddit_post(post_data)
        
        assert content is not None
        assert content.title == "Test Post"
        assert content.source == "reddit"
        assert content.engagement["likes"] == 100
        assert content.engagement["comments"] == 20
        assert "softwaretesting" in content.tags


class TestDevToCollector:
    """DevToCollector 테스트."""
    
    def test_parse_article(self):
        """Dev.to 아티클 파싱 테스트."""
        collector = DevToCollector()
        
        article = {
            "title": "Test Article",
            "description": "Test description",
            "url": "https://dev.to/test",
            "published_at": "2024-01-01T00:00:00Z",
            "positive_reactions_count": 50,
            "comments_count": 10,
            "tag_list": "testing,qa,automation",
            "id": 12345,
            "reading_time_minutes": 5,
            "user": {"username": "testuser"},
            "organization": None
        }
        
        content = collector._parse_article(article)
        
        assert content is not None
        assert content.title == "Test Article"
        assert content.source == "devto"
        assert content.engagement["likes"] == 50
        assert content.engagement["comments"] == 10
        assert "testing" in content.tags


class TestStackOverflowCollector:
    """StackOverflowCollector 테스트."""
    
    def test_parse_question(self):
        """Stack Overflow 질문 파싱 테스트."""
        collector = StackOverflowCollector()
        
        question = {
            "title": "How to test with Playwright?",
            "body": "<p>Test question body</p>",
            "link": "https://stackoverflow.com/q/12345",
            "creation_date": 1609459200,
            "score": 50,
            "comment_count": 5,
            "tags": ["playwright", "testing"],
            "question_id": 12345,
            "view_count": 1000,
            "answer_count": 3,
            "is_answered": True,
            "owner": {"display_name": "testuser"}
        }
        
        content = collector._parse_question(question)
        
        assert content is not None
        assert content.title == "How to test with Playwright?"
        assert content.source == "stackoverflow"
        assert content.engagement["likes"] == 50
        assert "playwright" in content.tags
        assert "Test question body" in content.content  # HTML 태그 제거됨


class TestContentAggregator:
    """ContentAggregator 테스트."""
    
    def test_is_collector_configured(self):
        """수집기 설정 확인 테스트."""
        aggregator = ContentAggregator()
        
        with patch.dict(os.environ, {
            "REDDIT_CLIENT_ID": "test_id",
            "REDDIT_CLIENT_SECRET": "test_secret"
        }):
            assert aggregator._is_collector_configured("reddit") is True
        
        with patch.dict(os.environ, {}, clear=True):
            assert aggregator._is_collector_configured("reddit") is False
            assert aggregator._is_collector_configured("devto") is True  # API 키 불필요
    
    def test_calculate_quality_score(self):
        """품질 점수 계산 테스트."""
        aggregator = ContentAggregator()
        
        # 고품질 콘텐츠
        high_quality = EnhancedContent(
            source="test",
            title="Test QA Automation",
            url="https://example.com",
            content=" ".join(["word"] * 1000),  # 1000단어
            author="test",
            engagement={"likes": 150, "comments": 30, "shares": 0},
            tags=["qa", "automation"],
            published_at=datetime.now(),
            metadata={}
        )
        
        score = aggregator._calculate_quality_score(high_quality)
        assert score >= 70
        
        # 저품질 콘텐츠
        low_quality = EnhancedContent(
            source="test",
            title="Test",
            url="https://example.com",
            content="short",
            author="test",
            engagement={"likes": 5, "comments": 1, "shares": 0},
            tags=[],
            published_at=datetime.now() - timedelta(days=60),
            metadata={}
        )
        
        score = aggregator._calculate_quality_score(low_quality)
        assert score < 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
