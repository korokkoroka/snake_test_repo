#!/bin/bash

# 진화 스네이크 게임 실행 스크립트
# 자동으로 환경을 설정하고 게임을 실행합니다

echo "🐍 진화 스네이크 게임 실행 중..."
echo "============================================"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 파이썬 설치 확인
echo -e "${BLUE}파이썬 설치 확인 중...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3가 설치되어 있지 않습니다.${NC}"
    echo "Python3를 먼저 설치해주세요: https://www.python.org/downloads/"
    exit 1
fi

python_version=$(python3 --version 2>&1)
echo -e "${GREEN}✅ $python_version 발견${NC}"

# pip 설치 확인
echo -e "${BLUE}pip 설치 확인 중...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3가 설치되어 있지 않습니다.${NC}"
    echo "pip3를 먼저 설치해주세요."
    exit 1
fi
echo -e "${GREEN}✅ pip3 설치 확인 완료${NC}"

# 가상환경 생성 및 활성화 (선택사항)
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 가상환경 생성 중...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
fi

echo -e "${YELLOW}🔧 가상환경 활성화 중...${NC}"
source venv/bin/activate

# 의존성 설치
echo -e "${BLUE}📥 필요한 패키지 설치 중...${NC}"
pip install -r requirements.txt

# 설치 결과 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 패키지 설치 완료${NC}"
else
    echo -e "${RED}❌ 패키지 설치 중 오류 발생${NC}"
    exit 1
fi

# 게임 실행
echo ""
echo -e "${GREEN}🎮 게임 시작!${NC}"
echo "============================================"
echo "게임 조작법:"
echo "• 방향키/WASD: 이동"
echo "• 스페이스바: 대시"
echo "• TAB: 스탯 창"
echo "• E: 탱크 면역 능력"
echo "• ESC: 종료"
echo "============================================"
echo ""

# 게임 실행
python3 main.py

# 게임 종료 후 가상환경 비활성화
deactivate

echo ""
echo -e "${BLUE}🎮 게임이 종료되었습니다. 감사합니다!${NC}" 