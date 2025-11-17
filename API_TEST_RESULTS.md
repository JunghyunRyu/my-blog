# API 직접 동작 확인 테스트 결과

## 테스트 일시
2025년 1월 17일

## 테스트 환경
- **테스트 아이템**: "Playwright로 QA 프로세스 자동화"
- **모델 설정**:
  - OpenAI: `gpt-5-mini`
  - Claude: `claude-haiku-4-5`
  - Perplexity: `sonar`
  - Gemini: `gemini-2.5-flash-lite`

## 테스트 결과

### ✅ OpenAI API - 성공
- **상태**: ✅ 성공
- **요약 길이**: 401자
- **QA 쌍 개수**: 3개
- **문제점**: 없음
- **해결 사항**: 
  - `gpt-5-mini` 모델은 temperature 파라미터를 지원하지 않아 조건부로 제거
  - 모델 이름이 `gpt-5`로 시작하면 temperature 파라미터를 제외하도록 수정

### ❌ Claude API - 실패 (JSON 파싱 오류)
- **상태**: ❌ 실패
- **오류**: JSON 파싱 오류 (Expecting value: line 276 column 25)
- **원인**: 
  - API 호출은 성공했지만 응답이 너무 길어서 JSON이 잘렸을 가능성
  - 또는 응답 형식이 예상과 다름
- **해결 방안**:
  1. `max_tokens` 값을 늘려서 전체 응답을 받도록 수정
  2. 프롬프트에서 JSON 형식 명확히 지정
  3. JSON 파싱 로직 개선 (불완전한 JSON 처리)

### ✅ Perplexity API - 부분 성공
- **상태**: ✅ API 호출 성공
- **요약 길이**: 49자
- **QA 쌍 개수**: 0개
- **문제점**: 
  - API 호출은 성공했지만 QA 쌍이 생성되지 않음
  - JSON 형식이 예상과 다를 수 있음
- **해결 방안**:
  1. 응답 형식 확인 및 JSON 파싱 로직 개선
  2. 프롬프트에서 JSON 스키마 명확히 지정

### ✅ Gemini API - 부분 성공
- **상태**: ✅ API 호출 성공
- **요약 길이**: 49자
- **QA 쌍 개수**: 0개
- **문제점**: 
  - API 호출은 성공했지만 QA 쌍이 생성되지 않음
  - JSON 형식이 예상과 다를 수 있음
- **해결 방안**:
  1. 응답 형식 확인 및 JSON 파싱 로직 개선
  2. 프롬프트에서 JSON 스키마 명확히 지정

## 적용된 수정 사항

### 1. OpenAI Temperature 파라미터 처리
```python
# temperature를 지원하는 모델에만 추가
# gpt-5-mini 같은 일부 모델은 temperature를 지원하지 않음
if not self.model.startswith("gpt-5"):
    payload["temperature"] = 0.3
```

### 2. JSON 파싱 로직 개선
- 마크다운 코드 블록 처리 개선 (` ```json ... ``` ` 형식 지원)
- JSON 배열도 처리 가능하도록 개선
- 불완전한 JSON 처리 (중괄호 균형 확인 및 자동 보정)

## 다음 단계

### 즉시 수정 필요
1. **Claude API**: 
   - `max_tokens` 값 증가 (4096 → 8192)
   - 프롬프트에서 JSON 형식 명확히 지정
   - 응답 길이 제한 확인

2. **Perplexity/Gemini API**:
   - 실제 응답 형식 확인
   - JSON 파싱 로직 디버깅
   - 프롬프트에서 JSON 스키마 명확히 지정

### 개선 사항
1. **에러 처리 강화**: JSON 파싱 실패 시 원본 응답 저장
2. **로깅 개선**: API 응답의 일부를 로그에 기록하여 디버깅 용이하게
3. **재시도 로직**: JSON 파싱 실패 시 재시도 또는 백업 처리

## 최종 상태

| API | 상태 | 비고 |
|-----|------|------|
| OpenAI | ✅ 정상 작동 | QA 쌍 3개 생성 성공 |
| Claude | ⚠️ 부분 작동 | JSON 파싱 오류 (응답 길이 문제) |
| Perplexity | ⚠️ 부분 작동 | API 호출 성공, QA 쌍 0개 |
| Gemini | ⚠️ 부분 작동 | API 호출 성공, QA 쌍 0개 |

## 권장 사항

1. **프로덕션 환경**: 현재는 OpenAI만 완전히 작동하므로 OpenAI를 기본으로 사용
2. **개발 환경**: Claude, Perplexity, Gemini의 JSON 파싱 문제 해결 후 사용
3. **모니터링**: API 응답 형식과 파싱 성공률을 모니터링하여 문제 조기 발견

