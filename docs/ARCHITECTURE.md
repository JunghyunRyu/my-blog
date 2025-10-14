# 시스템 아키텍처

GeekNews 블로그 자동화 시스템의 구조와 동작 방식을 설명합니다.

## 📋 목차

- [시스템 개요](#시스템-개요)
- [아키텍처 다이어그램](#아키텍처-다이어그램)
- [컴포넌트 설명](#컴포넌트-설명)
- [데이터 흐름](#데이터-흐름)
- [기술 스택](#기술-스택)
- [확장성](#확장성)

## 🎯 시스템 개요

GeekNews 자동화는 다음과 같은 목적으로 설계되었습니다:

1. **자동화**: GeekNews RSS 피드에서 콘텐츠를 자동 수집
2. **지능화**: AI 기반 필터링 및 분석
3. **전문화**: QA Engineer 관점의 심층 콘텐츠 생성
4. **안정성**: EC2 환경에서 무중단 운영

### 핵심 원칙

- **단순성**: 복잡한 의존성 최소화
- **안정성**: 에러 발생 시 자동 복구
- **효율성**: 최소 리소스로 최대 효과
- **확장성**: 쉬운 기능 추가 및 변경

## 🏗️ 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                     EC2 Instance (Ubuntu)                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │            systemd / cron (스케줄러)                  │ │
│  └─────────────────┬───────────────────────────────────────┘ │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────────┐ │
│  │              scripts/run_once.py                        │ │
│  │              scripts/run_scheduler.py                   │ │
│  └─────────────────┬───────────────────────────────────────┘ │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────────┐ │
│  │           geeknews/pipeline.py (메인)                  │ │
│  │                                                         │ │
│  │  1. RSS 피드 수집                                      │ │
│  │  2. 중복 필터링                                        │ │
│  │  3. AI/트렌드 필터링 ◄─── content_filter.py          │ │
│  │  4. 웹 연구 (선택) ◄────── web_researcher.py          │ │
│  │  5. QA 콘텐츠 생성 ◄─────── qa_generator.py           │ │
│  │  6. Jekyll 포스트 작성                                 │ │
│  │  7. 상태 저장                                          │ │
│  └─────────────────┬───────────────────────────────────────┘ │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────────┐ │
│  │                외부 API 호출                           │ │
│  │                                                         │ │
│  │  • GeekNews RSS                                        │ │
│  │  • OpenAI GPT API ◄─── config.py                      │ │
│  │  • DuckDuckGo Search                                   │ │
│  │  • HackerNews API                                      │ │
│  └─────────────────┬───────────────────────────────────────┘ │
│                    │                                        │
│  ┌─────────────────▼───────────────────────────────────────┐ │
│  │                 로컬 저장소                            │ │
│  │                                                         │ │
│  │  • _posts/learning/                                    │ │
│  │  • _posts/qa-engineer/                                 │ │
│  │  • data/geeknews_state.json                            │ │
│  │  • logs/*.log ◄────────── logger.py                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 컴포넌트 설명

### 1. geeknews 패키지 (핵심 로직)

#### config.py
- **역할**: 중앙 집중식 설정 관리
- **기능**:
  - 환경 변수 로딩
  - 기본값 설정
  - 설정 유효성 검증
  - EC2 환경 자동 감지
  - 디렉토리 자동 생성

```python
from geeknews.config import Config

# 설정 사용
api_key = Config.OPENAI_API_KEY
max_posts = Config.MAX_POSTS_PER_RUN

# 설정 검증
errors = Config.validate()
```

#### pipeline.py
- **역할**: 메인 파이프라인 로직
- **주요 함수**:
  - `fetch_feed()`: RSS/Atom 피드 수집
  - `select_new_items()`: 중복 필터링
  - `write_post()`: Jekyll 포스트 작성
  - `run_pipeline()`: 전체 파이프라인 실행
  - `main()`: CLI 진입점

**파이프라인 흐름**:
```python
items = fetch_feed(url)                    # 1. RSS 수집
processed = load_state()                   # 2. 상태 로드
new_items = select_new_items(items)        # 3. 중복 제거
filtered = filter_and_sort(new_items)      # 4. 필터링
for item, metrics in filtered:
    research = researcher.research()        # 5. 웹 연구
    qa_result = generator.generate()        # 6. QA 생성
    write_post(item, qa_result)            # 7. 포스트 작성
save_state(processed)                      # 8. 상태 저장
```

#### content_filter.py
- **역할**: 콘텐츠 필터링 및 우선순위 결정
- **주요 클래스**:
  - `ContentMetrics`: 콘텐츠 메트릭 데이터
  - `ContentFilter`: 필터링 로직

**필터링 알고리즘**:
```python
priority_score = 0
if is_ai_related: priority_score += 30      # AI 관련성
if is_trending: priority_score += 20        # 트렌드
if is_qa: priority_score += 20              # QA 관련
priority_score += votes_score               # 투표수 (선택)
priority_score += comments_score            # 댓글 (선택)

# 통과 조건: 20점 이상
if priority_score >= 20: process()
```

#### qa_generator.py
- **역할**: AI 기반 QA 콘텐츠 생성
- **주요 클래스**:
  - `QAResult`: 생성된 콘텐츠 데이터
  - `QAContentGenerator`: 생성 로직 총괄
  - `OpenAIProvider`: OpenAI API 호출
  - `RuleBasedProvider`: 백업 로직

**생성 프로세스**:
```python
# 1. 프롬프트 구성 (웹 연구 데이터 포함)
prompt = build_prompt(item, research_data)

# 2. OpenAI API 호출
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[system, user],
    response_format={"type": "json_object"}
)

# 3. 응답 파싱
qa_result = parse_response(response.content)

# 4. 검증 및 반환
return qa_result
```

#### web_researcher.py
- **역할**: 웹 검색 및 외부 자료 수집
- **주요 클래스**:
  - `WebResource`: 검색 결과 데이터
  - `ResearchResult`: 통합 연구 결과
  - `WebResearcher`: 검색 로직

**검색 대상**:
1. DuckDuckGo API (웹 검색)
2. HackerNews Algolia API (전문가 의견)
3. 관련 기술 문서 (Medium, Dev.to 등)

#### logger.py
- **역할**: 중앙 집중식 로깅
- **주요 클래스**:
  - `JsonFormatter`: JSON 형식 로그
  - `TextFormatter`: 텍스트 형식 로그

**로깅 계층**:
```
DEBUG    상세한 디버깅 정보
INFO     일반 정보 (기본값)
WARNING  경고 메시지
ERROR    에러 발생
CRITICAL 심각한 오류
```

### 2. scripts 패키지 (실행 스크립트)

#### run_once.py
- **역할**: 파이프라인 1회 실행
- **사용처**: cron, systemd 타이머, 수동 실행

```python
def main():
    # 1. 설정 검증
    errors = Config.validate()
    if errors: exit(1)
    
    # 2. 파이프라인 실행
    return pipeline_main()
```

#### run_scheduler.py
- **역할**: 파이프라인 주기적 실행
- **사용처**: systemd 서비스, 장기 실행

```python
def main():
    while True:
        run_pipeline()
        time.sleep(interval)
```

#### health_check.py
- **역할**: 시스템 상태 점검
- **검사 항목**:
  - 설정 유효성
  - OpenAI API 키
  - 네트워크 연결
  - 디스크 용량
  - 마지막 실행 시간
  - 디렉토리 구조

### 3. deploy 패키지 (배포 도구)

#### systemd/
- `geeknews.service`: 백그라운드 서비스
- `geeknews.timer`: 타이머 기반 실행
- `geeknews-oneshot.service`: 1회 실행용

#### cron/
- `geeknews.cron`: 전통적인 cron 설정

#### setup_ec2.sh
- EC2 초기 설정 자동화
- 대화형 설정 프로세스

#### deploy.sh
- 무중단 배포
- 백업 및 롤백 지원

## 🌊 데이터 흐름

### 1. 수집 단계
```
GeekNews RSS → fetch_feed() → List[FeedItem]
```

### 2. 필터링 단계
```
List[FeedItem] → load_state() → 중복 제거
              → ContentFilter → 우선순위 점수
              → filter_and_sort() → List[(item, metrics)]
```

### 3. 처리 단계
```
For each (item, metrics):
  → WebResearcher.research() → ResearchResult
  → QAContentGenerator.generate() → QAResult
  → write_post() → Markdown 파일
```

### 4. 저장 단계
```
생성된 포스트 → _posts/{category}/YYYY-MM-DD-{slug}.md
처리 상태 → data/geeknews_state.json
실행 로그 → logs/geeknews.log
```

## 🛠️ 기술 스택

### 언어 및 프레임워크
- **Python 3.11+**: 메인 언어
- **asyncio**: 비동기 처리 (최소 사용)
- **urllib**: HTTP 클라이언트

### 라이브러리
- **openai**: OpenAI GPT API
- **feedparser**: RSS/Atom 파싱
- **requests**: HTTP 요청
- **python-dotenv**: 환경 변수 관리

### 인프라
- **EC2**: Ubuntu 22.04 LTS
- **systemd**: 서비스 관리
- **cron**: 스케줄링 (대안)
- **Git**: 버전 관리

### 외부 서비스
- **OpenAI GPT API**: AI 콘텐츠 생성
- **GeekNews RSS**: 뉴스 소스
- **DuckDuckGo API**: 웹 검색
- **HackerNews Algolia API**: 전문가 의견

## 🔐 보안 고려사항

### API 키 관리
- 환경 변수(.env)로 관리
- Git에 절대 커밋 안 함
- 파일 권한 600 설정

### 네트워크 보안
- HTTPS만 사용
- API 호출 타임아웃 설정
- Rate limiting 준수

### 시스템 보안
- SSH 키 기반 인증
- UFW 방화벽 설정
- 최소 권한 원칙

## 📈 확장성

### 수평 확장
여러 EC2 인스턴스 운영 가능:
```
EC2-1: Learning 카테고리 전담
EC2-2: QA Engineer 카테고리 전담
```

### 기능 확장
추가 가능한 기능:
- 다른 RSS 피드 소스
- 다른 AI 모델 (Claude, Gemini)
- 다국어 번역
- 이미지 자동 생성
- 소셜 미디어 자동 포스팅

### 성능 최적화
- Redis 캐싱
- PostgreSQL/SQLite 상태 저장
- 비동기 처리 확대
- 배치 API 호출

## 🔄 개선 로드맵

### 단기 (1-3개월)
- [ ] 단위 테스트 추가
- [ ] CI/CD 파이프라인 구축
- [ ] CloudWatch 연동
- [ ] 알림 기능 (Slack, Email)

### 중기 (3-6개월)
- [ ] 웹 대시보드 추가
- [ ] A/B 테스트 시스템
- [ ] 독자 피드백 수집
- [ ] 다국어 지원

### 장기 (6-12개월)
- [ ] 머신러닝 기반 필터링
- [ ] 실시간 스트리밍 처리
- [ ] 마이크로서비스 아키텍처
- [ ] 멀티 리전 배포

---

**관련 문서**:
- [EC2 배포 가이드](EC2_DEPLOYMENT.md)
- [운영 매뉴얼](OPERATIONS.md)


