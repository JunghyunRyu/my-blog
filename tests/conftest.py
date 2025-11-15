"""pytest 설정 및 공통 픽스처."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator

import pytest

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def project_root_path() -> Path:
    """프로젝트 루트 경로를 반환합니다."""
    return project_root


@pytest.fixture
def test_data_dir(project_root_path: Path) -> Path:
    """테스트 데이터 디렉토리 경로를 반환합니다."""
    return project_root_path / "tests" / "data"


@pytest.fixture
def temp_env(monkeypatch: pytest.MonkeyPatch) -> Generator[dict[str, str], None, None]:
    """임시 환경 변수를 설정하고 테스트 후 복원합니다."""
    original_env = os.environ.copy()
    
    # 테스트용 기본 환경 변수 설정
    test_env = {
        "OPENAI_API_KEY": "test-api-key",
        "OPENAI_MODEL": "gpt-4o-mini",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "text",
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    yield test_env
    
    # 원래 환경 변수 복원
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_feed_item() -> dict:
    """샘플 RSS 피드 아이템을 반환합니다."""
    return {
        "guid": "test-guid-123",
        "title": "Test Article Title",
        "link": "https://example.com/article",
        "summary": "This is a test article summary.",
        "published_at": "2025-01-01T00:00:00Z"
    }

