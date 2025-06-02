#!/bin/bash

# 간단한 게임 실행 스크립트 (환경이 이미 설정된 경우)

echo "🐍 진화 스네이크 게임 실행..."

# 가상환경이 있으면 활성화
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# 게임 실행
python3 main.py

# 가상환경 비활성화 (활성화되어 있었다면)
if [ -d "venv" ]; then
    deactivate
fi

echo "게임 종료" 