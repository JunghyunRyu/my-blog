"""개선된 필터링 테스트."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("개선된 필터링으로 실제 파이프라인 테스트")
print("=" * 80)

try:
    from automation import geeknews_pipeline
    
    # 최대 5개 포스트 생성 테스트
    print("\n[테스트] GeekNews 파이프라인 실행 (최대 5개 포스트)")
    print("-" * 80)
    
    result = geeknews_pipeline.run_pipeline(
        max_posts=5,
        feed_url="https://feeds.feedburner.com/geeknews-feed",
        timezone=None,
        enable_web_research=False,  # 속도 향상을 위해 비활성화
        enable_scraping=False,
        min_votes=10  # 기본값 유지
    )
    
    if result:
        print(f"\n✅ 성공: {len(result)}개 블로그 포스트 생성 완료!")
        for post in result:
            print(f"  - {post}")
    else:
        print("\n⚠️ 생성된 포스트가 없습니다.")
        print("  (이미 처리된 항목이거나 필터링 기준을 충족하지 않았을 수 있습니다)")
        
except Exception as e:
    print(f"\n❌ 파이프라인 실행 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)

