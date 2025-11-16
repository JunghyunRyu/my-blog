"""데이터 수집 및 필터링 진단 스크립트."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("데이터 수집 및 필터링 진단")
print("=" * 80)

# 1단계: RSS 피드 수집 확인
print("\n[1단계] RSS 피드 수집 확인")
print("-" * 80)

try:
    from automation.geeknews_pipeline import fetch_feed, DEFAULT_FEED_URL
    
    feed_url = DEFAULT_FEED_URL
    print(f"피드 URL: {feed_url}")
    
    rss_items = fetch_feed(feed_url)
    print(f"✅ RSS 피드에서 {len(rss_items)}개 항목 수집")
    
    if rss_items:
        print("\n수집된 항목 샘플 (최대 5개):")
        for i, item in enumerate(rss_items[:5], 1):
            print(f"  {i}. {item.get('title', 'N/A')[:60]}...")
            print(f"     GUID: {item.get('guid', 'N/A')[:60]}...")
            print(f"     투표수: {item.get('votes', 0)}")
            print(f"     댓글수: {item.get('comments', 0)}")
    else:
        print("⚠️ RSS 피드에서 항목을 수집하지 못했습니다.")
        
except Exception as e:
    print(f"❌ RSS 피드 수집 실패: {e}")
    import traceback
    traceback.print_exc()
    rss_items = []

# 2단계: 중복 필터링 확인
print("\n[2단계] 중복 필터링 확인")
print("-" * 80)

try:
    from automation.geeknews_pipeline import load_state, select_new_items
    
    processed = load_state()
    print(f"이미 처리된 항목: {len(processed)}개")
    
    if processed:
        print("\n처리된 항목 샘플 (최대 5개):")
        for i, guid in enumerate(sorted(processed)[:5], 1):
            print(f"  {i}. {guid[:70]}...")
    
    new_items = select_new_items(rss_items, processed)
    print(f"\n✅ 신규 항목: {len(new_items)}개 발견")
    
    if new_items:
        print("\n신규 항목 샘플 (최대 5개):")
        for i, item in enumerate(new_items[:5], 1):
            print(f"  {i}. {item.get('title', 'N/A')[:60]}...")
            print(f"     투표수: {item.get('votes', 0)}")
            print(f"     댓글수: {item.get('comments', 0)}")
    else:
        print("⚠️ 신규 항목이 없습니다. (모두 이미 처리됨)")
        
except Exception as e:
    print(f"❌ 중복 필터링 확인 실패: {e}")
    import traceback
    traceback.print_exc()
    new_items = []

# 3단계: 콘텐츠 필터링 확인
print("\n[3단계] 콘텐츠 필터링 확인")
print("-" * 80)

if not new_items:
    print("⚠️ 신규 항목이 없어 필터링을 건너뜁니다.")
else:
    try:
        from automation.content_filter import ContentFilter
        from automation.geeknews_pipeline import DEFAULT_MIN_VOTES
        
        min_votes = DEFAULT_MIN_VOTES
        print(f"최소 투표수 기준: {min_votes}")
        
        content_filter = ContentFilter(
            min_votes=min_votes,
            enable_scraping=False
        )
        
        # 각 항목별 상세 분석
        print("\n항목별 상세 분석:")
        print("-" * 80)
        
        analyzed_items = []
        for item in new_items:
            from automation.content_filter import ContentMetrics
            metrics = content_filter.analyze(item)
            should_process = content_filter.should_process(metrics)
            
            analyzed_items.append((item, metrics, should_process))
            
            print(f"\n제목: {item.get('title', 'N/A')[:60]}...")
            print(f"  투표수: {metrics.votes} (기준: {min_votes}) {'✅' if metrics.votes >= min_votes else '❌'}")
            print(f"  댓글수: {metrics.comments}")
            print(f"  AI 관련: {metrics.is_ai_related} {'✅' if metrics.is_ai_related else ''}")
            print(f"  트렌드: {metrics.is_trending} {'✅' if metrics.is_trending else ''}")
            print(f"  카테고리: {', '.join(metrics.categories)}")
            print(f"  우선순위 점수: {metrics.priority_score:.1f}/100")
            print(f"  처리 여부: {'✅ 처리됨' if should_process else '❌ 필터링됨'}")
            
            if not should_process:
                print(f"    필터링 이유:")
                if not metrics.is_ai_related and metrics.votes < min_votes:
                    print(f"      - AI 관련 아님 AND 투표수 부족 ({metrics.votes} < {min_votes})")
                elif not metrics.is_ai_related:
                    print(f"      - AI 관련 아님")
                elif metrics.votes < min_votes:
                    print(f"      - 투표수 부족 ({metrics.votes} < {min_votes})")
                if not metrics.is_trending and metrics.priority_score < 20:
                    print(f"      - 트렌드 아님 AND 우선순위 점수 낮음 ({metrics.priority_score:.1f} < 20)")
        
        # 필터링 결과 요약
        print("\n" + "=" * 80)
        print("필터링 결과 요약")
        print("=" * 80)
        
        processed_count = sum(1 for _, _, should_process in analyzed_items if should_process)
        filtered_count = len(analyzed_items) - processed_count
        
        print(f"총 신규 항목: {len(analyzed_items)}개")
        print(f"✅ 처리 가능: {processed_count}개")
        print(f"❌ 필터링됨: {filtered_count}개")
        
        # 필터링된 항목의 이유 분석
        if filtered_count > 0:
            print("\n필터링된 항목 분석:")
            low_votes = sum(1 for _, m, sp in analyzed_items if not sp and m.votes < min_votes and not m.is_ai_related)
            not_ai = sum(1 for _, m, sp in analyzed_items if not sp and not m.is_ai_related)
            low_score = sum(1 for _, m, sp in analyzed_items if not sp and m.priority_score < 20)
            
            print(f"  - 투표수 부족 (AI 아님): {low_votes}개")
            print(f"  - AI 관련 아님: {not_ai}개")
            print(f"  - 우선순위 점수 낮음: {low_score}개")
        
        # 실제 필터링 실행
        print("\n" + "=" * 80)
        print("실제 필터링 실행 결과")
        print("=" * 80)
        
        filtered_items = content_filter.filter_and_sort(new_items, max_items=10)
        print(f"✅ 최종 선별된 항목: {len(filtered_items)}개")
        
        if filtered_items:
            print("\n선별된 항목 목록:")
            for i, (item, metrics) in enumerate(filtered_items, 1):
                print(f"  {i}. {item.get('title', 'N/A')[:60]}...")
                print(f"     우선순위: {metrics.priority_score:.1f}, AI: {metrics.is_ai_related}, 투표: {metrics.votes}")
        else:
            print("⚠️ 필터링 후 선별된 항목이 없습니다.")
            print("\n💡 개선 제안:")
            print("  1. --min-votes 값을 낮춰보세요 (예: --min-votes 5)")
            print("  2. 필터링 기준을 완화하세요")
            print("  3. 더 많은 데이터 소스를 추가하세요")
        
    except Exception as e:
        print(f"❌ 콘텐츠 필터링 확인 실패: {e}")
        import traceback
        traceback.print_exc()

# 4단계: 향상된 소스 확인
print("\n" + "=" * 80)
print("[4단계] 향상된 데이터 소스 확인")
print("=" * 80)

try:
    from automation.enhanced_sources import DevToCollector, StackOverflowCollector, ContentAggregator
    import asyncio
    
    async def check_enhanced_sources():
        print("\nDevToCollector 테스트...")
        devto = DevToCollector()
        devto_contents = await devto.collect()
        print(f"✅ DevTo: {len(devto_contents)}개 기사 수집")
        
        print("\nStackOverflowCollector 테스트...")
        so = StackOverflowCollector()
        so_contents = await so.collect_top_questions(days=7)
        print(f"✅ StackOverflow: {len(so_contents)}개 질문 수집")
        
        print("\nContentAggregator 통합 테스트...")
        aggregator = ContentAggregator()
        all_contents = await aggregator.aggregate_all_sources()
        print(f"✅ 통합: {len(all_contents)}개 콘텐츠 수집")
        
        if all_contents:
            print("\n통합 콘텐츠 샘플 (최대 3개):")
            for i, content in enumerate(all_contents[:3], 1):
                print(f"  {i}. {content.title[:60]}...")
                print(f"     소스: {content.source}, Engagement: {content.engagement}")
        else:
            print("⚠️ 통합 콘텐츠가 없습니다. (필터링이 너무 엄격할 수 있음)")
    
    asyncio.run(check_enhanced_sources())
    
except Exception as e:
    print(f"❌ 향상된 소스 확인 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("진단 완료")
print("=" * 80)

