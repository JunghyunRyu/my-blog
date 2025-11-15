"""QA 생성기 모듈 테스트."""
from __future__ import annotations

import json
from unittest.mock import Mock, patch, MagicMock

import pytest

from automation.qa_generator import (
    QAContentGenerator,
    QAResult,
    RuleBasedProvider,
    OpenAIProvider
)


class TestRuleBasedProvider:
    """RuleBasedProvider 테스트."""
    
    def test_generate(self, sample_feed_item):
        """규칙 기반 생성 테스트."""
        provider = RuleBasedProvider()
        result = provider.generate(sample_feed_item)
        
        assert isinstance(result, QAResult)
        assert result.summary
        assert len(result.qa_pairs) == 3
        assert len(result.follow_ups) > 0
        assert len(result.resources) > 0
    
    def test_build_summary(self):
        """요약 생성 테스트."""
        provider = RuleBasedProvider()
        
        summary = provider._build_summary("테스트 제목", "테스트 요약")
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_build_qa_pairs(self):
        """Q&A 쌍 생성 테스트."""
        provider = RuleBasedProvider()
        
        qa_pairs = provider._build_qa_pairs("테스트 제목", "테스트 요약")
        assert len(qa_pairs) == 3
        for pair in qa_pairs:
            assert "question" in pair
            assert "answer" in pair
            assert pair["question"]
            assert pair["answer"]
    
    def test_build_follow_ups(self):
        """Follow-up 생성 테스트."""
        provider = RuleBasedProvider()
        
        follow_ups = provider._build_follow_ups("테스트 제목")
        assert isinstance(follow_ups, list)
        assert len(follow_ups) > 0


class TestQAContentGenerator:
    """QAContentGenerator 테스트."""
    
    def test_init_without_provider(self, monkeypatch: pytest.MonkeyPatch):
        """프로바이더 없이 초기화 테스트."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        generator = QAContentGenerator(enable_mcp=False)
        
        assert generator._provider is not None
        assert isinstance(generator._provider, RuleBasedProvider)
    
    def test_init_with_openai_key(self, monkeypatch: pytest.MonkeyPatch):
        """OpenAI API 키로 초기화 테스트."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
        
        generator = QAContentGenerator(enable_mcp=False)
        
        assert generator._provider is not None
        assert isinstance(generator._provider, OpenAIProvider)
    
    def test_generate_with_rule_based(self, sample_feed_item):
        """규칙 기반 생성 테스트."""
        provider = RuleBasedProvider()
        generator = QAContentGenerator(provider=provider, enable_mcp=False)
        
        result = generator.generate(sample_feed_item)
        
        assert isinstance(result, QAResult)
        assert result.summary
        assert len(result.qa_pairs) > 0
    
    @patch('automation.qa_generator.urllib.request.urlopen')
    def test_generate_with_openai_mock(self, mock_urlopen, sample_feed_item, monkeypatch: pytest.MonkeyPatch):
        """OpenAI API 모킹 테스트."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # 모의 응답 생성
        mock_response = MagicMock()
        mock_response.read.return_value.decode.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "summary": "테스트 요약",
                        "qa_pairs": [
                            {"question": "Q1", "answer": "A1"}
                        ],
                        "follow_ups": ["Follow-up 1"],
                        "resources": [],
                        "qa_engineer_insights": [],
                        "practical_guide": [],
                        "learning_roadmap": [],
                        "expert_opinions": [],
                        "technical_level": "advanced",
                        "blog_category": "Learning"
                    })
                }
            }]
        }).encode('utf-8')
        
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        generator = QAContentGenerator(enable_mcp=False)
        result = generator.generate(sample_feed_item)
        
        assert isinstance(result, QAResult)
        assert result.summary == "테스트 요약"
    
    def test_generate_with_exception_fallback(self, sample_feed_item):
        """예외 발생 시 규칙 기반 백업 테스트."""
        # 예외를 발생시키는 모의 프로바이더
        mock_provider = Mock()
        mock_provider.generate.side_effect = Exception("Test error")
        
        generator = QAContentGenerator(provider=mock_provider, enable_mcp=False)
        result = generator.generate(sample_feed_item)
        
        # 백업 규칙 기반 프로바이더가 사용되어야 함
        assert isinstance(result, QAResult)
        assert result.summary


class TestQAResult:
    """QAResult 데이터클래스 테스트."""
    
    def test_default_values(self):
        """기본값 테스트."""
        result = QAResult()
        
        assert result.summary == ""
        assert result.qa_pairs == []
        assert result.follow_ups == []
        assert result.resources == []
        assert result.qa_engineer_insights == []
        assert result.practical_guide == []
        assert result.learning_roadmap == []
        assert result.expert_opinions == []
        assert result.technical_level == "advanced"
        assert result.blog_category == "Learning"
    
    def test_custom_values(self):
        """사용자 정의 값 테스트."""
        result = QAResult(
            summary="테스트 요약",
            qa_pairs=[{"question": "Q1", "answer": "A1"}],
            follow_ups=["Follow-up 1"],
            technical_level="practical",
            blog_category="QA Engineer"
        )
        
        assert result.summary == "테스트 요약"
        assert len(result.qa_pairs) == 1
        assert len(result.follow_ups) == 1
        assert result.technical_level == "practical"
        assert result.blog_category == "QA Engineer"

