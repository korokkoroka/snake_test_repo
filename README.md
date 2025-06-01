##진화 스네이크 게임

현대적인 게임플레이 요소들이 추가된 스네이크 게임입니다.

게임 모드

1. 클래식 모드
- 기본적인 스네이크 게임플레이
- 대시 기능 추가 (스페이스바)
- 간단한 리드용 뱀
- 점수 시스템과 리더보드

2. 진화 모드
- 레벨업 시스템 (경험치 획득)
- 스탯 강화 시스템
- 진화 시스템
- 특수 아이템 생성성
- AI 적들과의 상호작용
- 에너지 관리 시스템

3. 보스전 모드
- 강력한 보스와의 전투
- 3단계 페이즈 시스템
  - 1페이즈: 기본 패턴 (5초마다 단일 투사체)
  - 2페이즈: 강화 패턴 (3초마다 2발 투사체)
  - 3페이즈: 최종 패턴 (원형 탄막 + 전체 공격)
- 투사체 회피 시스템
- 전체 공격 시스템
  - 경고음 재생
  - 안전 구역 생성 (화면 1/6 크기)
  - 구역 외 지속 데미지
- 보스 체력 시스템 (200 HP)

게임 특징

진화 시스템
- **레벨 5 진화**:
  - SPEEDER: 이동속도 증가, 대시 쿨다운 감소
  - TANK: 체력 증가, E키로 일회용 피해 면역 (20초 쿨다운)
  - HUNTER: 먹이 흡수 범위 3배 증가, 긴 대시 거리
- **레벨 10 진화**:
  - ULTIMATE: 모든 능력 획득, 무적 대시
  
  스탯 시스템
- 이동속도 (SPEED)
  - 레벨당 이동속도 20% 증가
- 에너지 관리 (ENERGY)
  - 레벨당 최대 에너지 20 증가
  - 에너지 소모량 15% 감소
- 레벨 2당 1개의 스탯 포인트 획득
- 최대 스탯 레벨: 5

특수 아이템 시스템
- 보호막 (SHIELD)
  - 일시적 무적 효과
  - 모든 피해 면역
- 속도 부스트 (SPEED_BOOST)
  - 이동속도 대폭 증가
  - 에너지 소모 감소
- 유령화 (GHOST)
  - 충돌 무시
  - 벽 통과 가능

에너지 시스템
- 기본 에너지: 100
- 대시 사용시 에너지 소모
- 에너지 부족시 행동 제한
- 자동 회복 시스템

AI 시스템
- 기본 AI 행동:
  - 먹이 추적
  - 충돌 회피
  - 생존 우선
- 고급 AI 기능 (개발 중):
  - 에너지 공유 시스템
  - 감정 시스템
  - 번식 시스템

조작 방법

기본 조작
- **방향키/WASD**: 이동
- **스페이스바**: 대시
  - 쿨다운: 10초
  - 지속시간: 4초
  - 에너지 소모: 초당 1
- **TAB**: 스탯 창 열기
- **E**: 탱크 면역 능력 (진화 모드/보스전)
- **ESC**: 게임 종료

스탯 창 조작
- **1**: 이동속도 강화
- **2**: 에너지 강화

💻 Developer's Guide

시스템 아키텍처

1. 코어 시스템 (module.py)
- **기본 클래스**
  ```python
  class Snake:
      # 뱀의 기본 동작 및 상태 관리
      # 진화, 스탯, 효과 시스템 포함
  
  class Food:
      # 기본 먹이 클래스
  
  class SpecialItem(Food):
      # 특수 아이템 클래스
      # 효과 시스템 연동
  ```

- **상수 및 설정**
  ```python
  # 게임 기본 설정
  WIDTH, HEIGHT = 1024, 768
  CELL_SIZE = 10
  
  # 게임 밸런스 상수
  SPAWN_PROTECTION_TIME = 45  # 3초
  DASH_DURATION = 60         # 4초
  DASH_COOLDOWN = 150       # 10초
  ```

2. 게임 모드별 구현 (main.py)

클래식 모드
```python
def game_loop(game_mode="CLASSIC"):
    # 기본 게임 로직
    # 대시 시스템
    # AI 적 생성 및 관리
    # 점수 시스템
```

진화 모드
```python
class EvolutionSystem:
    # 레벨업 시스템
    # 진화 트리 관리
    # 스탯 포인트 시스템

def handle_evolution(screen, player):
    # 진화 선택 UI
    # 능력치 변경
    # 이펙트 처리
```

보스전 모드
```python
class BossSnake(Snake):
    # 보스 AI 패턴
    # 페이즈 시스템
    # 투사체 관리
    # 전체 공격 시스템
```

코드 구조

1. 메인 게임 루프 (main.py)
```python
def main():
    # 게임 초기화
    # 모드 선택
    # 게임 루프 실행
    # 종료 처리
```

2. 이벤트 처리 시스템
```python
def handle_events():
    # 키보드 입력
    # 충돌 감지
    # UI 이벤트
```

3. 렌더링 시스템
```python
def draw_game_objects():
    # 게임 오브젝트 렌더링
    # UI 렌더링
    # 이펙트 렌더링
```

### 현재 미사용 코드 (초기 개발에 따른 시뮬레이션 모드 파일과 보스의 전체 공격 패턴 파일들이 섞여있음)

1. 전투 시스템 관련
```python
def fight(self, other):
    # 현재 사용되지 않는 전투 시스템
    # 공격력/방어력 기반 전투
    # 데미지 계산
```

2. AI 행동 패턴
```python
def share_energy(self, nearby_snakes):
    # 미구현된 에너지 공유 시스템
    
def store_extra_energy(self):
    # 사용되지 않는 에너지 저장 시스템
```

3. 보스 패턴
```python
def global_attack():
    # 비활성화된 전체 공격 시스템
    # 60초 주기 타이머
    # 데미지 존 생성
```

모드별 파일 구조

1. 클래식 모드
- **main.py**
  - `mode_select_screen()`
  - `game_loop("CLASSIC")`
  - `handle_classic_events()`
- **module.py**
  - `Snake` 클래스 기본 기능
  - `spawn_food()`
  - `handle_collisions()`

2. 진화 모드
- **main.py**
  - `game_loop("EVOLUTION")`
  - `draw_evolution_ui()`
  - `handle_evolution()`
- **module.py**
  - `Snake` 클래스 진화 관련 메서드
  - `EVOLUTION_FORMS` 상수
  - `SpecialItem` 클래스

3. 보스전 모드
- **main.py**
  - `game_loop("BOSS")`
  - `draw_boss_ui()`
  - `handle_boss_events()`
- **module.py**
  - `BossSnake` 클래스
  - `BOSS_PATTERNS` 상수
  - `handle_boss_collision()`
``'