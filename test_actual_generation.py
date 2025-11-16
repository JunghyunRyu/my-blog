"""실제 블로그 포스트 생성 테스트 (작동하는 AI Provider만 사용)."""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def test_blog_post_generation():
    """실제 블로그 포스트 생성 테스트."""
    print("=" * 60)
    print("실제 블로그 포스트 생성 테스트")
    print("=" * 60)
    
    # 테스트용 기사 (실제 GeekNews 스타일)
    test_article = {
        "title": "AI-Powered Testing Tools: The Future of QA Automation",
        "summary": "최근 AI 기반 테스팅 도구들이 QA 업계를 혁신하고 있습니다. 이 기사는 AI를 활용한 자동화 테스트의 현재와 미래를 탐구합니다.",
        "link": "https://example.com/ai-testing-tools"
    }
    
    print(f"\n테스트 기사:")
    print(f"제목: {test_article['title']}")
    print(f"요약: {test_article['summary']}")
    
    # OpenAI로 블로그 포스트 생성
    if os.getenv("OPENAI_API_KEY"):
        print("\n" + "-" * 60)
        print("[1] OpenAI로 블로그 포스트 생성 중...")
        print("-" * 60)
        
        try:
            from automation.qa_generator import OpenAIProvider, QAResult
            from automation.geeknews_pipeline import write_post
            
            provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
            qa_result = provider.generate(test_article)
            
            print(f"✅ 분석 완료!")
            print(f"   요약: {qa_result.summary[:100]}...")
            print(f"   QA 페어: {len(qa_result.qa_pairs)}개")
            print(f"   인사이트: {len(qa_result.qa_engineer_insights)}개")
            
            # 블로그 포스트 파일 생성
            post_path = write_qa_post(qa_result, test_article)
            print(f"\n✅ 블로그 포스트 생성 완료!")
            print(f"   파일 경로: {post_path}")
            print(f"   파일 크기: {post_path.stat().st_size} bytes")
            
            # 파일 내용 일부 확인
            with open(post_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"   내용 길이: {len(content)}자")
                print(f"\n   파일 미리보기 (처음 300자):")
                print(f"   {'-' * 60}")
                print(content[:300])
                print(f"   {'-' * 60}")
            
            return post_path
            
        except Exception as e:
            print(f"[FAIL] OpenAI 블로그 포스트 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # Perplexity로 블로그 포스트 생성
    if os.getenv("PERPLEXITY_API_KEY"):
        print("\n" + "-" * 60)
        print("[2] Perplexity로 블로그 포스트 생성 중...")
        print("-" * 60)
        
        try:
            from automation.qa_generator import PerplexityProvider
            from automation.geeknews_pipeline import write_post
            
            provider = PerplexityProvider(api_key=os.getenv("PERPLEXITY_API_KEY"))
            qa_result = provider.generate(test_article)
            
            print(f"✅ 분석 완료!")
            print(f"   요약: {qa_result.summary[:100]}...")
            print(f"   QA 페어: {len(qa_result.qa_pairs)}개")
            
            # 블로그 포스트 파일 생성
            post_path = write_qa_post(qa_result, test_article)
            print(f"\n✅ 블로그 포스트 생성 완료!")
            print(f"   파일 경로: {post_path}")
            
            return post_path
            
        except Exception as e:
            print(f"[FAIL] Perplexity 블로그 포스트 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    print("\n⚠️ 사용 가능한 AI Provider가 없습니다.")
    return None


async def test_data_collection_and_generation():
    """실제 데이터 수집 후 블로그 포스트 생성 테스트."""
    print("\n" + "=" * 60)
    print("데이터 수집 + 블로그 포스트 생성 통합 테스트")
    print("=" * 60)
    
    try:
        from automation.enhanced_sources import DevToCollector
        
        print("\n[1] Dev.to에서 최신 기사 수집 중...")
        collector = DevToCollector()
        contents = await collector.collect()
        
        if not contents:
            print("⚠️ 수집된 기사가 없습니다.")
            return
        
        # 첫 번째 기사 선택
        article = contents[0]
        print(f"✅ {len(contents)}개 기사 수집 완료")
        print(f"   선택된 기사: {article.title[:60]}...")
        
        # OpenAI로 분석
        if os.getenv("OPENAI_API_KEY"):
            print("\n[2] OpenAI로 분석 및 블로그 포스트 생성 중...")
            from automation.qa_generator import OpenAIProvider
            from automation.geeknews_pipeline import write_post
            
            provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
            
            item = {
                "title": article.title,
                "summary": article.content[:500] if article.content else "",
                "link": article.url
            }
            
            qa_result = provider.generate(item)
            
            # 블로그 포스트 생성
            post_item = {
                "title": article.title,
                "link": article.url,
                "published_at": article.published_at.isoformat() if article.published_at else None
            }
            
            feed_item = {
                "title": article.title,
                "link": article.url,
                "published_at": article.published_at.isoformat() if article.published_at else None
            }
            post_path = write_post(feed_item, qa_result)
            
            print(f"✅ 통합 테스트 완료!")
            print(f"   생성된 포스트: {post_path.name}")
            print(f"   요약: {qa_result.summary[:150]}...")
            
    except Exception as e:
        print(f"[FAIL] 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수."""
    print("\n" + "=" * 60)
    print("실제 블로그 포스트 생성 테스트")
    print("=" * 60)
    
    # 1. 테스트 기사로 블로그 포스트 생성
    post_path = await test_blog_post_generation()
    
    # 2. 실제 데이터 수집 후 블로그 포스트 생성
    await test_data_collection_and_generation()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    
    if post_path:
        print(f"\n생성된 블로그 포스트를 확인하세요:")
        print(f"  {post_path}")
        print(f"\n다음 단계:")
        print(f"  1. 생성된 포스트 파일을 확인")
        print(f"  2. Jekyll 블로그에 배포")
        print(f"  3. 기존 파이프라인 실행: python -m automation.geeknews_pipeline")


if __name__ == "__main__":
    asyncio.run(main())

