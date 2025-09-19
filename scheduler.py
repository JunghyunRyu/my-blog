import json
import random
import subprocess
import time
import os

def load_topics(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("topics.json 파일을 찾을 수 없습니다.")
        return {"topics": []}
    except json.JSONDecodeError:
        print("topics.json 파일 형식이 올바르지 않습니다.")
        return {"topics": []}

def save_topics(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_random_topic(topics_data):
    all_items = []
    for category in topics_data['topics']:
        if 'items' in category and category['items']:
            all_items.extend(category['items'])
    
    if not all_items:
        return None
    
    return random.choice(all_items)

def remove_topic(topics_data, selected_topic):
    for category in topics_data['topics']:
        if 'items' in category and selected_topic in category['items']:
            category['items'].remove(selected_topic)
            break
    return topics_data

def run_article_generator(topic):
    try:
        # Activate virtual environment and run article_generator.py
        activate_cmd = '.\\venv\\Scripts\\activate' if os.name == 'nt' else 'source ./venv/bin/activate'
        cmd = f'{activate_cmd} && python article_generator.py "{topic}"'
        subprocess.run(cmd, shell=True, check=True)
        
        # Git operations
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', '새 글 작성함'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print(f"Successfully processed topic: {topic}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing topic {topic}: {e}")

def main():
    topics_file = 'topics.json'
    
    while True:
        # Load topics
        topics_data = load_topics(topics_file)
        
        # Get random topic
        selected_topic = get_random_topic(topics_data)
        
        if not selected_topic:
            print("더 이상 처리할 토픽이 없습니다.")
            break
            
        # Remove selected topic and save
        topics_data = remove_topic(topics_data, selected_topic)
        save_topics(topics_file, topics_data)
        
        # Process topic
        print(f"Processing topic: {selected_topic}")
        run_article_generator(selected_topic)
        
        # Wait 5 seconds
        print("Waiting for 5 seconds...")
        time.sleep(5)  # 5 seconds in seconds

if __name__ == "__main__":
    main()