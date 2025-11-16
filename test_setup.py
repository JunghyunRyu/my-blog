"""API 키 설정 확인 및 기본 테스트 스크립트."""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("=" * 60)
print("API Keys 확인")
print("=" * 60)

keys_to_check = [
    'OPENAI_API_KEY',
    'CLAUDE_API_KEY',
    'PERPLEXITY_API_KEY',
    'GEMINI_API_KEY',
    'STACKOVERFLOW_API_KEY',
    'YOUTUBE_API_KEY'
]

for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # 키의 마지막 4자만 표시 (보안)
        masked = value[-4:] if len(value) > 4 else "****"
        print(f"{key}: 설정됨 (끝자리: ...{masked})")
    else:
        print(f"{key}: 미설정")

print("\n" + "=" * 60)
print("모듈 import 테스트")
print("=" * 60)

try:
    from automation.enhanced_sources import RedditCollector, DevToCollector, StackOverflowCollector
    print("[OK] enhanced_sources 모듈 import 성공")
except Exception as e:
    print(f"[FAIL] enhanced_sources 모듈 import 실패: {e}")

try:
    from automation.qa_generator import ClaudeProvider, PerplexityProvider, GeminiProvider
    print("[OK] qa_generator 모듈 import 성공")
except Exception as e:
    print(f"[FAIL] qa_generator 모듈 import 실패: {e}")

try:
    from automation.enhanced_prompts import EnhancedPromptTemplates, PromptOptimizer
    print("[OK] enhanced_prompts 모듈 import 성공")
except Exception as e:
    print(f"[FAIL] enhanced_prompts 모듈 import 실패: {e}")

try:
    from automation.social_media_publisher import InstagramPublisher, LinkedInPublisher, TwitterPublisher
    print("[OK] social_media_publisher 모듈 import 성공")
except Exception as e:
    print(f"[FAIL] social_media_publisher 모듈 import 실패: {e}")

try:
    from automation.enhanced_pipeline_example import EnhancedQAPipeline
    print("[OK] enhanced_pipeline_example 모듈 import 성공")
except Exception as e:
    print(f"[FAIL] enhanced_pipeline_example 모듈 import 실패: {e}")

print("\n" + "=" * 60)
print("기본 기능 테스트")
print("=" * 60)

# DevToCollector 테스트 (API 키 불필요)
try:
    collector = DevToCollector()
    print("[OK] DevToCollector 초기화 성공")
except Exception as e:
    print(f"[FAIL] DevToCollector 초기화 실패: {e}")

# StackOverflowCollector 테스트 (API 키 선택사항)
try:
    collector = StackOverflowCollector()
    print("[OK] StackOverflowCollector 초기화 성공")
except Exception as e:
    print(f"[FAIL] StackOverflowCollector 초기화 실패: {e}")

# EnhancedPromptTemplates 테스트
try:
    templates = EnhancedPromptTemplates()
    context = {
        "title": "Test Article",
        "summary": "Test summary",
        "link": "https://example.com"
    }
    prompt = EnhancedPromptTemplates.combine_prompts(
        persona="senior_qa_architect",
        analysis_type="deep_technical",
        format_type="case_study",
        level="intermediate",
        context=context
    )
    print("[OK] EnhancedPromptTemplates 작동 확인")
except Exception as e:
    print(f"[FAIL] EnhancedPromptTemplates 테스트 실패: {e}")

# PromptOptimizer 테스트
try:
    optimizer = PromptOptimizer()
    optimizer.track_performance("test_prompt", {"quality": 85.0, "engagement": 72.0})
    suggestions = optimizer.suggest_improvements("test_prompt")
    print("[OK] PromptOptimizer 작동 확인")
except Exception as e:
    print(f"[FAIL] PromptOptimizer 테스트 실패: {e}")

print("\n" + "=" * 60)
print("AI Provider 초기화 테스트")
print("=" * 60)

# OpenAI Provider
if os.getenv("OPENAI_API_KEY"):
    try:
        from automation.qa_generator import OpenAIProvider
        provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
        print("[OK] OpenAIProvider 초기화 성공")
    except Exception as e:
        print(f"[FAIL] OpenAIProvider 초기화 실패: {e}")
else:
    print("[WARN] OpenAIProvider: API 키 미설정")

# Claude Provider
if os.getenv("CLAUDE_API_KEY"):
    try:
        from automation.qa_generator import ClaudeProvider
        provider = ClaudeProvider(api_key=os.getenv("CLAUDE_API_KEY"))
        print("[OK] ClaudeProvider 초기화 성공")
    except Exception as e:
        print(f"[FAIL] ClaudeProvider 초기화 실패: {e}")
else:
    print("[WARN] ClaudeProvider: API 키 미설정")

# Perplexity Provider
if os.getenv("PERPLEXITY_API_KEY"):
    try:
        from automation.qa_generator import PerplexityProvider
        provider = PerplexityProvider(api_key=os.getenv("PERPLEXITY_API_KEY"))
        print("[OK] PerplexityProvider 초기화 성공")
    except Exception as e:
        print(f"[FAIL] PerplexityProvider 초기화 실패: {e}")
else:
    print("[WARN] PerplexityProvider: API 키 미설정")

# Gemini Provider
if os.getenv("GEMINI_API_KEY"):
    try:
        from automation.qa_generator import GeminiProvider
        provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))
        print("[OK] GeminiProvider 초기화 성공")
    except Exception as e:
        print(f"[FAIL] GeminiProvider 초기화 실패: {e}")
else:
    print("[WARN] GeminiProvider: API 키 미설정")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)

