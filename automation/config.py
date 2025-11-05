"""중앙 집중식 설정 관리 모듈.

모든 환경 변수와 기본 설정을 관리합니다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """애플리케이션 설정 클래스."""
    
    # ========================================
    # 프로젝트 경로
    # ========================================
    PROJECT_ROOT = Path(__file__).parent.parent.absolute()
    POSTS_DIR = PROJECT_ROOT / "_posts"
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # ========================================
    # OpenAI API 설정
    # ========================================
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # ========================================
    # GeekNews 설정
    # ========================================
    GEEKNEWS_FEED_URL: str = os.getenv(
        "GEEKNEWS_FEED_URL", 
        "https://feeds.feedburner.com/geeknews-feed"
    )
    
    # ========================================
    # 콘텐츠 필터링 설정
    # ========================================
    MIN_VOTE_COUNT: int = int(os.getenv("MIN_VOTE_COUNT", "10"))
    MAX_POSTS_PER_RUN: int = int(os.getenv("MAX_POSTS_PER_RUN", "10"))
    ENABLE_WEB_RESEARCH: bool = os.getenv("ENABLE_WEB_RESEARCH", "true").lower() == "true"
    ENABLE_SCRAPING: bool = os.getenv("ENABLE_SCRAPING", "false").lower() == "true"
    
    # ========================================
    # 스케줄러 설정
    # ========================================
    PIPELINE_INTERVAL_SECONDS: int = int(os.getenv("PIPELINE_INTERVAL_SECONDS", "3600"))
    PIPELINE_MAX_POSTS: int = int(os.getenv("PIPELINE_MAX_POSTS", "10"))
    PIPELINE_TIMEZONE: str = os.getenv("PIPELINE_TIMEZONE", "Asia/Seoul")
    
    # ========================================
    # 로깅 설정
    # ========================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # "json" 또는 "text"
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # ========================================
    # YouTube 수집 설정
    # ========================================
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    YOUTUBE_KEYWORDS: str = os.getenv("YOUTUBE_KEYWORDS", "QA, software testing, test automation, DevOps")
    YOUTUBE_MAX_RESULTS: int = int(os.getenv("YOUTUBE_MAX_RESULTS", "10"))
    YOUTUBE_REGION_CODE: str = os.getenv("YOUTUBE_REGION_CODE", "KR")
    YOUTUBE_PUBLISHED_AFTER_DAYS: int = int(os.getenv("YOUTUBE_PUBLISHED_AFTER_DAYS", "7"))
    YOUTUBE_CHANNELS_ENABLED: bool = os.getenv("YOUTUBE_CHANNELS_ENABLED", "true").lower() == "true"
    YOUTUBE_CHANNELS_FILE: Path = DATA_DIR / "youtube_channels.json"
    YOUTUBE_WATCHLIST_ENABLED: bool = os.getenv("YOUTUBE_WATCHLIST_ENABLED", "true").lower() == "true"
    YOUTUBE_WATCHLIST_FILE: Path = DATA_DIR / "youtube_watchlist.json"

    # ========================================
    # Gmail 뉴스레터 인입 설정
    # ========================================
    GOOGLE_CLIENT_SECRET_FILE: str = os.getenv("GOOGLE_CLIENT_SECRET_FILE", str((Path(__file__).parent.parent / "data" / "google_client_secret.json").absolute()))
    GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", str((Path(__file__).parent.parent / "data" / "google_token.json").absolute()))
    GMAIL_LABEL: str = os.getenv("GMAIL_LABEL", "newsletter")

    # ========================================
    # 미디어 생성 설정
    # ========================================
    GENERATE_CHARTS: bool = os.getenv("GENERATE_CHARTS", "true").lower() == "true"
    GENERATE_DIAGRAMS: bool = os.getenv("GENERATE_DIAGRAMS", "true").lower() == "true"
    GENERATE_VIDEO: bool = os.getenv("GENERATE_VIDEO", "false").lower() == "true"

    # 출력 에셋 경로
    ASSETS_IMG_AUTO_DIR: Path = (Path(__file__).parent.parent / "assets" / "img" / "auto").absolute()

    # ========================================
    # EC2 환경 감지
    # ========================================
    IS_EC2: bool = os.path.exists("/sys/hypervisor/uuid")
    
    # ========================================
    # 상태 파일
    # ========================================
    STATE_FILE: Path = DATA_DIR / "geeknews_state.json"
    
    @classmethod
    def load_channels(cls) -> list[dict]:
        """YouTube 채널 설정을 로드합니다.
        
        Returns:
            채널 정보 딕셔너리 리스트. 파일이 없거나 오류 시 빈 리스트 반환.
        """
        import json
        
        if not cls.YOUTUBE_CHANNELS_FILE.exists():
            return []
        
        try:
            with open(cls.YOUTUBE_CHANNELS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                channels = data.get("channels", [])
                # enabled=true인 채널만 반환
                return [ch for ch in channels if ch.get("enabled", False)]
        except Exception as e:
            print(f"⚠️ 채널 설정 로드 실패: {e}", file=sys.stderr)
            return []
    
    @classmethod
    def load_watchlist(cls) -> list[dict]:
        """YouTube 워치리스트를 로드합니다.
        
        Returns:
            워치리스트 비디오 정보 딕셔너리 리스트. 파일이 없거나 오류 시 빈 리스트 반환.
        """
        import json
        
        if not cls.YOUTUBE_WATCHLIST_FILE.exists():
            return []
        
        try:
            with open(cls.YOUTUBE_WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                watchlist = data.get("watchlist", [])
                # enabled=true인 비디오만 반환
                return [vid for vid in watchlist if vid.get("enabled", False)]
        except Exception as e:
            print(f"⚠️ 워치리스트 로드 실패: {e}", file=sys.stderr)
            return []
    
    @classmethod
    def validate(cls) -> list[str]:
        """설정 유효성을 검사하고 오류 목록을 반환합니다.
        
        Returns:
            오류 메시지 리스트. 비어있으면 모든 설정이 유효합니다.
        """
        errors: list[str] = []
        
        # 필수 설정 확인
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        # OpenAI API 키 형식 검증 (간단한 검사)
        if cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith("sk-"):
            errors.append("OPENAI_API_KEY 형식이 올바르지 않습니다 (sk-로 시작해야 함).")
        
        # 디렉토리 존재 확인 및 생성
        for dir_path in [cls.POSTS_DIR, cls.DATA_DIR, cls.LOGS_DIR]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"디렉토리 생성 실패 ({dir_path}): {e}")
        
        # 숫자 범위 검증
        if cls.MIN_VOTE_COUNT < 0:
            errors.append("MIN_VOTE_COUNT는 0 이상이어야 합니다.")
        
        if cls.MAX_POSTS_PER_RUN < 1:
            errors.append("MAX_POSTS_PER_RUN은 1 이상이어야 합니다.")
        
        if cls.PIPELINE_INTERVAL_SECONDS < 60:
            errors.append("PIPELINE_INTERVAL_SECONDS는 60초 이상이어야 합니다.")

        # YouTube 키 검증 (옵션)
        if cls.YOUTUBE_API_KEY is not None and not cls.YOUTUBE_API_KEY:
            errors.append("YOUTUBE_API_KEY가 비어 있습니다.")

        # Gmail 토큰/시크릿 파일 경로 안내 (선택, 존재하지 않아도 동작은 가능)
        # 실제 최초 OAuth 동의 시 토큰 파일이 생성됩니다.
        
        return errors
    
    @classmethod
    def print_config(cls) -> None:
        """현재 설정을 출력합니다."""
        print("\n" + "=" * 80)
        print("GeekNews 자동화 설정")
        print("=" * 80)
        print(f"\n[프로젝트]")
        print(f"  프로젝트 루트: {cls.PROJECT_ROOT}")
        print(f"  포스트 디렉토리: {cls.POSTS_DIR}")
        print(f"  데이터 디렉토리: {cls.DATA_DIR}")
        print(f"  로그 디렉토리: {cls.LOGS_DIR}")
        
        print(f"\n[OpenAI]")
        print(f"  API 키: {'설정됨' if cls.OPENAI_API_KEY else '미설정'}")
        print(f"  모델: {cls.OPENAI_MODEL}")
        
        print(f"\n[GeekNews]")
        print(f"  RSS 피드: {cls.GEEKNEWS_FEED_URL}")
        
        print(f"\n[필터링]")
        print(f"  최소 투표수: {cls.MIN_VOTE_COUNT}")
        print(f"  최대 포스트 수: {cls.MAX_POSTS_PER_RUN}")
        print(f"  웹 연구: {'활성화' if cls.ENABLE_WEB_RESEARCH else '비활성화'}")
        print(f"  스크래핑: {'활성화' if cls.ENABLE_SCRAPING else '비활성화'}")
        
        print(f"\n[스케줄러]")
        print(f"  실행 주기: {cls.PIPELINE_INTERVAL_SECONDS}초 ({cls.PIPELINE_INTERVAL_SECONDS // 60}분)")
        print(f"  최대 포스트: {cls.PIPELINE_MAX_POSTS}")
        print(f"  시간대: {cls.PIPELINE_TIMEZONE}")
        
        print(f"\n[로깅]")
        print(f"  로그 레벨: {cls.LOG_LEVEL}")
        print(f"  로그 형식: {cls.LOG_FORMAT}")
        
        print(f"\n[환경]")
        print(f"  EC2: {'예' if cls.IS_EC2 else '아니오'}")

        print(f"\n[YouTube]")
        print(f"  API 키: {'설정됨' if cls.YOUTUBE_API_KEY else '미설정'}")
        print(f"  키워드: {cls.YOUTUBE_KEYWORDS}")
        print(f"  최대 결과: {cls.YOUTUBE_MAX_RESULTS}")
        print(f"  지역 코드: {cls.YOUTUBE_REGION_CODE}")
        print(f"  최근 일수: {cls.YOUTUBE_PUBLISHED_AFTER_DAYS}")
        print(f"  채널 수집: {'활성화' if cls.YOUTUBE_CHANNELS_ENABLED else '비활성화'}")
        if cls.YOUTUBE_CHANNELS_ENABLED:
            channels = cls.load_channels()
            print(f"  활성 채널 수: {len(channels)}")
        print(f"  워치리스트: {'활성화' if cls.YOUTUBE_WATCHLIST_ENABLED else '비활성화'}")
        if cls.YOUTUBE_WATCHLIST_ENABLED:
            watchlist = cls.load_watchlist()
            print(f"  워치리스트 비디오 수: {len(watchlist)}")

        print(f"\n[Gmail]")
        print(f"  라벨: {cls.GMAIL_LABEL}")
        print(f"  Client Secret: {cls.GOOGLE_CLIENT_SECRET_FILE}")
        print(f"  Token: {cls.GOOGLE_TOKEN_FILE}")

        print(f"\n[미디어]")
        print(f"  차트 생성: {'예' if cls.GENERATE_CHARTS else '아니오'}")
        print(f"  다이어그램 생성: {'예' if cls.GENERATE_DIAGRAMS else '아니오'}")
        print(f"  영상 생성: {'예' if cls.GENERATE_VIDEO else '아니오'}")
        print(f"  에셋 디렉토리: {cls.ASSETS_IMG_AUTO_DIR}")
        
        print("=" * 80 + "\n")
    
    @classmethod
    def ensure_directories(cls) -> None:
        """필요한 디렉토리들을 생성합니다."""
        for dir_path in [cls.POSTS_DIR, cls.DATA_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 카테고리별 포스트 디렉토리도 생성
        (cls.POSTS_DIR / "learning").mkdir(parents=True, exist_ok=True)
        (cls.POSTS_DIR / "qa-engineer").mkdir(parents=True, exist_ok=True)
        (cls.POSTS_DIR / "daily-life").mkdir(parents=True, exist_ok=True)


# 설정 유효성 검사 (import 시 자동 실행)
def _check_config():
    """설정 유효성을 확인하고 오류가 있으면 경고를 출력합니다."""
    errors = Config.validate()
    if errors:
        print("\n⚠️  설정 오류가 발견되었습니다:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        print("\n계속 진행하려면 설정을 수정하세요.\n", file=sys.stderr)


# 디렉토리 자동 생성
Config.ensure_directories()
try:
    Config.ASSETS_IMG_AUTO_DIR.mkdir(parents=True, exist_ok=True)
except Exception as _e:  # 경로 생성 실패는 치명적이지 않음
    pass

