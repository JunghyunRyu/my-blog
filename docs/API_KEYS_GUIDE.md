# API 키 발급 가이드

이 문서는 QA 블로그 자동화 시스템에 필요한 모든 API 키 발급 방법을 안내합니다.

## 목차

1. [AI API 키](#ai-api-키)
2. [데이터 소스 API 키](#데이터-소스-api-키)
3. [소셜 미디어 API 키](#소셜-미디어-api-키)
4. [API 키 보안 관리](#api-키-보안-관리)

---

## AI API 키

### OpenAI API

**용도**: 기본 AI 콘텐츠 생성

**발급 방법**:
1. https://platform.openai.com/ 접속
2. 계정 생성 또는 로그인
3. API Keys 메뉴로 이동
4. "Create new secret key" 클릭
5. 키 이름 입력 후 생성
6. **중요**: 키는 한 번만 표시되므로 복사하여 안전하게 보관

**비용**: 사용량 기반 (gpt-4o-mini는 저렴함)
**필수 여부**: 필수 (다른 AI 키가 없을 경우)

---

### Claude API (Anthropic)

**용도**: 기술적 심층 분석에 특화된 AI

**발급 방법**:
1. https://console.anthropic.com/ 접속
2. 계정 생성 또는 로그인
3. API Keys 메뉴로 이동
4. "Create Key" 클릭
5. 키 이름 입력 후 생성
6. 키 복사하여 보관

**비용**: 사용량 기반
**필수 여부**: 선택사항 (기술 분석 강화용)

**모델**: claude-3-5-sonnet-20241022 (기본값)

---

### Perplexity API

**용도**: 실시간 웹 검색 기반 AI 분석

**발급 방법**:
1. https://www.perplexity.ai/ 접속
2. 계정 생성 또는 로그인
3. Settings > API 메뉴로 이동
4. "Generate API Key" 클릭
5. 키 복사하여 보관

**비용**: 사용량 기반 (무료 티어 제공)
**필수 여부**: 선택사항 (최신 정보 수집 강화용)

**모델**: llama-3.1-sonar-large-128k-online (기본값)

---

### Gemini API (Google)

**용도**: 멀티모달 분석 (이미지, 차트 포함)

**발급 방법**:
1. https://makersuite.google.com/app/apikey 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 프로젝트 선택 또는 새로 생성
5. 키 복사하여 보관

**비용**: 사용량 기반 (무료 티어 제공)
**필수 여부**: 선택사항 (멀티모달 분석 강화용)

**모델**: gemini-1.5-pro (기본값)

---

## 데이터 소스 API 키

### Reddit API

**용도**: Reddit에서 QA 관련 포스트 수집

**발급 방법**:
1. https://www.reddit.com/prefs/apps 접속
2. Reddit 계정으로 로그인
3. 하단 "create another app..." 또는 "create app" 클릭
4. 앱 정보 입력:
   - **name**: QA-Blog-Automation (또는 원하는 이름)
   - **type**: script 선택
   - **description**: QA 블로그 자동화용
   - **about url**: (선택사항)
   - **redirect uri**: http://localhost:8080 (필수, 실제로 사용되지 않음)
5. "create app" 클릭
6. 생성된 앱 정보에서:
   - **client_id**: 앱 이름 아래 작은 글씨로 표시됨
   - **secret**: "secret" 필드의 값

**User Agent**: `QA-Blog-Automation/1.0` (기본값)

**비용**: 무료
**필수 여부**: 선택사항 (Reddit 수집 활성화 시)

---

### Stack Overflow API

**용도**: Stack Overflow에서 QA 관련 질문/답변 수집

**발급 방법**:
1. https://stackapps.com/apps/oauth/register 접속
2. Stack Overflow 계정으로 로그인
3. 앱 정보 입력:
   - **Application Name**: QA-Blog-Automation
   - **Application Website**: (선택사항)
   - **OAuth Domain**: localhost
   - **Application Description**: QA 블로그 자동화용
4. "Register Your Application" 클릭
5. 생성된 **Client Key** 복사

**참고**: API 키 없이도 사용 가능하지만, 키가 있으면 더 높은 rate limit 제공

**비용**: 무료
**필수 여부**: 선택사항

---

### Dev.to API

**용도**: Dev.to에서 QA 관련 아티클 수집

**발급 방법**:
1. https://dev.to/settings/extensions 접속
2. Dev.to 계정으로 로그인
3. "Generate API Key" 클릭
4. 키 복사하여 보관

**참고**: API 키 없이도 공개 API 사용 가능

**비용**: 무료
**필수 여부**: 선택사항

---

## 소셜 미디어 API 키

### Instagram Graph API

**용도**: Instagram에 블로그 포스트 자동 게시

**발급 방법**:
1. https://developers.facebook.com/ 접속
2. Facebook 계정으로 로그인
3. "My Apps" > "Create App" 클릭
4. 앱 유형 선택: "Business" 또는 "Other"
5. 앱 이름 입력 후 생성
6. "Add Product" > "Instagram Graph API" 추가
7. "Basic Display" 또는 "Instagram Graph API" 설정
8. OAuth 설정:
   - Valid OAuth Redirect URIs 추가
   - 앱 검수 제출 (프로덕션 사용 시)
9. "Settings" > "Basic"에서:
   - **App ID** 확인
   - **App Secret** 확인 (Show 클릭)
10. Instagram Business Account 연결:
    - "Instagram" > "Basic Display" 또는 "Graph API"
    - Instagram Business Account 연결
    - **Business Account ID** 확인

**필요한 권한**:
- `instagram_basic`
- `instagram_content_publish`
- `pages_show_list`
- `pages_read_engagement`

**비용**: 무료 (제한적)
**필수 여부**: 선택사항 (Instagram 자동 게시 시)

**주의사항**:
- Instagram Business Account 필요
- 앱 검수 과정이 필요할 수 있음
- 개발 모드에서는 제한된 사용자만 접근 가능

---

### LinkedIn API

**용도**: LinkedIn에 블로그 포스트 자동 게시

**발급 방법**:
1. https://www.linkedin.com/developers/apps 접속
2. LinkedIn 계정으로 로그인
3. "Create app" 클릭
4. 앱 정보 입력:
   - **App name**: QA-Blog-Automation
   - **LinkedIn Page**: (선택사항, 회사 페이지 연결)
   - **Privacy policy URL**: (필수)
   - **App logo**: (선택사항)
5. "Create app" 클릭
6. "Auth" 탭에서:
   - **Client ID** 확인
   - **Client Secret** 생성 (Generate 클릭)
7. OAuth 설정:
   - **Authorized redirect URLs** 추가: `http://localhost:8080`
8. 권한 요청:
   - "Products" 탭에서 필요한 제품 추가
   - "Sign In with LinkedIn using OpenID Connect" 추가
   - "Marketing Developer Platform" 추가 (게시용)
9. Access Token 생성:
   - OAuth 2.0 플로우를 통해 Access Token 획득
   - 또는 "Auth" 탭에서 직접 생성 (테스트용)

**Person URN 찾기**:
1. LinkedIn 프로필 페이지 접속
2. URL에서 숫자 부분 확인: `https://www.linkedin.com/in/username/`
3. 또는 API를 통해 확인: `https://api.linkedin.com/v2/me`
4. URN 형식: `urn:li:person:YOUR_PERSON_ID`

**필요한 권한**:
- `r_liteprofile`
- `r_emailaddress`
- `w_member_social` (게시용)

**비용**: 무료 (제한적)
**필수 여부**: 선택사항 (LinkedIn 자동 게시 시)

**주의사항**:
- 앱 검수 과정이 필요할 수 있음
- 일부 권한은 파트너 프로그램 가입 필요

---

### Twitter/X API v2

**용도**: Twitter/X에 블로그 포스트 자동 게시

**발급 방법**:
1. https://developer.twitter.com/en/portal/dashboard 접속
2. Twitter 계정으로 로그인
3. "Sign up for Free" 또는 기존 계정 사용
4. "Create Project" 클릭
5. 프로젝트 정보 입력:
   - **Project name**: QA-Blog-Automation
   - **Use case**: Making a bot
   - **Project description**: QA 블로그 자동 게시 봇
6. "Create App" 클릭
7. 앱 정보 입력:
   - **App name**: QA-Blog-Automation
   - **Environment**: Development 또는 Production
8. "Keys and tokens" 탭에서:
   - **API Key** 확인
   - **API Key Secret** 확인 (Reveal 클릭)
   - **Bearer Token** 생성 (Generate 클릭)
9. "User authentication settings" 설정:
   - **App permissions**: Read and Write
   - **Type of App**: Web App
   - **Callback URL**: `http://localhost:8080`
   - **Website URL**: (선택사항)
10. "Keys and tokens" > "Access Token and Secret" 생성:
    - **Access Token** 확인
    - **Access Token Secret** 확인

**필요한 권한**:
- Read and Write (게시용)

**비용**: 
- Free Tier: 제한적 (월 1,500 트윗)
- Basic: $100/월
- Pro: $5,000/월

**필수 여부**: 선택사항 (Twitter 자동 게시 시)

**주의사항**:
- API v2 사용 권장
- Rate limit 주의
- 트윗 정책 준수 필요

---

## API 키 보안 관리

### 1. 환경 변수 사용

**절대 코드에 직접 입력하지 마세요!**

`.env` 파일 사용:
```bash
# .env 파일 생성
cp env.example .env

# .env 파일 편집 (실제 키 값 입력)
# .env 파일은 git에 커밋하지 마세요!
```

### 2. .gitignore 설정

`.env` 파일이 git에 커밋되지 않도록 확인:
```gitignore
.env
.env.local
*.key
*.secret
```

### 3. 키 로테이션

정기적으로 API 키를 갱신하세요:
- 보안상의 이유로 3-6개월마다 갱신 권장
- 키 유출 시 즉시 재발급

### 4. 권한 최소화

필요한 최소한의 권한만 요청하세요:
- 소셜 미디어 API는 읽기/쓰기 권한만
- 불필요한 사용자 정보 접근 권한 요청 금지

### 5. 키 모니터링

API 키 사용량을 정기적으로 확인하세요:
- 각 플랫폼의 대시보드에서 사용량 확인
- 비정상적인 사용 패턴 감지

---

## API 키 우선순위

### 필수 (최소 1개 필요)
- **OpenAI API Key**: 기본 AI 생성

### 권장 (품질 향상)
- **Claude API Key**: 기술 분석 강화
- **Perplexity API Key**: 최신 정보 수집

### 선택사항 (기능 확장)
- **Gemini API Key**: 멀티모달 분석
- **Reddit API**: Reddit 수집
- **Stack Overflow API**: Stack Overflow 수집
- **Instagram API**: Instagram 자동 게시
- **LinkedIn API**: LinkedIn 자동 게시
- **Twitter API**: Twitter 자동 게시

---

## 문제 해결

### API 키가 작동하지 않는 경우

1. **키 형식 확인**: 공백이나 특수문자 포함 여부 확인
2. **권한 확인**: 필요한 권한이 모두 부여되었는지 확인
3. **Rate Limit**: API 사용량 한도 초과 여부 확인
4. **키 만료**: 키가 만료되었는지 확인
5. **환경 변수 로드**: `.env` 파일이 제대로 로드되는지 확인

### Rate Limit 오류

- API 호출 간격 조정
- 배치 처리로 요청 수 감소
- 더 높은 티어 구독 고려

### 인증 오류

- OAuth 토큰 갱신 필요 여부 확인
- 리다이렉트 URI 설정 확인
- 앱 검수 상태 확인 (소셜 미디어)

---

## 추가 리소스

- [OpenAI API 문서](https://platform.openai.com/docs)
- [Anthropic Claude API 문서](https://docs.anthropic.com/)
- [Perplexity API 문서](https://docs.perplexity.ai/)
- [Google Gemini API 문서](https://ai.google.dev/docs)
- [Instagram Graph API 문서](https://developers.facebook.com/docs/instagram-api/)
- [LinkedIn API 문서](https://learn.microsoft.com/en-us/linkedin/)
- [Twitter API v2 문서](https://developer.twitter.com/en/docs/twitter-api)

---

**마지막 업데이트**: 2025-01-27

