"""API 직접 동작 확인 테스트."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("API 직접 동작 확인 테스트")
print("=" * 80)

# 환경 변수 확인
print("\n[1] 환경 변수 확인")
print("-" * 80)
claude_key = os.getenv("CLAUDE_API_KEY")
claude_model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")
perplexity_key = os.getenv("PERPLEXITY_API_KEY")
perplexity_model = os.getenv("PERPLEXITY_MODEL", "sonar")
gemini_key = os.getenv("GEMINI_API_KEY")
gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
openai_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print(f"Claude API Key: {'[설정됨]' if claude_key else '[없음]'}")
print(f"Claude Model: {claude_model}")
print(f"Perplexity API Key: {'[설정됨]' if perplexity_key else '[없음]'}")
print(f"Perplexity Model: {perplexity_model}")
print(f"Gemini API Key: {'[설정됨]' if gemini_key else '[없음]'}")
print(f"Gemini Model: {gemini_model}")
print(f"OpenAI API Key: {'[설정됨]' if openai_key else '[없음]'}")
print(f"OpenAI Model: {openai_model}")

# 테스트용 아이템
test_item = {
    "title": "Playwright로 QA 프로세스 자동화",
    "summary": "Playwright 프레임워크를 사용하여 QA 워크플로우를 자동화하는 방법을 소개합니다.",
    "link": "https://example.com/playwright-qa"
}

print("\n[2] 테스트 아이템")
print("-" * 80)
print(f"제목: {test_item['title']}")
print(f"요약: {test_item['summary']}")

# 각 API 테스트
results = {}

# OpenAI 테스트
if openai_key:
    print("\n[3] OpenAI API 테스트")
    print("-" * 80)
    try:
        from automation.qa_generator import OpenAIProvider
        provider = OpenAIProvider(api_key=openai_key, model=openai_model)
        result = provider.generate(test_item)
        results["OpenAI"] = {
            "status": "SUCCESS",
            "summary_length": len(result.summary),
            "qa_pairs_count": len(result.qa_pairs),
            "error": None
        }
        print("[OK] OpenAI API 호출 성공")
        print(f"  요약 길이: {len(result.summary)}자")
        print(f"  QA 쌍 개수: {len(result.qa_pairs)}개")
    except Exception as e:
        results["OpenAI"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"[FAIL] OpenAI API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n[3] OpenAI API 테스트 - 스킵 (API 키 없음)")
    results["OpenAI"] = {"status": "SKIP", "error": "API 키 없음"}

# Claude 테스트
if claude_key:
    print("\n[4] Claude API 테스트")
    print("-" * 80)
    try:
        from automation.qa_generator import ClaudeProvider
        provider = ClaudeProvider(api_key=claude_key, model=claude_model)
        result = provider.generate(test_item)
        results["Claude"] = {
            "status": "SUCCESS",
            "summary_length": len(result.summary),
            "qa_pairs_count": len(result.qa_pairs),
            "error": None
        }
        print("[OK] Claude API 호출 성공")
        print(f"  요약 길이: {len(result.summary)}자")
        print(f"  QA 쌍 개수: {len(result.qa_pairs)}개")
    except Exception as e:
        results["Claude"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"[FAIL] Claude API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n[4] Claude API 테스트 - 스킵 (API 키 없음)")
    results["Claude"] = {"status": "SKIP", "error": "API 키 없음"}

# Perplexity 테스트
if perplexity_key:
    print("\n[5] Perplexity API 테스트")
    print("-" * 80)
    try:
        from automation.qa_generator import PerplexityProvider
        provider = PerplexityProvider(api_key=perplexity_key, model=perplexity_model)
        result = provider.generate(test_item)
        results["Perplexity"] = {
            "status": "SUCCESS",
            "summary_length": len(result.summary),
            "qa_pairs_count": len(result.qa_pairs),
            "error": None
        }
        print("[OK] Perplexity API 호출 성공")
        print(f"  요약 길이: {len(result.summary)}자")
        print(f"  QA 쌍 개수: {len(result.qa_pairs)}개")
    except Exception as e:
        results["Perplexity"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"[FAIL] Perplexity API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n[5] Perplexity API 테스트 - 스킵 (API 키 없음)")
    results["Perplexity"] = {"status": "SKIP", "error": "API 키 없음"}

# Gemini 테스트
if gemini_key:
    print("\n[6] Gemini API 테스트")
    print("-" * 80)
    try:
        from automation.qa_generator import GeminiProvider
        provider = GeminiProvider(api_key=gemini_key, model=gemini_model)
        result = provider.generate(test_item)
        results["Gemini"] = {
            "status": "SUCCESS",
            "summary_length": len(result.summary),
            "qa_pairs_count": len(result.qa_pairs),
            "error": None
        }
        print("[OK] Gemini API 호출 성공")
        print(f"  요약 길이: {len(result.summary)}자")
        print(f"  QA 쌍 개수: {len(result.qa_pairs)}개")
    except Exception as e:
        results["Gemini"] = {
            "status": "FAIL",
            "error": str(e)
        }
        print(f"[FAIL] Gemini API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n[6] Gemini API 테스트 - 스킵 (API 키 없음)")
    results["Gemini"] = {"status": "SKIP", "error": "API 키 없음"}

# 최종 요약
print("\n" + "=" * 80)
print("최종 결과 요약")
print("=" * 80)

for api_name, result in results.items():
    status = result["status"]
    if status == "SUCCESS":
        print(f"[OK] {api_name}: 성공")
        print(f"     요약 길이: {result['summary_length']}자, QA 쌍: {result['qa_pairs_count']}개")
    elif status == "FAIL":
        print(f"[FAIL] {api_name}: 실패")
        print(f"     오류: {result['error'][:100]}...")
    else:
        print(f"[SKIP] {api_name}: 스킵 ({result['error']})")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)

