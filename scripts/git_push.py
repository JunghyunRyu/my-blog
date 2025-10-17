"""GitHub 자동 Push 스크립트

생성된 블로그 포스트를 자동으로 Git에 커밋하고 푸시합니다.

환경 변수:
----------
AUTO_GIT_PUSH : bool
    자동 푸시 활성화 여부 (기본값: true)
GIT_USER_NAME : str
    Git 커밋 사용자 이름 (기본값: GeekNews Bot)
GIT_USER_EMAIL : str
    Git 커밋 이메일 (기본값: bot@geeknews.local)
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List


def run_command(cmd: List[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    쉘 명령어를 실행합니다.
    
    Args:
        cmd: 실행할 명령어 리스트
        cwd: 작업 디렉토리
        check: 오류 발생 시 예외를 발생시킬지 여부
    
    Returns:
        subprocess.CompletedProcess 객체
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            encoding='utf-8'
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 명령어 실행 실패: {' '.join(cmd)}")
        print(f"   오류: {e.stderr}")
        raise


def setup_git_config(project_dir: Path) -> None:
    """
    Git 사용자 설정을 구성합니다.
    
    Args:
        project_dir: 프로젝트 디렉토리 경로
    """
    git_user_name = os.getenv("GIT_USER_NAME", "GeekNews Bot")
    git_user_email = os.getenv("GIT_USER_EMAIL", "bot@geeknews.local")
    
    # 기존 설정 확인
    try:
        result = run_command(["git", "config", "user.name"], cwd=project_dir, check=False)
        if not result.stdout.strip():
            run_command(["git", "config", "user.name", git_user_name], cwd=project_dir)
            print(f"✓ Git user.name 설정: {git_user_name}")
    except:
        run_command(["git", "config", "user.name", git_user_name], cwd=project_dir)
        print(f"✓ Git user.name 설정: {git_user_name}")
    
    try:
        result = run_command(["git", "config", "user.email"], cwd=project_dir, check=False)
        if not result.stdout.strip():
            run_command(["git", "config", "user.email", git_user_email], cwd=project_dir)
            print(f"✓ Git user.email 설정: {git_user_email}")
    except:
        run_command(["git", "config", "user.email", git_user_email], cwd=project_dir)
        print(f"✓ Git user.email 설정: {git_user_email}")


def check_git_status(project_dir: Path) -> bool:
    """
    Git 저장소 상태를 확인합니다.
    
    Args:
        project_dir: 프로젝트 디렉토리 경로
    
    Returns:
        변경사항이 있으면 True
    """
    result = run_command(["git", "status", "--porcelain"], cwd=project_dir)
    return bool(result.stdout.strip())


def auto_push_posts(created_files: List[Path], project_dir: Path | None = None) -> bool:
    """
    생성된 포스트 파일들을 Git에 커밋하고 푸시합니다.
    
    Args:
        created_files: 생성된 파일 경로 리스트
        project_dir: 프로젝트 디렉토리 (None이면 현재 디렉토리)
    
    Returns:
        성공하면 True, 실패하면 False
    """
    # 자동 푸시 비활성화 확인
    if os.getenv("AUTO_GIT_PUSH", "true").lower() not in ("true", "1", "yes"):
        print("ℹ️  자동 Git push가 비활성화되어 있습니다.")
        return False
    
    if not created_files:
        print("ℹ️  푸시할 파일이 없습니다.")
        return False
    
    # 프로젝트 디렉토리 결정
    if project_dir is None:
        project_dir = Path.cwd()
    
    print("\n" + "=" * 80)
    print("GitHub 자동 Push 시작")
    print("=" * 80)
    
    try:
        # Git 설정 확인
        setup_git_config(project_dir)
        
        # 변경사항 확인
        if not check_git_status(project_dir):
            print("ℹ️  변경사항이 없습니다.")
            return False
        
        # 파일 추가
        print("\n[1단계] 생성된 포스트 파일 추가 중...")
        for file_path in created_files:
            relative_path = file_path.relative_to(project_dir) if file_path.is_absolute() else file_path
            run_command(["git", "add", str(relative_path)], cwd=project_dir)
            print(f"  ✓ 추가됨: {relative_path}")
        
        # data/geeknews_state.json도 추가 (있는 경우)
        state_file = project_dir / "data" / "geeknews_state.json"
        if state_file.exists():
            run_command(["git", "add", "data/geeknews_state.json"], cwd=project_dir)
            print(f"  ✓ 추가됨: data/geeknews_state.json")
        
        # 커밋 메시지 생성
        print("\n[2단계] Git 커밋 생성 중...")
        now = datetime.now()
        post_count = len(created_files)
        
        # 첫 번째 포스트의 제목 추출 (간단하게)
        first_file = created_files[0]
        post_title = first_file.stem  # 파일명에서 제목 추출
        
        if post_count == 1:
            commit_message = f"Auto-post: {post_title} ({now:%Y-%m-%d %H:%M})"
        else:
            commit_message = f"Auto-post: {post_count}개 포스트 추가 ({now:%Y-%m-%d %H:%M})"
        
        run_command(["git", "commit", "-m", commit_message], cwd=project_dir)
        print(f"  ✓ 커밋 완료: {commit_message}")
        
        # 푸시
        print("\n[3단계] GitHub에 푸시 중...")
        
        # 현재 브랜치 확인
        result = run_command(["git", "branch", "--show-current"], cwd=project_dir)
        current_branch = result.stdout.strip() or "main"
        
        # 푸시 실행
        push_result = run_command(
            ["git", "push", "origin", current_branch],
            cwd=project_dir,
            check=False
        )
        
        if push_result.returncode == 0:
            print(f"  ✓ 푸시 완료: origin/{current_branch}")
            print("\n" + "=" * 80)
            print(f"✅ GitHub 자동 Push 성공! ({post_count}개 포스트)")
            print("=" * 80)
            return True
        else:
            print(f"  ⚠️  푸시 실패: {push_result.stderr}")
            print("\n" + "=" * 80)
            print("⚠️  커밋은 완료되었으나 푸시에 실패했습니다.")
            print("   수동으로 푸시를 실행하세요: git push origin " + current_branch)
            print("=" * 80)
            return False
    
    except Exception as exc:
        print(f"\n❌ Git 자동 푸시 중 오류 발생: {exc}")
        print("=" * 80)
        print("⚠️  자동 푸시에 실패했습니다.")
        print("   수동으로 커밋 및 푸시를 실행하세요:")
        print("     git add _posts/")
        print("     git commit -m 'Add new posts'")
        print("     git push")
        print("=" * 80)
        return False


def main():
    """테스트용 메인 함수"""
    print("Git Push 스크립트 테스트")
    print("=" * 80)
    
    project_dir = Path.cwd()
    
    # Git 설정 확인
    setup_git_config(project_dir)
    
    # Git 상태 확인
    has_changes = check_git_status(project_dir)
    print(f"\n변경사항 존재: {has_changes}")
    
    if has_changes:
        result = run_command(["git", "status", "--short"], cwd=project_dir)
        print("\n변경된 파일:")
        print(result.stdout)


if __name__ == "__main__":
    main()

