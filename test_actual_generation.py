"""실제 블로그 포스트 생성 테스트."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("실제 블로그 포스트 생성 테스트")
print("=" * 60)

# 기존 파이프라인 실행 (1개 포스트만)
print("\n[테스트] GeekNews 파이프라인 실행 (최대 1개 포스트)")
print("-" * 60)

try:
    # automation.geeknews_pipeline 모듈 직접 실행
    from automation import geeknews_pipeline
    
    # 간단한 테스트: 최대 1개 포스트만 생성
    import argparse
    
    # 인자 설정
    test_args = argparse.Namespace(
        max_posts=1,
        feed_url="https://feeds.feedburner.com/geeknews-feed",
        timezone=None,
        no_web_research=False,
        enable_scraping=False,
        min_votes=10
    )
    
    # 파이프라인 실행
    result = geeknews_pipeline.run_pipeline(
        max_posts=test_args.max_posts,
        feed_url=test_args.feed_url,
        timezone=None,
        enable_web_research=not test_args.no_web_research,
        enable_scraping=test_args.enable_scraping,
        min_votes=test_args.min_votes
    )
    
    if result:
        print(f"\n[성공] {len(result)}개 블로그 포스트 생성 완료!")
        for post in result:
            print(f"  - {post}")
    else:
        print("\n[알림] 생성된 포스트가 없습니다.")
        print("  (이미 처리된 항목이거나 필터링 기준을 충족하지 않았을 수 있습니다)")
        
except Exception as e:
    print(f"\n[오류] 파이프라인 실행 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)
