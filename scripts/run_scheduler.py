#!/usr/bin/env python3
"""GeekNews 파이프라인을 주기적으로 실행하는 스케줄러.

EC2 systemd 서비스나 장기 실행에 사용됩니다.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import timezone
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from geeknews.config import Config
from geeknews.pipeline import run_pipeline, resolve_timezone


def main() -> None:
    """스케줄러를 실행합니다."""
    print("=" * 80)
    print("GeekNews 자동화 스케줄러 시작")
    print("=" * 80)
    
    # 설정 검증
    errors = Config.validate()
    if errors:
        print("\n❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # 설정 출력
    Config.print_config()
    
    # 스케줄러 설정
    interval = Config.PIPELINE_INTERVAL_SECONDS
    max_posts = Config.PIPELINE_MAX_POSTS
    feed_url = Config.GEEKNEWS_FEED_URL
    tz_name = Config.PIPELINE_TIMEZONE
    tz = resolve_timezone(tz_name) or timezone.utc
    
    enable_web_research = Config.ENABLE_WEB_RESEARCH
    enable_scraping = Config.ENABLE_SCRAPING
    min_votes = Config.MIN_VOTE_COUNT
    
    print(f"\n⏰ 스케줄러 설정:")
    print(f"  - 실행 주기: {interval}초 ({interval // 60}분)")
    print(f"  - 최대 포스트: {max_posts}개")
    print(f"  - 시간대: {tz_name}")
    print(f"  - 웹 연구: {'활성화' if enable_web_research else '비활성화'}")
    print(f"  - 스크래핑: {'활성화' if enable_scraping else '비활성화'}")
    print("\n▶️  스케줄러를 시작합니다. Ctrl+C로 중단할 수 있습니다.\n")
    
    run_count = 0
    
    try:
        while True:
            run_count += 1
            
            print("\n" + "=" * 80)
            print(f"실행 #{run_count}")
            print("=" * 80)
            
            try:
                result = run_pipeline(
                    max_posts=max_posts,
                    feed_url=feed_url,
                    timezone=tz,
                    enable_web_research=enable_web_research,
                    enable_scraping=enable_scraping,
                    min_votes=min_votes
                )
                print(f"\n✅ 실행 #{run_count} 완료: {len(result)}개 포스트 생성")
            except Exception as exc:
                print(f"\n❌ 실행 #{run_count} 실패: {exc}")
                import traceback
                traceback.print_exc()
            
            print(f"\n⏸️  다음 실행까지 {interval}초 대기 중...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  스케줄러가 중단되었습니다.")
        print(f"총 {run_count}회 실행됨")
        sys.exit(0)


if __name__ == "__main__":
    main()


