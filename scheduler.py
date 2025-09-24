import json
import os
import random
import time
import subprocess

def load_topics(file_path="topics.json"):
    """topics.json 파일에서 토픽 목록을 읽어옴"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("topics.json 파일을 찾을 수 없습니다.")
        return []
    except json.JSONDecodeError:
        print("topics.json 파일 형식이 잘못되었습니다.")
        return []

def save_topics(topics, file_path="topics.json"):
    """수정된 토픽 목록을 topics.json에 저장"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=4)

def run_article_generator(topic):
    """article_generator.py 실행 및 Git 명령어 수행"""
    # 가상환경 활성화 및 Python 명령어 실행    
    activate_cmd = "source venv/bin/activate "
    python_cmd = f"python article_generator.py \"{topic}\""
    git_cmd = " && git add . && git commit -m \"새 글 작성함\" && git push origin main"
    
    # 전체 명령어 조합
    full_cmd = activate_cmd + python_cmd + git_cmd
    
    # 명령어 실행 (인코딩을 utf-8로 설정하고 오류 대체 처리)
    result = subprocess.run(full_cmd, shell=True, text=True, executable = '/bin/bash', capture_output=True, encoding='utf-8', errors='replace')
    
    if result.returncode == 0:
        print(f"성공적으로 '{topic}'에 대한 글을 작성하고 푸시했습니다.")
        if result.stdout:  # 실행 결과 출력 (디버깅용)
            print("출력:", result.stdout)
    else:
        print(f"오류 발생: {result.stderr}")

def main():
    # topics.json에서 토픽 목록 로드
    topics = load_topics()
    
    # 토픽이 없을 때까지 반복
    while topics:
        # 랜덤으로 토픽 선택
        selected_topic = random.choice(topics)
        
        # 선택된 토픽 제거
        topics.remove(selected_topic)
        
        # 수정된 토픽 목록 저장
        save_topics(topics)
        
        # article_generator 실행 및 Git 작업 수행
        run_article_generator(selected_topic)
        
        # 토픽이 남아있다면 5초 대기
        if topics:
            print("5초 대기 중...")
            time.sleep(5)
    
    print("모든 토픽이 소진되었습니다. 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()