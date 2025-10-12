"""GeekNews QA 자동화 파이프라인을 주기적으로 실행하는 스케줄러."""
from __future__ import annotations

import os
import time
from datetime import timezone

from automation.geeknews_pipeline import (
    DEFAULT_FEED_URL,
    run_pipeline,
    resolve_timezone,
)


DEFAULT_INTERVAL_SECONDS = 60 * 60  # 1시간
DEFAULT_MAX_POSTS = 3
DEFAULT_TIMEZONE = "Asia/Seoul"


def main() -> None:
    interval = int(os.getenv("PIPELINE_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS))
    max_posts = int(os.getenv("PIPELINE_MAX_POSTS", DEFAULT_MAX_POSTS))
    feed_url = os.getenv("GEEKNEWS_FEED_URL", DEFAULT_FEED_URL)
    tz_name = os.getenv("PIPELINE_TIMEZONE", DEFAULT_TIMEZONE)
    tz = resolve_timezone(tz_name) or timezone.utc
    
    # 새로운 설정 추가
    enable_web_research = os.getenv("ENABLE_WEB_RESEARCH", "true").lower() == "true"
    enable_scraping = os.getenv("ENABLE_SCRAPING", "false").lower() == "true"
    min_votes = int(os.getenv("MIN_VOTE_COUNT", 10))

    while True:
        print("\n" + "=" * 80)
        print("GeekNews QA 전문가급 자동화 스케줄러")
        print("=" * 80)
        
        result = run_pipeline(
            max_posts=max_posts,
            feed_url=feed_url,
            timezone=tz,
            enable_web_research=enable_web_research,
            enable_scraping=enable_scraping,
            min_votes=min_votes
        )
        
        print(f"\n다음 실행까지 {interval}초 대기 중...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
