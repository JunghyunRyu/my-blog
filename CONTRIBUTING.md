# 기여 가이드

GeekNews 자동화 블로그 시스템에 기여해주셔서 감사합니다! 🎉

## 📋 목차

- [행동 강령](#행동-강령)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일](#코드-스타일)
- [커밋 메시지 규칙](#커밋-메시지-규칙)
- [Pull Request 프로세스](#pull-request-프로세스)
- [버그 리포트](#버그-리포트)
- [기능 제안](#기능-제안)

---

## 행동 강령

### 우리의 약속

우리는 개방적이고 환영하는 환경을 조성하기 위해 노력합니다. 모든 기여자들을 존중하며, 차별 없는 참여를 보장합니다.

### 기대되는 행동

- 친절하고 포용적인 언어 사용
- 다른 관점과 경험 존중
- 건설적인 비판 수용
- 커뮤니티에 긍정적인 영향

---

## 기여 방법

### 1. 이슈 생성

버그를 발견하거나 새로운 기능을 제안하고 싶다면:

```bash
# GitHub Issues에서:
# 1. 검색하여 중복 이슈 확인
# 2. 새 이슈 생성
# 3. 템플릿에 따라 작성
```

### 2. 코드 기여

```bash
# 1. Fork 저장소
# GitHub에서 Fork 버튼 클릭

# 2. Clone
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli

# 3. 새 브랜치 생성
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/bug-description

# 4. 개발 환경 설정
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# 5. 코드 수정
# ... 작업 ...

# 6. 테스트
python scripts/health_check.py
python scripts/run_once.py --max-posts 1

# 7. 커밋
git add .
git commit -m "feat: add amazing feature"

# 8. Push
git push origin feature/your-feature-name

# 9. Pull Request 생성
# GitHub에서 Pull Request 생성
```

---

## 개발 환경 설정

### 필수 요구사항

- Python 3.11+
- Git
- OpenAI API Key (테스트용)

### 설정 단계

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/my-blog-cli.git
cd my-blog-cli

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp env.example .env
# .env 파일 편집:
# OPENAI_API_KEY=your-test-key
# ENABLE_MCP=false  # 로컬 개발 시
# AUTO_GIT_PUSH=false  # 테스트 시

# 5. 테스트 실행
python scripts/health_check.py
```

---

## 코드 스타일

### Python 코드 스타일

프로젝트는 **PEP 8** 스타일 가이드를 따릅니다.

```python
# ✅ 좋은 예
def generate_content(item: dict, depth: int = 3) -> dict:
    """
    QA 콘텐츠를 생성합니다.
    
    Args:
        item: 기사 정보
        depth: 분석 깊이
    
    Returns:
        생성된 콘텐츠
    """
    result = mcp_client.think(item['title'], depth=depth)
    return process_result(result)

# ❌ 나쁜 예
def gen(i,d=3):
    r=mcp.think(i['title'],depth=d)
    return proc(r)
```

### 네이밍 규칙

```python
# 변수/함수: snake_case
user_name = "John"
def calculate_score(): pass

# 클래스: PascalCase
class QAContentGenerator: pass

# 상수: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT = 30

# 비공개: _prefix
def _internal_method(): pass
```

### 타입 힌팅

```python
from typing import Dict, List, Optional

def process_items(
    items: List[Dict[str, str]], 
    max_count: Optional[int] = None
) -> List[str]:
    """타입 힌팅을 항상 사용하세요."""
    pass
```

### Docstring

```python
def function_name(param1: str, param2: int) -> bool:
    """
    함수의 간단한 설명 (한 줄).
    
    더 자세한 설명이 필요하면 여기에 작성합니다.
    여러 줄로 작성할 수 있습니다.
    
    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명
    
    Returns:
        반환값 설명
    
    Raises:
        ValueError: 값이 잘못된 경우
        IOError: 파일 읽기 실패 시
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

---

## 커밋 메시지 규칙

**Conventional Commits** 형식을 따릅니다.

### 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

### 예시

```bash
# 기능 추가
git commit -m "feat(mcp): add multi-model support"

# 버그 수정
git commit -m "fix(git): resolve push authentication error"

# 문서 업데이트
git commit -m "docs(readme): update installation guide"

# 리팩토링
git commit -m "refactor(pipeline): simplify error handling"
```

### 세부 사항

```bash
git commit -m "feat(mcp): add sequential thinking depth configuration

Allow users to configure MCP thinking depth via environment variable.
This enables finer control over analysis quality vs performance.

Closes #42"
```

---

## Pull Request 프로세스

### 1. PR 생성 전 체크리스트

- [ ] 코드가 스타일 가이드를 따르는가?
- [ ] 모든 테스트가 통과하는가?
- [ ] 새로운 기능에 테스트를 추가했는가?
- [ ] 문서를 업데이트했는가? (README, docs/)
- [ ] 커밋 메시지가 규칙을 따르는가?
- [ ] `.gitignore`에 민감한 정보가 없는가?

### 2. PR 템플릿

```markdown
## 설명
이 PR이 해결하는 문제나 추가하는 기능을 설명하세요.

## 변경 사항
- 변경 1
- 변경 2
- 변경 3

## 테스트 방법
1. 단계 1
2. 단계 2
3. 결과 확인

## 스크린샷 (필요시)
![screenshot](url)

## 관련 이슈
Closes #이슈번호
```

### 3. 리뷰 프로세스

1. **자동 검사**: CI/CD 통과 확인
2. **코드 리뷰**: 최소 1명의 승인 필요
3. **테스트**: 기능 동작 확인
4. **병합**: Squash and merge 권장

---

## 버그 리포트

### 버그 리포트 템플릿

```markdown
## 버그 설명
명확하고 간결한 버그 설명

## 재현 방법
1. '...'로 이동
2. '...'를 클릭
3. '...'를 스크롤
4. 오류 발생

## 예상 동작
무엇이 일어나야 하는지 설명

## 실제 동작
실제로 무엇이 일어났는지 설명

## 스크린샷
가능하면 스크린샷 첨부

## 환경
- OS: [e.g. Ubuntu 22.04]
- Python 버전: [e.g. 3.11]
- 브라우저: [e.g. Chrome 120]

## 추가 정보
로그, 에러 메시지 등
```

### 버그 리포트 시 포함할 정보

```bash
# Python 버전
python --version

# 패키지 버전
pip list

# 환경 변수 (민감한 정보 제외)
cat .env | grep -v "API_KEY"

# 에러 로그
tail -n 50 logs/error.log
```

---

## 기능 제안

### 기능 제안 템플릿

```markdown
## 기능 설명
원하는 기능을 명확하게 설명

## 해결하려는 문제
이 기능이 어떤 문제를 해결하는지 설명

## 제안하는 솔루션
기능이 어떻게 작동해야 하는지 설명

## 대안
고려한 다른 대안들

## 추가 정보
스크린샷, 참고 링크 등
```

---

## 우선순위

### High Priority

- 보안 취약점
- 데이터 손실 버그
- 시스템 크래시

### Medium Priority

- 기능 버그
- 성능 개선
- 새로운 기능

### Low Priority

- 문서 개선
- 코드 정리
- 사소한 UI 개선

---

## 테스트 가이드

### 단위 테스트

```bash
# pytest 실행
pytest tests/

# 특정 테스트
pytest tests/test_mcp_client.py

# 커버리지
pytest --cov=automation tests/
```

### 통합 테스트

```bash
# 전체 파이프라인 테스트
python scripts/run_once.py --max-posts 1

# MCP 통합 테스트
python -c "
from automation.mcp_client import create_mcp_client
client = create_mcp_client()
if client:
    result = client.think('test problem')
    print(result)
"
```

---

## 릴리스 프로세스

### 버전 관리

Semantic Versioning (SemVer) 사용:

- `MAJOR.MINOR.PATCH`
- 예: `1.2.3`

**MAJOR**: 호환성이 깨지는 변경  
**MINOR**: 새로운 기능 추가 (하위 호환)  
**PATCH**: 버그 수정

### 릴리스 체크리스트

- [ ] CHANGELOG.md 업데이트
- [ ] 버전 번호 업데이트
- [ ] 모든 테스트 통과
- [ ] 문서 업데이트
- [ ] Git 태그 생성
- [ ] GitHub Release 생성

---

## 연락처

질문이나 제안이 있으시면:

- **GitHub Issues**: 버그 리포트, 기능 제안
- **GitHub Discussions**: 일반 토론, Q&A
- **Email**: your-email@example.com

---

## 라이선스

기여하신 코드는 프로젝트의 MIT 라이선스에 따라 배포됩니다.

---

**다시 한번 기여해주셔서 감사합니다! 🙏**

여러분의 기여가 이 프로젝트를 더 좋게 만듭니다.

