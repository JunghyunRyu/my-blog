"""통합 테스트: 실제 데이터 수집 및 AI 분석 테스트."""

import os
import asyncio
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

async def test_data_collection():
    """데이터 수집 테스트."""
    print("=" * 60)
    print("데이터 수집 테스트")
    print("=" * 60)
    
    try:
        from automation.enhanced_sources import DevToCollector, StackOverflowCollector, ContentAggregator
        
        # DevToCollector 테스트 (API 키 불필요)
        print("\n[1] DevToCollector 테스트...")
        devto = DevToCollector()
        devto_contents = await devto.collect()
        print(f"    수집된 Dev.to 기사: {len(devto_contents)}개")
        if devto_contents:
            print(f"    예시: {devto_contents[0].title[:50]}...")
        
        # StackOverflowCollector 테스트
        print("\n[2] StackOverflowCollector 테스트...")
        so = StackOverflowCollector()
        so_contents = await so.collect_top_questions(days=7)
        print(f"    수집된 Stack Overflow 질문: {len(so_contents)}개")
        if so_contents:
            print(f"    예시: {so_contents[0].title[:50]}...")
        
        # ContentAggregator 통합 테스트
        print("\n[3] ContentAggregator 통합 테스트...")
        aggregator = ContentAggregator()
        all_contents = await aggregator.aggregate_all_sources()
        print(f"    총 수집된 콘텐츠: {len(all_contents)}개")
        
        return all_contents
        
    except Exception as e:
        print(f"[FAIL] 데이터 수집 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_ai_providers():
    """AI Provider 테스트."""
    print("\n" + "=" * 60)
    print("AI Provider 테스트")
    print("=" * 60)
    
    # 테스트용 아이템
    test_item = {
        "title": "AI-Powered Testing: The Future of QA",
        "summary": "This article discusses how AI is transforming the QA industry, with new tools and methodologies emerging.",
        "link": "https://example.com/ai-testing"
    }
    
    results = {}
    
    # OpenAI 테스트
    if os.getenv("OPENAI_API_KEY"):
        print("\n[1] OpenAI Provider 테스트...")
        try:
            from automation.qa_generator import OpenAIProvider
            provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
            result = provider.generate(test_item)
            print(f"    [OK] OpenAI 분석 완료")
            print(f"    요약 길이: {len(result.summary)}자")
            print(f"    QA 페어: {len(result.qa_pairs)}개")
            results["openai"] = result
        except Exception as e:
            print(f"    [FAIL] OpenAI 테스트 실패: {e}")
    
    # Claude 테스트
    if os.getenv("CLAUDE_API_KEY"):
        print("\n[2] Claude Provider 테스트...")
        try:
            from automation.qa_generator import ClaudeProvider
            provider = ClaudeProvider(api_key=os.getenv("CLAUDE_API_KEY"))
            result = provider.generate(test_item)
            print(f"    [OK] Claude 분석 완료")
            print(f"    요약 길이: {len(result.summary)}자")
            print(f"    QA 페어: {len(result.qa_pairs)}개")
            results["claude"] = result
        except Exception as e:
            print(f"    [FAIL] Claude 테스트 실패: {e}")
    
    # Perplexity 테스트 (실시간 웹 검색 포함)
    if os.getenv("PERPLEXITY_API_KEY"):
        print("\n[3] Perplexity Provider 테스트...")
        try:
            from automation.qa_generator import PerplexityProvider
            provider = PerplexityProvider(api_key=os.getenv("PERPLEXITY_API_KEY"))
            result = provider.generate(test_item)
            print(f"    [OK] Perplexity 분석 완료")
            print(f"    요약 길이: {len(result.summary)}자")
            print(f"    QA 페어: {len(result.qa_pairs)}개")
            results["perplexity"] = result
        except Exception as e:
            print(f"    [FAIL] Perplexity 테스트 실패: {e}")
    
    # Gemini 테스트
    if os.getenv("GEMINI_API_KEY"):
        print("\n[4] Gemini Provider 테스트...")
        try:
            from automation.qa_generator import GeminiProvider
            provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))
            result = provider.generate(test_item)
            print(f"    [OK] Gemini 분석 완료")
            print(f"    요약 길이: {len(result.summary)}자")
            print(f"    QA 페어: {len(result.qa_pairs)}개")
            results["gemini"] = result
        except Exception as e:
            print(f"    [FAIL] Gemini 테스트 실패: {e}")
    
    return results


async def test_enhanced_pipeline():
    """향상된 파이프라인 테스트 (제한적)."""
    print("\n" + "=" * 60)
    print("향상된 파이프라인 테스트")
    print("=" * 60)
    
    try:
        from automation.enhanced_pipeline_example import EnhancedQAPipeline
        
        print("\n[1] EnhancedQAPipeline 초기화...")
        pipeline = EnhancedQAPipeline()
        print("    [OK] 파이프라인 초기화 완료")
        
        print("\n[2] 프롬프트 템플릿 테스트...")
        from automation.enhanced_prompts import EnhancedPromptTemplates
        
        context = {
            "title": "Test Article",
            "summary": "Test summary for QA testing",
            "link": "https://example.com"
        }
        
        prompt = EnhancedPromptTemplates.combine_prompts(
            persona="senior_qa_architect",
            analysis_type="deep_technical",
            format_type="case_study",
            level="intermediate",
            context=context
        )
        
        print(f"    [OK] 프롬프트 생성 완료 (길이: {len(prompt)}자)")
        
        print("\n[참고] 전체 파이프라인 실행은 시간이 오래 걸릴 수 있습니다.")
        print("      실제 실행은 다음 명령으로 수행하세요:")
        print("      python -m automation.enhanced_pipeline_example")
        
    except Exception as e:
        print(f"[FAIL] 파이프라인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수."""
    print("\n" + "=" * 60)
    print("QA 블로그 자동화 시스템 통합 테스트")
    print("=" * 60)
    
    # 1. 데이터 수집 테스트
    contents = await test_data_collection()
    
    # 2. AI Provider 테스트
    ai_results = await test_ai_providers()
    
    # 3. 향상된 파이프라인 테스트
    await test_enhanced_pipeline()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"수집된 콘텐츠: {len(contents)}개")
    print(f"테스트된 AI Provider: {len(ai_results)}개")
    print("\n[OK] 모든 기본 테스트 완료!")
    print("\n다음 단계:")
    print("1. 실제 파이프라인 실행: python -m automation.enhanced_pipeline_example")
    print("2. 기존 파이프라인 실행: python -m automation.geeknews_pipeline")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

