"""QA 자동화 관련 필터링 테스트."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("QA 자동화 관련 필터링 테스트")
print("=" * 80)

try:
    from automation.content_filter import ContentFilter, ContentMetrics
    
    # 테스트용 샘플 항목들
    test_items = [
        {
            "title": "AI 기반 테스트 자동화 도구 출시",
            "summary": "AI를 활용한 테스트 케이스 자동 생성 도구가 발표되었습니다.",
            "link": "https://example.com/ai-test-automation"
        },
        {
            "title": "Selenium으로 E2E 테스트 자동화",
            "summary": "Selenium WebDriver를 사용하여 End-to-End 테스트를 자동화하는 방법을 소개합니다.",
            "link": "https://example.com/selenium-automation"
        },
        {
            "title": "Playwright로 QA 프로세스 자동화",
            "summary": "Playwright 프레임워크를 사용하여 QA 워크플로우를 자동화하는 사례를 공유합니다.",
            "link": "https://example.com/playwright-qa"
        },
        {
            "title": "CI/CD 파이프라인에 테스트 자동화 통합",
            "summary": "Jenkins와 GitHub Actions에 자동화된 테스트를 통합하는 방법입니다.",
            "link": "https://example.com/cicd-testing"
        },
        {
            "title": "일반 기술 뉴스",
            "summary": "일반적인 기술 뉴스 기사입니다.",
            "link": "https://example.com/general-tech"
        }
    ]
    
    print("\n[테스트] ContentFilter로 QA 자동화 관련 항목 필터링")
    print("-" * 80)
    
    filter_engine = ContentFilter(min_votes=10, enable_scraping=False)
    
    print("\n항목별 분석 결과:")
    print("=" * 80)
    
    processed_count = 0
    for i, item in enumerate(test_items, 1):
        metrics = filter_engine.analyze(item)
        should_process = filter_engine.should_process(metrics)
        
        status = "[OK] 처리됨" if should_process else "[SKIP] 필터링됨"
        if should_process:
            processed_count += 1
        
        print(f"\n{i}. {item['title']}")
        print(f"   상태: {status}")
        print(f"   AI 관련: {metrics.is_ai_related}")
        print(f"   카테고리: {', '.join(metrics.categories)}")
        print(f"   우선순위 점수: {metrics.priority_score:.1f}/100")
        print(f"   투표수: {metrics.votes}")
    
    print("\n" + "=" * 80)
    print("필터링 결과 요약")
    print("=" * 80)
    print(f"총 항목: {len(test_items)}개")
    print(f"[OK] 처리 가능: {processed_count}개")
    print(f"[SKIP] 필터링됨: {len(test_items) - processed_count}개")
    
    # 실제 필터링 실행
    print("\n" + "=" * 80)
    print("실제 필터링 실행 결과")
    print("=" * 80)
    
    filtered_items = filter_engine.filter_and_sort(test_items, max_items=10)
    print(f"[OK] 최종 선별된 항목: {len(filtered_items)}개")
    
    if filtered_items:
        print("\n선별된 항목 목록:")
        for i, (item, metrics) in enumerate(filtered_items, 1):
            print(f"  {i}. {item['title']}")
            print(f"     우선순위: {metrics.priority_score:.1f}, AI: {metrics.is_ai_related}, QA: {'QA' in metrics.categories}")
    else:
        print("[WARN] 필터링 후 선별된 항목이 없습니다.")
        
except Exception as e:
    print(f"[FAIL] 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)

