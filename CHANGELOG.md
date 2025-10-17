# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- MCP Sequential Thinking 통합
- GitHub 자동 Push 기능
- EC2 배포 자동화 스크립트
- 포괄적인 `.gitignore` 설정
- 완전한 `README.md` 문서
- `CONTRIBUTING.md` 기여 가이드
- `LICENSE` (MIT)
- `docs/EC2_DEPLOYMENT_GUIDE.md` 배포 가이드
- MCP 클라이언트 모듈 (`automation/mcp_client.py`)
- Git 자동 푸시 스크립트 (`scripts/git_push.py`)
- 헬스체크 확장 (Node.js, MCP, Git 설정)
- systemd 서비스 파일 (MCP 서버용)

### Changed
- QA Generator에 MCP 인사이트 통합
- 파이프라인에 Git push 단계 추가
- `env.example`에 MCP 및 Git 설정 추가
- `requirements.txt`에 MCP 의존성 추가 (httpx, anyio)
- `deploy/setup_ec2.sh`에 Node.js 및 MCP 설치 추가
- `deploy/deploy.sh`에 MCP 서버 상태 체크 추가

### Fixed
- 로그 파일 Git 제외 (`nohup.out` 삭제)
- Python 캐시 파일 Git 제외
- 민감한 정보 Git 제외 강화

---

## [1.0.0] - 2025-10-17

### Added
- 초기 프로젝트 구조
- GeekNews RSS 피드 수집
- OpenAI 기반 QA 콘텐츠 생성
- 웹 연구 통합 (DuckDuckGo)
- Jekyll 블로그 포스트 자동 생성
- 콘텐츠 필터링 및 우선순위 지정
- 로컬 실행 스크립트
- EC2 배포 기본 설정

### Features
- **AI 기반 분석**: OpenAI GPT-4o-mini로 전문가급 QA 콘텐츠 생성
- **웹 연구**: DuckDuckGo 검색으로 추가 정보 수집
- **자동화**: RSS → 분석 → 생성 → 포스트 작성
- **필터링**: AI 관련 항목 우선, 투표수 기반 우선순위
- **카테고리**: Learning, QA Engineer, Daily Life 자동 분류

---

## Migration Notes

### v1.0.0 → v2.0.0 (Unreleased)

**Breaking Changes:**
- MCP 서버 필요 (선택적, `ENABLE_MCP=false`로 비활성화 가능)
- Node.js 18 LTS 필요 (MCP 사용 시)
- 새로운 환경 변수 추가 (`ENABLE_MCP`, `MCP_SERVER_URL`, etc.)

**Migration Steps:**
1. `.env` 파일 업데이트 (`.env.example` 참고)
2. Node.js 18 설치 (MCP 사용 시)
3. `requirements.txt` 재설치: `pip install -r requirements.txt`
4. GitHub 인증 설정 (자동 Push 사용 시)

**New Features:**
- MCP Sequential Thinking으로 더 깊이 있는 분석
- GitHub 자동 커밋 및 푸시
- EC2 완전 자동 배포
- systemd 서비스 자동 관리

---

## Development Timeline

### 2025-10-17
- ✅ MCP 통합 완료
- ✅ GitHub 자동화 완료
- ✅ EC2 배포 스크립트 완료
- ✅ 문서 정비 완료
- ✅ Git 저장소 정리 완료

### Future Plans
- [ ] 멀티 MCP 서버 통합 (Memory, RAG)
- [ ] A/B 테스트 프레임워크
- [ ] 콘텐츠 품질 메트릭
- [ ] 멀티 모델 지원 (Claude, Gemini)
- [ ] 자동 SEO 최적화
- [ ] 인터랙티브 블로그 기능

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-10-17 | 초기 릴리스 (OpenAI 기반) |
| 2.0.0 | TBD | MCP 통합 및 자동화 강화 |

---

## Links

- [GitHub Repository](https://github.com/your-username/my-blog-cli)
- [Issues](https://github.com/your-username/my-blog-cli/issues)
- [Releases](https://github.com/your-username/my-blog-cli/releases)
- [Documentation](./docs/)

---

**Note:** 이 CHANGELOG는 [Keep a Changelog](https://keepachangelog.com/) 형식을 따릅니다.

