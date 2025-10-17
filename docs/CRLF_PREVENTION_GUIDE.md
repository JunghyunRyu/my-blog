# CRLF 이슈 방지 가이드

## 개요

이 문서는 Windows 환경에서 Git을 사용할 때 발생하는 CRLF(줄바꿈) 이슈를 방지하기 위한 가이드입니다.

## 문제 상황

Windows에서는 줄바꿈을 `\r\n` (CRLF)로 표현하고, Unix/Linux에서는 `\n` (LF)로 표현합니다. 이 차이로 인해 Git에서 다음과 같은 경고가 발생할 수 있습니다:

```
warning: in the working copy of 'filename', CRLF will be replaced by LF the next time Git touches it
```

## 해결 방법

### 1. Git 설정 최적화

다음 명령어들을 실행하여 Git 설정을 최적화하세요:

```bash
# Windows에서 자동 줄바꿈 변환 활성화
git config --global core.autocrlf true

# 줄바꿈 변환 시 안전성 검사 활성화
git config --global core.safecrlf true

# 기본 줄바꿈 문자를 LF로 설정
git config --global core.eol lf
```

### 2. .gitattributes 파일 활용

프로젝트 루트에 `.gitattributes` 파일이 생성되어 있습니다. 이 파일은 각 파일 타입별로 줄바꿈 규칙을 명시합니다:

- **텍스트 파일**: LF 사용 (Unix 스타일)
- **Windows 배치 파일**: CRLF 사용
- **PowerShell 스크립트**: CRLF 사용
- **바이너리 파일**: 줄바꿈 변환 안 함

### 3. .editorconfig 설정

`.editorconfig` 파일이 프로젝트에 포함되어 있어 에디터가 자동으로 올바른 줄바꿈을 사용하도록 합니다.

## 권장사항

### 개발자별 설정

#### Windows 개발자
```bash
git config --global core.autocrlf true
git config --global core.safecrlf true
```

#### Mac/Linux 개발자
```bash
git config --global core.autocrlf input
git config --global core.safecrlf true
```

### 에디터 설정

#### Visual Studio Code
- `files.eol` 설정을 `\n` (LF)로 설정
- `.editorconfig` 확장 프로그램 설치 권장

#### IntelliJ IDEA
- Settings → Editor → Code Style → Line separator를 "Unix and macOS (\n)"로 설정

## 문제 해결

### 기존 파일의 줄바꿈 정규화

모든 파일의 줄바꿈을 정규화하려면:

```bash
# 모든 파일을 다시 체크아웃하여 줄바꿈 정규화
git rm --cached -r .
git reset --hard
```

### 특정 파일의 줄바꿈 확인

```bash
# 파일의 줄바꿈 타입 확인
file filename.txt

# 또는 PowerShell에서
Get-Content filename.txt -Raw | ForEach-Object { $_.Length - $_.Replace("`n", "").Length }
```

## 예방 조치

1. **새 프로젝트 시작 시**: `.gitattributes` 파일을 먼저 생성
2. **팀 협업 시**: 모든 팀원이 동일한 Git 설정 사용
3. **CI/CD 파이프라인**: 줄바꿈 검사 단계 추가 고려

## 참고 자료

- [Git 공식 문서 - 줄바꿈 처리](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration#_core_autocrlf)
- [EditorConfig 공식 사이트](https://editorconfig.org/)
- [Git Attributes 문서](https://git-scm.com/docs/gitattributes)

## 문제 발생 시 연락처

CRLF 관련 문제가 지속적으로 발생하는 경우, 프로젝트 관리자에게 문의하세요.
