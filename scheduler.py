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

    while True:
        print("GeekNews 파이프라인 실행 시작")
        result = run_pipeline(max_posts, feed_url, tz)
        if result:
            print("생성된 포스트:")
            for path in result:
                print(f"- {path}")
        else:
            print("새롭게 생성된 포스트가 없습니다.")

        print(f"{interval}초 대기 후 다음 실행")
        time.sleep(interval)


if __name__ == "__main__":
    main()
