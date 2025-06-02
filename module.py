"""
Snake Game - 모듈 파일
게임의 핵심 로직과 클래스들을 포함하는 모듈
"""

import pygame
import random
import math
import json
from datetime import datetime
from font_manager import get_font_manager

#############################################
# 공통 상수 (모든 모드에서 사용)
#############################################
# 게임 화면 설정
WIDTH, HEIGHT = 1024, 768
CELL_SIZE = 10
LEADERBOARD_FILE = "leaderboard.json"

# 기본 색상 정의
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
PURPLE = (147, 0, 211)
GOLD = (255, 215, 0)

# 기본 게임 상수
SPAWN_PROTECTION_TIME = 45  # 3초간 스폰 보호 (15fps 기준)
SPAWN_AREA_PADDING = 100   # 화면 가장자리로부터의 여유 공간
SAFE_SPAWN_DISTANCE = 150  # 다른 뱀으로부터의 최소 안전 거리
DASH_DURATION = 60      # 4초 (15fps * 4)
DASH_COOLDOWN = 150     # 10초
DASH_ENERGY_COST = 1    # 초당 에너지 소모량

#############################################
# 진화 모드 상수
#############################################
# 스탯 시스템
MAX_STAT_LEVEL = 5
STAT_COSTS = {
    "SPEED": 1,
    "ENERGY": 1
}

# 진화 형태 정의
EVOLUTION_FORMS = {
    "NORMAL": {
        "color": GREEN,
        "abilities": [],
        "description": "기본 형태"
    },
    "SPEEDER": {
        "color": BLUE,
        "abilities": ["빠른 이동", "대시 쿨다운 감소"],
        "description": "빠른 이동 특화"
    },
    "TANK": {
        "color": RED,
        "abilities": ["체력 증가", "E키: 일회용 피해 면역 (20초 쿨다운)"],
        "description": "생존력 특화"
    },
    "HUNTER": {
        "color": PURPLE,
        "abilities": ["먹이 흡수 범위 3배", "긴 대시"],
        "description": "사냥 특화"
    },
    "ULTIMATE": {
        "color": GOLD,
        "abilities": ["모든 능력", "무적 대시"],
        "description": "완전진화 형태"
    }
}

# 특수 아이템 정의
SPECIAL_ITEMS = {
    "SHIELD": {
        "color": (0, 191, 255),  # 하늘색
        "duration": 45,  # 3초
        "effect": "피해 면역",
        "name": "쉴드"  # 한글 이름 추가
    },
    "SPEED_BOOST": {
        "color": (255, 215, 0),  # 골드
        "duration": 30,  # 2초
        "effect": "이동속도 2배 증가",
        "name": "스피드 부스트"
    },
    "GHOST": {
        "color": (169, 169, 169),  # 회색
        "duration": 15,  # 1초
        "effect": "다른 뱀 통과 가능",
        "name": "유령화"  # 한글 이름 추가
    }
}

#############################################
# 시뮬레이션 모드 상수
#############################################
# AI 행동 관련
PLAYER_DETECTION_RANGE = 150  # 플레이어 감지 범위
CHASE_ENERGY_THRESHOLD = 40   # 추적 시작을 위한 최소 에너지
RETREAT_ENERGY_THRESHOLD = 30  # 후퇴를 위한 에너지 임계값
CHASE_DURATION = 100          # 추적 지속 시간 (틱)

# 시뮬레이션 물리
MAX_SPEED = 2.5
MAX_FORCE = 0.1
VISION_RANGE = 150
VISION_ANGLE = 120

# 감정 상태 정의
EMOTIONS = {
    "NORMAL": {
        "color": WHITE,
        "energy_consume": 1.0,
        "speed_multiplier": 1.0,
        "duration": 0
    },
    "CALM": {
        "color": GREEN,
        "energy_consume": 0.8,
        "speed_multiplier": 0.8,
        "duration": 300
    },
    "EXCITED": {
        "color": YELLOW,
        "energy_consume": 1.2,
        "speed_multiplier": 1.2,
        "duration": 200
    },
    "ANGRY": {
        "color": RED,
        "energy_consume": 1.5,
        "speed_multiplier": 1.5,
        "duration": 150
    }
}

#############################################
# 기본 클래스 (모든 모드에서 사용)
#############################################
class Food:
    """기본 음식 클래스"""
    def __init__(self, x, y, is_item=False):
        self.x = float(x)
        self.y = float(y)
        self.is_item = is_item

    def get_pos(self):
        return int(self.x), int(self.y)

class Snake:
    """뱀 기본 클래스"""
    def __init__(self, x, y, color=GREEN, is_ai=False, name="Player"):
        # 기본 속성
        self.body = [[x, y], [x - CELL_SIZE, y], [x - 2 * CELL_SIZE, y]]
        self.direction = 'RIGHT'
        self.color = color
        self.is_ai = is_ai
        self.name = name
        self.alive = True
        self.score = 0
        
        # 에너지 시스템
        self.energy = 100.0
        self.boost = 1
        self.grow = False
        
        # 대시 시스템
        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_duration = 0
        self.invincible_time = 0
        self.collision_immune = False
        
        # Tank 능력 시스템
        self.tank_immunity_cooldown = 0
        self.tank_immunity_active = False
        self.tank_immunity_used = False  # 일회용 면역 사용 여부
        
        # 스폰 보호
        self.spawn_protection_time = SPAWN_PROTECTION_TIME if is_ai else 0
        
        # 회복 시스템
        self.recovery_timer = None
        
        # 번식 시스템
        self.breed_cooldown = 0
        
        # 감정 시스템
        self.emotion = "NORMAL"
        self.emotion_timer = 0
        
        # 효과 시스템
        self.active_effects = {
            "SHIELD": 0,
            "SPEED_BOOST": 0,
            "GHOST": 0,
            "INVINCIBLE": 0,
            "STUN": 0
        }
        
        # 스탯 시스템
        self.stats = {
            "SPEED": 1,
            "ENERGY": 1
        }
        
        # 경험치 시스템
        self.level = 1
        self.exp = 0
        self.exp_to_level = 100
        self.evolution_form = "NORMAL"
        self.evolution_points = 0
        self.stat_points = 0
        
        # 진화 모드 속성
        if not is_ai:
            self.init_evolution_attributes()
        
        # AI 속성
        if is_ai:
            self.init_ai_attributes()
            
        # 메시지 시스템 추가
        self.message = None
        self.message_duration = 0

    def init_evolution_attributes(self):
        """진화 모드 속성 초기화"""
        # 특수 효과 초기화
        self.active_effects = {
            "SHIELD": 0,
            "SPEED_BOOST": 0,
            "GHOST": 0
        }

    def init_ai_attributes(self):
        """AI 속성 초기화"""
        self.chase_timer = 0
        self.is_chasing = False
        self.target_player = None
        self.last_player_pos = None
        self.chase_cooldown = 0
        self.food_detection_range = 50

    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp -= self.exp_to_level
        self.exp_to_level = int(self.exp_to_level * 1.5)
        self.evolution_points += 1
        # 2레벨당 1개의 스탯 포인트 획득
        if self.level % 2 == 0:
            self.stat_points += 1
        return self.level

    def can_evolve(self):
        if self.level >= 10 and self.evolution_form != "Max_Level":
            return True
        if self.level >= 5 and self.evolution_form == "NORMAL":
            return True
        return False

    def evolve(self, new_form):
        if new_form in EVOLUTION_FORMS:
            self.evolution_form = new_form
            self.color = EVOLUTION_FORMS[new_form]["color"]
            
            # 진화 형태별 특수 능력 적용
            if new_form == "SPEEDER":
                self.dash_cooldown = max(0, self.dash_cooldown - 15)
            elif new_form == "TANK":
                self.energy = min(200, self.energy + 50)
                self.collision_immune = True
            elif new_form == "HUNTER":
                self.food_detection_range = 150
            elif new_form == "ULTIMATE":
                self.collision_immune = True
                self.food_detection_range = 200
                self.dash_cooldown = 0

    def get_head(self):
        return self.body[0]

    def update_emotion_state(self, snakes):
        if not self.alive:
            return

        # 에너지 기반 기본 감정 상태
        if self.energy < 20:
            self.emotion = "TIRED"
        elif self.energy > 80:
            self.emotion = "HAPPY"
        else:
            self.emotion = "CALM"

        # 주변 상황 기반 감정 변화
        nearby_snakes = self.get_nearby_snakes(snakes, 100)
        
        # 위험 감지
        for snake in nearby_snakes:
            if snake != self and snake.is_ai and snake.aggression > 1.0:
                distance = math.hypot(self.get_head()[0] - snake.get_head()[0],
                                   self.get_head()[1] - snake.get_head()[1])
                if distance < 50:  # 매우 가까운 거리
                    self.emotion = "SCARED"
                    break

        # 사냥 상태
        if self.is_dashing and self.energy > 50:
            self.emotion = "HUNTING"

        # 감정에 따른 속도와 에너지 소모 조정
        emotion_data = EMOTIONS[self.emotion]
        self.move_delay = int(5 / emotion_data["speed_multiplier"])
        
    def get_nearby_snakes(self, snakes, radius):
        nearby = []
        head_x, head_y = self.get_head()
        for snake in snakes:
            if snake != self and snake.alive:
                other_x, other_y = snake.get_head()
                distance = math.hypot(head_x - other_x, head_y - other_y)
                if distance < radius:
                    nearby.append(snake)
        return nearby

    def fight(self, other):
        """전투 시스템"""
        if not self.alive or not other.alive:
            return
            
        # 내가 먼저 공격
        damage = self.strength * (1.5 if self.is_dashing else 1.0)
        other.energy -= damage
        
        if other.energy <= 0:
            other.alive = False
            self.score += 50
            self.add_exp(300)
            # 승리 시 회복 시작
            if self.alive:
                self.recovery_timer = 3.0
            return
            
        # 상대 반격
        if other.alive:
            counter_damage = other.strength * (1.5 if other.is_dashing else 1.0)
            self.energy -= counter_damage
            
            if self.energy <= 0:
                self.alive = False
                other.score += 50
                other.add_exp(300)
                # 승리한 상대 회복 시작
                if other.alive:
                    other.recovery_timer = 3.0

    def share_energy(self, nearby_snakes):
        """에너지 공유 시스템"""
        if self.stored_energy <= 0 or self.altruism < 5:
            return
            
        # 가장 에너지가 낮은 아군 찾기
        target = None
        min_energy = float('inf')
        for snake in nearby_snakes:
            if snake != self and snake.alive and snake.energy < min_energy:
                min_energy = snake.energy
                target = snake
                
        if target and target.energy < 70:
            share_amount = min(self.stored_energy, 20)
            target.energy += share_amount
            self.stored_energy -= share_amount
            self.energy_given_count += 1
            target.energy_received_count += 1

    def store_extra_energy(self):
        """여분의 에너지 저장"""
        if self.energy > 120:
            extra = self.energy - 120
            self.energy = 120
            self.stored_energy += extra * 0.5  # 50% 효율로 저장

    def update_recovery(self):
        """회복 시스템"""
        if self.recovery_timer is not None:
            self.recovery_timer -= 1
            if self.recovery_timer <= 0:
                self.recovery_timer = None
                heal_amount = 30
                self.energy = min(150, self.energy + heal_amount)

    def try_breed(self, snakes):
        """번식 시도"""
        if not self.alive or self.gender != "F":
            return
            
        if self.birth_count >= self.max_births:
            return
            
        if self.energy < self.breed_energy_threshold or self.breed_cooldown > 0:
            return
            
        # 근처에 수컷이 있는지 확인
        nearby_male = None
        for snake in snakes:
            if (snake != self and snake.alive and snake.gender == "M" and
                math.hypot(snake.get_head()[0] - self.get_head()[0],
                          snake.get_head()[1] - self.get_head()[1]) < 50):
                nearby_male = snake
                break
                
        if nearby_male:
            # 새로운 AI 스네이크 생성
            self.energy -= 30
            nearby_male.energy -= 20
            self.breed_cooldown = 130
            nearby_male.breed_cooldown = 130
            self.birth_count += 1
            
            # 새 개체 생성
            new_x = (self.get_head()[0] + nearby_male.get_head()[0]) // 2
            new_y = (self.get_head()[1] + nearby_male.get_head()[1]) // 2
            new_snake = Snake(new_x, new_y, color=self.color, is_ai=True)
            snakes.append(new_snake)

    def move(self, food_list, snakes, tick_count, simulation_mode=False):
        """뱀 이동 처리"""
        # 스폰 보호 시간 처리
        if hasattr(self, 'spawn_protection_time') and self.spawn_protection_time > 0:
            self.spawn_protection_time -= 1
            self.collision_immune = True
        elif self.invincible_time > 0:
            self.invincible_time -= 1
            self.collision_immune = True
        else:
            # Tank 형태의 면역 상태 처리
            if self.evolution_form == "TANK":
                if self.tank_immunity_active:
                    self.collision_immune = True
                else:
                    self.collision_immune = False
            else:
                # 다른 형태의 면역 처리 (쉴드 효과나 Ultimate 형태)
                self.collision_immune = (self.evolution_form == "ULTIMATE" or 
                                       self.active_effects["SHIELD"] > 0 or 
                                       self.stats["ENERGY"] >= MAX_STAT_LEVEL)

        # 대시 상태 업데이트
        if self.is_dashing:
            self.dash_duration -= 1
            # 보스전일 때 대시 에너지 소모 절반으로 감소
            dash_energy_cost = DASH_ENERGY_COST * 0.5 if any(isinstance(s, BossSnake) for s in snakes) else DASH_ENERGY_COST
            self.energy -= dash_energy_cost
            
            if self.dash_duration <= 0 or self.energy <= 0:
                self.is_dashing = False
                self.dash_duration = 0
                self.dash_cooldown = DASH_COOLDOWN
        
        # 대시 쿨다운 감소
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # 에너지 관련 처리
        max_energy = 100 + (self.stats["ENERGY"] - 1) * 20  # 스탯당 20 에너지 증가
        if self.energy <= 0:
            self.alive = False
            return
        elif self.energy > max_energy:
            self.energy = max_energy

        # AI 행동 처리
        if self.is_ai:
            self.ai_decide_direction(food_list, snakes)

        # 회복 시스템 업데이트
        self.update_recovery()
        
        # 번식 쿨다운 감소
        if self.breed_cooldown > 0:
            self.breed_cooldown -= 1
        
        # 이동 처리
        head_x, head_y = self.get_head()
        dx, dy = 0, 0
        
        # 기존 방식의 이동
        base_speed = CELL_SIZE * (1 + (self.stats["SPEED"] - 1) * 0.2)  # 스탯당 20% 속도 증가
        if self.direction == 'UP': dy = -base_speed
        elif self.direction == 'DOWN': dy = base_speed
        elif self.direction == 'LEFT': dx = -base_speed
        elif self.direction == 'RIGHT': dx = base_speed

        # 대시와 스피드 부스트 효과 적용
        speed_mult = 1
        if self.is_dashing:
            speed_mult *= 2
        if self.active_effects["SPEED_BOOST"] > 0:
            speed_mult *= 2
        # 돌진 모드일 때 속도 2배
        if hasattr(self, 'is_charging') and self.is_charging:
            speed_mult *= 2
        dx *= speed_mult
        dy *= speed_mult

        new_head = [head_x + dx, head_y + dy]

        # 벽 충돌 처리
        new_head[0] = max(0, min(new_head[0], WIDTH - CELL_SIZE))
        new_head[1] = max(0, min(new_head[1], HEIGHT - CELL_SIZE))

        # 충돌 체크 (고스트 효과 중에는 무시)
        if not self.collision_immune and not self.active_effects["GHOST"] > 0:
            if new_head in self.body[1:]:
                self.alive = False
                return

        self.body.insert(0, new_head)
        
        # 에너지 소모 (스탯에 따라 감소)
        base_consume = 0.5  # 기본 소모량을 절반으로 감소
        # 보스전일 때 에너지 소모 절반으로 감소
        if any(isinstance(s, BossSnake) for s in snakes):
            base_consume *= 0.5
        energy_efficiency = 1 - (self.stats["ENERGY"] - 1) * 0.15  # 스탯당 15% 에너지 소모 감소
        self.energy -= base_consume * energy_efficiency

        # 음식 충돌 체크 및 경험치 획득
        foods_to_remove = []
        for food in food_list:
            food_x, food_y = food.get_pos()
            # Hunter 형태일 때 흡수 범위 3배 증가
            absorption_range = CELL_SIZE * 3 if self.evolution_form == "HUNTER" else CELL_SIZE
            distance = math.sqrt((food_x - new_head[0])**2 + (food_y - new_head[1])**2)
            
            if distance < absorption_range:
                foods_to_remove.append(food)
                if isinstance(food, SpecialItem):
                    self.apply_special_item(food.type)
                    self.score += 20  # 점수만 획득
                else:
                    self.boost = 2 if food.is_item else 1
                    if food.is_item:  # 황금 음식
                        self.energy += 40
                        self.score += 10
                        self.add_exp(500)
                    else:  # 일반 음식
                        self.energy += 15
                        self.score += 1
                        self.add_exp(100)  # 1000에서 100으로 수정
                    self.grow = True
                break

        for food in foods_to_remove:
            if food in food_list:
                food_list.remove(food)

        if not self.grow:
            self.body.pop()
        else:
            for _ in range(self.boost - 1):
                self.body.append(self.body[-1])
            self.boost = 1
            self.grow = False

        # 돌진 모드 타이머 관리(중복 방지)
        if hasattr(self, 'is_charging') and self.is_charging:
            self.charge_timer -= 1
            if self.charge_timer <= 0:
                self.is_charging = False

    def ai_decide_direction(self, food_list, snakes):
        """AI의 방향 결정"""
        if not self.alive:
            return

        head_x, head_y = self.get_head()
        
        # 플레이어 감지 및 추적
        player = None
        for snake in snakes:
            if not snake.is_ai and snake.alive:
                player = snake
                break
        
        if player:
            player_x, player_y = player.get_head()
            distance_to_player = math.hypot(player_x - head_x, player_y - head_y)
            
            # 플레이어가 감지 범위 내에 있고 에너지가 충분할 때
            if distance_to_player < PLAYER_DETECTION_RANGE and self.energy > CHASE_ENERGY_THRESHOLD:
                self.is_chasing = True
                self.chase_timer = CHASE_DURATION
                self.target_player = player
                self.last_player_pos = (player_x, player_y)
            
            # 추적 중이면서 에너지가 충분할 때
            if self.is_chasing and self.energy > RETREAT_ENERGY_THRESHOLD:
                self.chase_timer -= 1
                if self.chase_timer <= 0:
                    self.is_chasing = False
                    self.target_player = None
                else:
                    # 플레이어 방향으로 이동
                    if player_x > head_x: self.direction = 'RIGHT'
                    elif player_x < head_x: self.direction = 'LEFT'
                    elif player_y > head_y: self.direction = 'DOWN'
                    elif player_y < head_y: self.direction = 'UP'
                    
                    # 가까이 있을 때 대시 시도
                    if distance_to_player < 50 and self.energy > 50:
                        self.dash()
                    return
        
        # 에너지가 낮거나 추적 중이 아닐 때는 음식 찾기
        closest_food = None
        min_distance = float('inf')
        
        for food in food_list:
            distance = math.hypot(food.x - head_x, food.y - head_y)
            if distance < min_distance:
                min_distance = distance
                closest_food = food
        
        if closest_food:
            # 음식 방향으로 이동
            if closest_food.x > head_x: self.direction = 'RIGHT'
            elif closest_food.x < head_x: self.direction = 'LEFT'
            elif closest_food.y > head_y: self.direction = 'DOWN'
            elif closest_food.y < head_y: self.direction = 'UP'
        else:
            # 랜덤한 방향 선택
            if random.random() < 0.1:
                self.direction = random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])

    def dash(self):
        """대시 시스템"""
        # 이미 대시 중이면 대시 중지
        if self.is_dashing:
            self.is_dashing = False
            self.dash_duration = 0
            self.dash_cooldown = DASH_COOLDOWN  # 중지 시점부터 10초 쿨타임
            return False
            
        # 새로운 대시 시작
        dash_cost = 20 if self.evolution_form == "SPEEDER" else 30
        if self.dash_cooldown <= 0 and self.energy >= dash_cost:
            self.is_dashing = True
            self.energy -= dash_cost
            self.dash_duration = DASH_DURATION
            
            # 대시 시 짧은 무적 시간 부여
            if self.evolution_form == "ULTIMATE":
                self.invincible_time = 15
            elif self.evolution_form == "SPEEDER":
                self.invincible_time = 10
            else:
                self.invincible_time = 5
            
            return True
        return False

    def upgrade_stat(self, stat_name):
        """스탯 업그레이드"""
        if (stat_name in self.stats and 
            self.stat_points >= STAT_COSTS[stat_name] and 
            self.stats[stat_name] < MAX_STAT_LEVEL):
            self.stats[stat_name] += 1
            self.stat_points -= STAT_COSTS[stat_name]
            return True
        return False
        
    def apply_special_item(self, item_type):
        """특수 아이템 효과 적용"""
        if item_type in SPECIAL_ITEMS:
            self.active_effects[item_type] = SPECIAL_ITEMS[item_type]["duration"]
            # SHIELD 아이템은 완전 면역 효과 부여
            if item_type == "SHIELD":
                self.collision_immune = True
            # 메시지 설정
            self.message = f"{self.name}이(가) {SPECIAL_ITEMS[item_type]['name']}을(를) 섭취하였습니다!"
            self.message_duration = 45  # 3초간 표시 (15fps * 3)

    def update_effects(self):
        """특수 아이템 효과 업데이트"""
        # 기존 효과 업데이트
        for effect in self.active_effects:
            if self.active_effects[effect] > 0:
                self.active_effects[effect] -= 1
                # SHIELD 효과가 끝나면 면역 해제
                if effect == "SHIELD" and self.active_effects[effect] == 0:
                    self.collision_immune = False
        
        # Tank 면역 쿨다운 업데이트
        if self.tank_immunity_cooldown > 0:
            self.tank_immunity_cooldown -= 1
            if self.tank_immunity_cooldown <= 0:
                self.tank_immunity_used = False  # 쿨다운이 끝나면 다시 사용 가능

    def activate_tank_immunity(self):
        """Tank 형태의 일회용 피해 면역 능력을 활성화"""
        if (self.evolution_form == "TANK" and 
            self.tank_immunity_cooldown <= 0 and 
            not self.tank_immunity_used):
            self.tank_immunity_active = True
            self.tank_immunity_used = True
            self.tank_immunity_cooldown = 300  # 20초 (15fps * 20)
            self.collision_immune = True
            # 메시지 설정
            self.message = "일회용 피해 면역이 활성화되었습니다!"
            self.message_duration = 45  # 3초간 표시
            return True
        return False

    def handle_collision(self, other):
        """충돌 처리 시 Tank의 일회용 면역 해제"""
        if self.tank_immunity_active:
            self.tank_immunity_active = False
            self.collision_immune = False
            # 메시지 설정
            self.message = "일회용 피해 면역이 소모되었습니다!"
            self.message_duration = 45  # 3초간 표시
            return True  # 충돌 무시
        return False  # 일반 충돌 처리

    def update_message(self):
        """메시지 업데이트"""
        if self.message_duration > 0:
            self.message_duration -= 1
            if self.message_duration <= 0:
                self.message = None

#############################################
# 진화 모드 클래스
#############################################
class SpecialItem(Food):
    """특수 아이템 클래스 (진화 모드)"""
    def __init__(self, x, y):
        super().__init__(x, y, is_item=True)
        self.type = random.choice(list(SPECIAL_ITEMS.keys()))
        self.color = SPECIAL_ITEMS[self.type]["color"]

#############################################
# 유틸리티 함수 (모든 모드 공통)
#############################################
def generate_name():
    """AI 뱀 이름 생성"""
    names = ["Neo", "Axe", "Lyn", "Koz", "Dex", "Zex", "Vox", "Tyr", "Lux", "Kai"]
    return random.choice(names) + str(random.randint(10, 99))

def spawn_food(food_list, snakes, is_item=False):
    """음식 생성"""
    while True:
        fx = random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        fy = random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        if all(not [fx, fy] in s.body for s in snakes):
            food_list.append(Food(fx, fy, is_item=is_item))
            break

def is_safe_location(x, y, snakes, min_distance=SAFE_SPAWN_DISTANCE):
    """주어진 위치가 스폰하기에 안전한지 확인"""
    # 화면 가장자리 근처는 제외
    if (x < SPAWN_AREA_PADDING or x > WIDTH - SPAWN_AREA_PADDING or 
        y < SPAWN_AREA_PADDING or y > HEIGHT - SPAWN_AREA_PADDING):
        return False
        
    # 다른 뱀들과의 거리 확인
    for snake in snakes:
        if not snake.alive:
            continue
        for segment in snake.body:
            dist = math.hypot(x - segment[0], y - segment[1])
            if dist < min_distance:
                return False
    return True

def find_safe_spawn_location(snakes):
    """안전한 스폰 위치 찾기"""
    attempts = 100  # 최대 시도 횟수
    best_location = None
    max_min_distance = 0
    
    while attempts > 0:
        x = random.randint(SPAWN_AREA_PADDING, WIDTH - SPAWN_AREA_PADDING)
        x = x - (x % CELL_SIZE)  # 그리드에 맞추기
        y = random.randint(SPAWN_AREA_PADDING, HEIGHT - SPAWN_AREA_PADDING)
        y = y - (y % CELL_SIZE)  # 그리드에 맞추기
        
        # 최소 거리 계산
        min_distance = float('inf')
        for snake in snakes:
            if not snake.alive:
                continue
            for segment in snake.body:
                dist = math.hypot(x - segment[0], y - segment[1])
                min_distance = min(min_distance, dist)
        
        # 더 좋은 위치 발견시 업데이트
        if min_distance > max_min_distance:
            max_min_distance = min_distance
            best_location = (x, y)
        
        if min_distance >= SAFE_SPAWN_DISTANCE:
            return x, y
            
        attempts -= 1
    
    # 완벽한 위치를 찾지 못했다면 가장 좋은 위치 반환
    if best_location:
        return best_location
    
    # 최후의 수단: 화면 중앙에서 먼 곳
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(200, 300)
    x = center_x + math.cos(angle) * distance
    y = center_y + math.sin(angle) * distance
    return int(x - (x % CELL_SIZE)), int(y - (y % CELL_SIZE))

def spawn_ai_snake(snakes):
    """개선된 AI 스네이크 스폰 함수"""
    x, y = find_safe_spawn_location(snakes)
    new_snake = Snake(x, y, color=BLUE, is_ai=True, name=generate_name())
    new_snake.spawn_protection_time = SPAWN_PROTECTION_TIME
    new_snake.collision_immune = True
    snakes.append(new_snake)

def draw_energy_bar(screen, snake):
    bar_width = 200
    height = 15
    x, y = 20, 10
    
    # 뱀의 머리 위치 확인
    head_x, head_y = snake.get_head()
    text_area = pygame.Rect(x, y, bar_width + 100, height + 30)  # 텍스트 영역
    is_snake_near = text_area.collidepoint(head_x, head_y)
    
    # 알파값 설정 (뱀이 가까이 있으면 255, 아니면 128)
    alpha = 255 if is_snake_near else 128
    
    # 에너지 바 배경
    pygame.draw.rect(screen, (WHITE[0], WHITE[1], WHITE[2], alpha), (x-2, y-2, bar_width+4, height+4), 1)
    fill = min(bar_width, max(0, int((snake.energy / 150) * bar_width)))
    
    # 에너지 바 채우기
    energy_surface = pygame.Surface((fill, height), pygame.SRCALPHA)
    energy_surface.fill((RED[0], RED[1], RED[2], alpha))
    screen.blit(energy_surface, (x, y))
    
    # 텍스트 렌더링
    fm = get_font_manager()
    font = fm.get_font('small', 24)
    txt = font.render(f"Energy: {int(snake.energy)}", True, (WHITE[0], WHITE[1], WHITE[2], alpha))
    screen.blit(txt, (x, y + height + 4))

def draw_leaderboard(screen, snakes):
    fm = get_font_manager()
    font = fm.get_font('small', 24)
    sorted_snakes = sorted([s for s in snakes if s.alive], key=lambda s: s.score, reverse=True)
    
    # 리더보드 영역 정의
    x, y = WIDTH - 220, 10
    height_per_entry = 25
    total_height = 40 + len(sorted_snakes[:5]) * height_per_entry
    
    # 뱀들의 머리 위치 확인
    any_snake_near = False
    leaderboard_area = pygame.Rect(x, y, 220, total_height)
    for snake in snakes:
        if snake.alive:
            head_x, head_y = snake.get_head()
            if leaderboard_area.collidepoint(head_x, head_y):
                any_snake_near = True
                break
    
    # 알파값 설정
    alpha = 255 if any_snake_near else 128
    
    # 제목 렌더링
    title = font.render("Live Leaderboard:", True, (GRAY[0], GRAY[1], GRAY[2], alpha))
    screen.blit(title, (x, y))
    
    # 순위 렌더링
    for i, s in enumerate(sorted_snakes[:5]):
        text = font.render(f"{i+1}. {s.name} - {s.score}", True, (GRAY[0], GRAY[1], GRAY[2], alpha))
        screen.blit(text, (x, 40 + i * height_per_entry))

def draw_vision_cone(screen, x, y, angle, fov, dist, color=(255, 0, 0, 50)):
    """시야 원뿔을 그리는 함수
    Args:
        screen: pygame.Surface, 시야를 그릴 대상 Surface
        x, y: float, 시야의 시작점 좌표
        angle: float, 시야의 중심 각도 (도)
        fov: float, 시야각 (도)
        dist: float, 시야 거리
        color: tuple, 시야 색상 (RGBA)
    """
    # 시야 원뿔을 그릴 투명한 Surface 생성
    cone_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    
    # 시작과 끝 각도 계산 (라디안)
    start_angle = math.radians(angle - fov/2)
    end_angle = math.radians(angle + fov/2)
    
    # 원뿔의 꼭짓점들 계산
    points = [(x, y)]
    step = math.radians(15)  # 15도 간격으로 점 생성
    
    current_angle = start_angle
    while current_angle <= end_angle:
        px = x + math.cos(current_angle) * dist
        py = y + math.sin(current_angle) * dist
        points.append((px, py))
        current_angle += step
    
    # 마지막 점 추가
    px = x + math.cos(end_angle) * dist
    py = y + math.sin(end_angle) * dist
    points.append((px, py))
    
    # 원뿔 그리기
    pygame.draw.polygon(cone_surface, color, points)
    pygame.draw.polygon(cone_surface, (color[0], color[1], color[2], 255), points, 2)
    
    # 화면에 블렌딩
    screen.blit(cone_surface, (0, 0))

def draw_snake(screen, snake, show_emotion=False):
    if not snake.alive:
        return
        
    # 깜빡이는 효과는 Tank의 일회용 면역이 활성화되었을 때만 적용
    if snake.evolution_form == "TANK" and snake.tank_immunity_active:
        if pygame.time.get_ticks() % 200 < 100:  # 깜빡이는 효과
            alpha = 128
        else:
            alpha = 255
    # 다른 무적 상태에서는 반투명 효과만 적용
    elif snake.collision_immune:
        alpha = 180
    else:
        alpha = 255
    
    # 시야 원뿔 그리기 (시뮬레이션 모드에서만)
    if show_emotion and snake.is_ai:
        head_x, head_y = snake.get_head()
        angle = get_angle_from_direction(snake.direction)
        draw_vision_cone(screen, head_x, head_y, angle, snake.vision_angle, snake.vision_range)
    
    # 뱀 그리기
    for segment in snake.body:
        s = pygame.Surface((CELL_SIZE, CELL_SIZE))
        s.fill(snake.color)
        s.set_alpha(alpha)
        screen.blit(s, (segment[0], segment[1]))
    
    if show_emotion:
        fm = get_font_manager()
        font = fm.get_font('small', 18)
        emotion_color = EMOTIONS[snake.emotion]["color"]
        txt = font.render(snake.emotion, True, emotion_color)
        screen.blit(txt, (snake.get_head()[0] + 10, snake.get_head()[1] - 5))

def handle_collisions(snakes):
    for snake in snakes:
        if not snake.alive:
            continue
        head_x, head_y = snake.get_head()
        for other in snakes:
            if not other.alive or snake == other:
                continue
            # 보스(BossSnake)는 일반 충돌로 죽지 않음
            if isinstance(snake, BossSnake) or isinstance(other, BossSnake):
                continue
            # 머리끼리 충돌
            other_head_x, other_head_y = other.get_head()
            head_distance = math.sqrt((head_x - other_head_x)**2 + (head_y - other_head_y)**2)
            if head_distance < CELL_SIZE:
                snake_immune = snake.handle_collision(other) if snake.tank_immunity_active else snake.collision_immune
                other_immune = other.handle_collision(snake) if other.tank_immunity_active else other.collision_immune
                if not snake_immune:
                    snake.alive = False
                if not other_immune:
                    other.alive = False
                continue
            # 몸통 충돌
            for segment in other.body[1:]:
                segment_x, segment_y = segment
                distance = math.sqrt((head_x - segment_x)**2 + (head_y - segment_y)**2)
                if distance < CELL_SIZE:
                    if snake.tank_immunity_active:
                        snake.handle_collision(other)
                        break
                    elif not snake.collision_immune:
                        snake.alive = False
                        if not other.is_ai:
                            other.score += 50
                            other.add_exp(300)
                    break

def save_score(name, score):
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            board = json.load(f)
    except:
        board = []

    board.append({
        "name": name,
        "score": score,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    board = sorted(board, key=lambda x: x["score"], reverse=True)[:3]
    
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(board, f, indent=2)

def get_angle_from_direction(direction):
    if direction == 'RIGHT': return 0
    elif direction == 'DOWN': return 90
    elif direction == 'LEFT': return 180
    elif direction == 'UP': return 270
    return 0

def angle_diff(a, b):
    d = (b - a) % 360
    if d > 180:
        d -= 360
    return d

def draw_minimap(screen, snakes, food_list):
    """미니맵 그리기"""
    # 미니맵 크기와 위치 설정
    map_size = 150
    margin = 20
    map_x = WIDTH - map_size - margin
    map_y = HEIGHT - map_size - margin
    
    # 미니맵 배경
    pygame.draw.rect(screen, (50, 50, 50), 
                    (map_x, map_y, map_size, map_size))
    pygame.draw.rect(screen, WHITE, 
                    (map_x, map_y, map_size, map_size), 1)
    
    # 스케일 계산
    scale_x = map_size / WIDTH
    scale_y = map_size / HEIGHT
    
    # 음식 그리기 (흰 점)
    for food in food_list:
        if isinstance(food, SpecialItem):
            color = food.color
            size = 3
        else:
            color = WHITE
            size = 1
        x = map_x + int(food.x * scale_x)
        y = map_y + int(food.y * scale_y)
        pygame.draw.circle(screen, color, (x, y), size)
    
    # 뱀 그리기
    for snake in snakes:
        if not snake.alive:
            continue
        head = snake.get_head()
        x = map_x + int(head[0] * scale_x)
        y = map_y + int(head[1] * scale_y)
        color = snake.color
        # 플레이어는 더 크게 표시
        size = 4 if not snake.is_ai else 2
        pygame.draw.circle(screen, color, (x, y), size)

def draw_stats(screen, snake):
    """스탯 UI 그리기"""
    if snake.is_ai:
        return
        
    fm = get_font_manager()
    font = fm.get_font('small', 20)
    x, y = 20, 180
    stats_text = [
        f"스탯 포인트: {snake.stat_points}",
        f"이동속도: {snake.stats['SPEED']}/{MAX_STAT_LEVEL}",
        f"에너지: {snake.stats['ENERGY']}/{MAX_STAT_LEVEL}"
    ]
    
    # 뱀의 머리 위치 확인
    head_x, head_y = snake.get_head()
    stats_area = pygame.Rect(x-10, y-10, 200, len(stats_text) * 25 + 10)
    is_snake_near = stats_area.collidepoint(head_x, head_y)
    
    # 알파값 설정
    alpha = 255 if is_snake_near else 128
    
    # 배경 패널
    panel_height = len(stats_text) * 25 + 10
    panel_surface = pygame.Surface((200, panel_height), pygame.SRCALPHA)
    panel_surface.fill((0, 0, 0, alpha//2))  # 배경은 더 투명하게
    screen.blit(panel_surface, (x-10, y-10))
    
    # 스탯 텍스트
    for i, text in enumerate(stats_text):
        text_surface = font.render(text, True, (WHITE[0], WHITE[1], WHITE[2], alpha))
        screen.blit(text_surface, (x, y + i * 25))
        
    # 활성 효과 표시
    if any(snake.active_effects.values()):
        y += panel_height + 10
        effects_text = []
        for effect, duration in snake.active_effects.items():
            if duration > 0:
                effects_text.append(f"{effect}: {duration//15+1}초")
        
        if effects_text:
            effects_panel = pygame.Surface((200, len(effects_text) * 25 + 10), pygame.SRCALPHA)
            effects_panel.fill((0, 0, 0, alpha//2))
            screen.blit(effects_panel, (x-10, y-10))
            
            for i, text in enumerate(effects_text):
                effect_text = font.render(text, True, (WHITE[0], WHITE[1], WHITE[2], alpha))
                screen.blit(effect_text, (x, y + i * 25))

def spawn_special_item(food_list, snakes):
    """특수 아이템 생성"""
    while True:
        x = random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        if all(not [x, y] in s.body for s in snakes):
            food_list.append(SpecialItem(x, y))
            break

def draw_game_ui(screen, player, snakes, game_mode, food_list=None):
    """게임 UI 그리기"""
    # 기본 UI
    draw_leaderboard(screen, snakes)
    draw_energy_bar(screen, player)
    
    # 메시지 표시
    for snake in snakes:
        if snake.message and snake.message_duration > 0:
            fm = get_font_manager()
            font = fm.get_font('button', 24)
            text = font.render(snake.message, True, YELLOW)
            # 화면 중앙 상단에 메시지 표시
            x = (WIDTH - text.get_width()) // 2
            y = 50
            screen.blit(text, (x, y))
            snake.update_message()
    
    # 진화 모드 UI
    if game_mode == "EVOLUTION":
        draw_stats(screen, player)
        if food_list is not None:
            draw_minimap(screen, snakes, food_list)
        draw_status_ui(screen, player)
        if player.dash_cooldown > 0:
            fm = get_font_manager()
            font = fm.get_font('small', 24)
            cooldown_text = font.render(f"Dash: {player.dash_cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 140))
    
    # 클래식 모드 UI
    elif game_mode == "CLASSIC":
        if player.dash_cooldown > 0:
            fm = get_font_manager()
            font = fm.get_font('small', 24)
            cooldown_text = font.render(f"Dash: {player.dash_cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 60))

def draw_status_ui(screen, snake):
    """플레이어의 상태 UI를 화면에 표시하는 함수"""
    # 상태 UI 영역 정의
    status_width = 200
    x, y = 20, 80
    
    # 뱀의 머리 위치 확인
    head_x, head_y = snake.get_head()
    status_area = pygame.Rect(x, y, status_width, 100)
    is_snake_near = status_area.collidepoint(head_x, head_y)
    
    # 알파값 설정
    alpha = 255 if is_snake_near else 128
    
    # 상태 UI 배경
    background = pygame.Surface((status_width, 100), pygame.SRCALPHA)
    background.fill((0, 0, 0, alpha//2))
    screen.blit(background, (x, y))
    
    # 폰트 설정
    fm = get_font_manager()
    font = fm.get_font('small', 20)
    
    # 텍스트 렌더링
    level_text = font.render(f"Level: {snake.level}", True, (WHITE[0], WHITE[1], WHITE[2], alpha))
    exp_text = font.render(f"EXP: {snake.exp}/{snake.exp_to_level}", True, (WHITE[0], WHITE[1], WHITE[2], alpha))
    
    # 진화 형태 색상에 알파값 적용
    form_color = EVOLUTION_FORMS[snake.evolution_form]["color"]
    form_color_with_alpha = (form_color[0], form_color[1], form_color[2], alpha)
    form_text = font.render(f"Form: {snake.evolution_form}", True, form_color_with_alpha)
    
    # 텍스트 배치
    screen.blit(level_text, (x + 10, y + 10))
    screen.blit(exp_text, (x + 10, y + 35))
    screen.blit(form_text, (x + 10, y + 60))
    
    # 경험치 바
    exp_ratio = snake.exp / snake.exp_to_level
    bar_surface = pygame.Surface((status_width - 20, 5), pygame.SRCALPHA)
    pygame.draw.rect(bar_surface, (50, 50, 50, alpha), (0, 0, status_width - 20, 5))
    pygame.draw.rect(bar_surface, (0, 255, 0, alpha), (0, 0, (status_width - 20) * exp_ratio, 5))
    screen.blit(bar_surface, (x + 10, y + 85))

def update_items(food_list, snakes, item_timer, special_item_timer):
    """
    아이템 생성을 관리하는 함수
    
    매개변수:
        food_list: list - 게임 내 모든 음식/아이템 목록
        snakes: list - 게임 내 모든 뱀 목록
        item_timer: int - 일반 아이템 생성 타이머
        special_item_timer: int - 특수 아이템 생성 타이머
        
    기능:
        - 일정 시간마다 일반 아이템 생성
        - 일정 시간마다 특수 아이템 생성
    """
    if item_timer >= 75:  # 5초 (15fps * 5)
        spawn_food(food_list, snakes, is_item=True)
        item_timer = 0
        
    if special_item_timer >= 225:  # 15초 (15fps * 15)
        spawn_special_item(food_list, snakes)
        special_item_timer = 0

# =========================================
# 보스전 시스템 (Boss Battle System)
# =========================================

# 보스전 상수
BOSS_EVOLUTION_TIME = {
    "PHASE2": 2700,  # 3분 (15fps * 180초)
    "PHASE3": 5400   # 6분 (15fps * 360초) - 최종 페이즈
}

BOSS_PATTERNS = {
    "NORMAL": {
        "color": PURPLE,
        "speed": 1.0,
        "damage": 1.0,
        "description": "기본 상태"
    },
    "EVOLVED1": {
        "color": RED,
        "speed": 1.2,
        "damage": 1.3,
        "description": "1차 진화 - 속도 증가"
    },
    "EVOLVED2": {
        "color": ORANGE,
        "speed": 1.4,
        "damage": 1.6,
        "description": "최종 진화"
    }
}

class Projectile:
    """보스의 투사체 클래스"""
    def __init__(self, x, y, target_x, target_y, speed=5, is_circular=False):
        self.x = float(x)
        self.y = float(y)
        if is_circular:
            # 방향 벡터를 그대로 사용 (원형 탄막용)
            self.dx = target_x * speed
            self.dy = target_y * speed
        else:
            # 목표 지점을 향한 방향 벡터 계산
            dx = target_x - x
            dy = target_y - y
            # 방향 벡터 정규화
            length = math.sqrt(dx * dx + dy * dy)
            self.dx = (dx / length) * speed if length > 0 else 0
            self.dy = (dy / length) * speed if length > 0 else 0
        self.speed = speed
        self.size = CELL_SIZE
        self.alive = True
        self.color = ORANGE if is_circular else RED

    def move(self):
        """투사체 이동"""
        self.x += self.dx
        self.y += self.dy
        
        # 화면 밖으로 나가면 제거
        if (self.x < 0 or self.x > WIDTH or 
            self.y < 0 or self.y > HEIGHT):
            self.alive = False

class BossSnake(Snake):
    """보스 스네이크 클래스"""
    def __init__(self, x, y):
        super().__init__(x, y, color=PURPLE, name="BOSS", is_ai=True)
        self.init_boss_attributes()
        # 경고음 관련 속성 추가
        self.warning_sound = pygame.mixer.Sound("warning_sound.mp3")
        self.warning_duration = None  # 경고음 길이 (밀리초)
        self.warning_start_time = 0  # 경고음 시작 시간
        self.is_warning = False  # 경고음 재생 중 여부
        # 전체 공격 관련 속성 추가
        self.safe_zone = None  # (x, y, width, height)
        self.is_global_attack = False  # 전체 공격 상태
        self.global_attack_damage = 0  # 전체 공격 데미지
        self.global_attack_timer = 0  # 전체 공격 타이머

    def init_boss_attributes(self):
        """보스 속성 초기화"""
        # 기본 스탯
        self.max_health = 200
        self.health = self.max_health
        self.phase = 1
        self.pattern = "NORMAL"
        self.survival_time = 0  # 생존 시간 카운터
        
        # 공격 관련
        self.attack_cooldown = 0
        self.dash_cooldown = 0
        self.current_attack = None
        self.projectile_cooldown = 75  # 5초 (15fps * 5)
        self.projectiles = []  # 투사체 리스트
        self.circular_shot_count = 8  # 기본 원형 탄막 발사 수
        self.enhanced_circular_mode = False  # 강화된 원형 탄막 모드
        self.enhanced_shot_count = 16  # 강화된 원형 탄막 발사 수
        self.burst_count = 0  # 연속 발사 카운터
        self.max_bursts = 3  # 최대 연속 발사 횟수
        
        # 크기 증가
        self.size_multiplier = 2
        self.body = [[self.body[0][0], self.body[0][1]]]  # 초기 크기는 1로 시작
        self.body.append([self.body[0][0] - CELL_SIZE, self.body[0][1]])
        self.body.append([self.body[0][0] - CELL_SIZE * 2, self.body[0][1]])
        
        # 무한 스태미나
        self.energy = float('inf')
        
        # 이동 관련
        self.move_delay = 0

    def update_boss_state(self, player):
        """보스 상태 업데이트"""
        if not self.alive:
            return

        # 생존 시간 증가
        self.survival_time += 1
        
        # 체력 기반 강제 진화
        health_ratio = self.health / self.max_health
        if health_ratio <= 0.3 and self.phase < 3:  # 체력 30% 이하면 3페이즈
            self.evolve_boss(3, player)
            self.message = "보스가 위험 상태에서 최종 형태로 강제 진화했습니다!"
            self.message_duration = 60
        elif health_ratio <= 0.6 and self.phase < 2:  # 체력 60% 이하면 2페이즈
            self.evolve_boss(2, player)
            self.message = "보스가 위험 상태에서 2페이즈로 강제 진화했습니다!"
            self.message_duration = 60
        # 시간에 따른 진화 (체력 기반 진화가 되지 않았을 경우)
        elif self.survival_time >= BOSS_EVOLUTION_TIME["PHASE3"] and self.phase < 3:
            self.evolve_boss(3, player)
            # 3페이즈 진입 3초 후 강화 모드 활성화
            if self.survival_time == BOSS_EVOLUTION_TIME["PHASE3"] + 45:  # 3초 = 45틱
                self.enhanced_circular_mode = True
                self.message = "보스의 전체 공격이 더욱 강화되었습니다!"
                self.message_duration = 60
        elif self.survival_time >= BOSS_EVOLUTION_TIME["PHASE2"] and self.phase < 2:
            self.evolve_boss(2, player)
        
        # 쿨다운 감소
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            
        # 투사체 발사
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        else:
            if self.phase == 1:  # 1페이즈: 5초마다 단일 투사체
                self.shoot_projectile(player)
                self.projectile_cooldown = 75  # 5초
            elif self.phase == 2:  # 2페이즈: 3초마다 2발씩 발사
                self.shoot_projectile(player)
                self.shoot_projectile(player)
                self.projectile_cooldown = 45  # 3초
            elif self.phase >= 3:  # 3페이즈: 원형 탄막 + 전체 공격
                self.shoot_projectile(player)  # 원형 탄막 발사
                if self.burst_count >= self.max_bursts:
                    self.projectile_cooldown = 45  # 3초 후 다음 3연발
                    self.burst_count = 0
                else:
                    self.projectile_cooldown = 5  # 연속 발사 간격
                    self.burst_count += 1
            
            # 60초마다 전체 공격
            if self.phase >= 3 and self.survival_time % 9999999999999 == 0:  # 사실상 발동 불가능한 시간으로 설정
                self.start_global_attack(player)
        
        # 전체 공격 처리
        if self.is_warning:
            current_time = pygame.time.get_ticks()
            if current_time - self.warning_start_time >= self.warning_duration:
                self.is_warning = False
                self.is_global_attack = True
                self.global_attack_timer = 30  # 2초간 공격 지속
                self.message = "전체 공격 개시!"
                self.message_duration = 30
        
        if self.is_global_attack:
            self.global_attack_timer -= 1
            if self.global_attack_timer <= 0:
                self.is_global_attack = False
                self.safe_zone = None

    def play_warning(self):
        """경고음 재생 및 관련 상태 설정"""
        if not self.is_warning:
            self.warning_sound.play()
            self.warning_duration = int(self.warning_sound.get_length() * 1000)  # 밀리초 단위로 변환
            self.warning_start_time = pygame.time.get_ticks()
            self.is_warning = True

    def start_global_attack(self, player):
        """전체 공격 시작"""
        if not self.is_warning and not self.is_global_attack:
            self.play_warning()
            # 안전 구역 생성 (화면의 1/6 크기)
            safe_width = WIDTH // 6
            safe_height = HEIGHT // 6
            # 랜덤한 위치에 안전 구역 생성
            safe_x = random.randint(0, WIDTH - safe_width)
            safe_y = random.randint(0, HEIGHT - safe_height)
            self.safe_zone = (safe_x, safe_y, safe_width, safe_height)
            self.global_attack_damage = 10 if self.phase == 3 else 5
            self.message = "전체 공격 준비 중! 안전 구역으로 이동하세요!"
            self.message_duration = 60

    def shoot_projectile(self, player):
        """투사체 발사 - 플레이어를 향해"""
        if not player.alive:
            return
        head_x, head_y = self.get_head()
        
        if self.phase <= 2:
            # 1,2페이즈: 플레이어 추적 투사체
            player_x, player_y = player.get_head()
            self.projectiles.append(Projectile(head_x, head_y, player_x, player_y, speed=3 + self.phase))
        else:
            # 3페이즈: 회전하는 원형 탄막
            shot_count = self.enhanced_shot_count if self.enhanced_circular_mode else self.circular_shot_count
            base_rotation = (2 * math.pi * self.burst_count) / self.max_bursts  # 기본 회전 각도
            
            for i in range(shot_count):
                angle = (2 * math.pi * i) / shot_count + base_rotation  # 기본 회전 각도 추가
                dx = math.cos(angle)
                dy = math.sin(angle)
                self.projectiles.append(Projectile(head_x, head_y, dx, dy, speed=4, is_circular=True))

    def update_projectiles(self):
        """투사체 업데이트"""
        for projectile in self.projectiles[:]:  # 리스트 복사본으로 반복
            projectile.move()
            if not projectile.alive:
                self.projectiles.remove(projectile)

    def evolve_boss(self, new_phase, player=None):
        """보스 진화"""
        self.phase = new_phase
        if new_phase == 2:
            self.pattern = "EVOLVED1"
            self.size_multiplier = 2.2
            self.message = "보스가 2페이즈로 진화했습니다! 더 빠르게 추적합니다!"
            # 2페이즈 진입 시 대시 관련 변수 초기화
            self.is_dashing = False
            self.dash_duration = 0
            self.dash_cooldown = 0
            # 페이즈2 진입 시 플레이어 길이의 2배로 맞춤(최소 3)
            if player is not None:
                target_len = max(3, int(len(player.body) * 2))
                if len(self.body) < target_len:
                    while len(self.body) < target_len:
                        self.body.append(self.body[-1][:])
                elif len(self.body) > target_len:
                    self.body = self.body[:target_len]
        elif new_phase == 3:
            self.pattern = "EVOLVED2"
            self.size_multiplier = 2.5
            self.message = "보스가 최종 형태에 도달했습니다! 원형 탄막과 대시 능력 사용 시작작!"
            # 3페이즈 진입 시 경고음 재생
            self.warning_sound.play()
            # 페이즈3 진입 시 플레이어 길이의 4배로 맞춤(최소 3)
            if player is not None:
                target_len = max(3, int(len(player.body) * 4))
                if len(self.body) < target_len:
                    while len(self.body) < target_len:
                        self.body.append(self.body[-1][:])
                elif len(self.body) > target_len:
                    self.body = self.body[:target_len]
        # 진화 시 몸 크기 조정 메시지
        self.body = [[x, y] for x, y in self.body]
        self.message_duration = 60

    def boss_ai_behavior(self, player, food_list):
        """보스 AI 행동 결정"""
        if not self.alive or not player.alive:
            return

        # 페이즈1에서는 모드2 AI(추적/대시 등) 사용
        if self.phase == 1:
            self.ai_decide_direction(food_list, [player, self])
            return

        # 페이즈2: 플레이어를 먹이로 인식, 더 공격적으로 추적 (대시 없음)
        if self.phase == 2:
            head_x, head_y = self.get_head()
            player_x, player_y = player.get_head()
            distance_to_player = math.hypot(player_x - head_x, player_y - head_y)
            PLAYER_CHASE_RANGE = 300  # 추적 범위 증가
            
            # 플레이어가 가까우면 무조건 추적
            if distance_to_player < PLAYER_CHASE_RANGE:
                # 플레이어 방향으로 이동
                if abs(player_x - head_x) > abs(player_y - head_y):
                    if player_x > head_x:
                        self.direction = 'RIGHT'
                    else:
                        self.direction = 'LEFT'
                else:
                    if player_y > head_y:
                        self.direction = 'DOWN'
                    else:
                        self.direction = 'UP'
            return

        # 페이즈3: 매우 공격적인 AI
        if self.phase == 3:
            head_x, head_y = self.get_head()
            player_x, player_y = player.get_head()
            distance_to_player = math.hypot(player_x - head_x, player_y - head_y)
            AGGRESSIVE_CHASE_RANGE = 400  # 더 넓은 추적 범위
            AGGRESSIVE_DASH_RANGE = 150  # 더 넓은 대시 범위
            
            # 항상 플레이어 추적
            if abs(player_x - head_x) > abs(player_y - head_y):
                if player_x > head_x:
                    self.direction = 'RIGHT'
                else:
                    self.direction = 'LEFT'
            else:
                if player_y > head_y:
                    self.direction = 'DOWN'
                else:
                    self.direction = 'UP'
            
            # 더 자주 대시 사용
            if distance_to_player < AGGRESSIVE_DASH_RANGE and not self.is_dashing and self.dash_cooldown <= 0:
                self.is_dashing = True
                self.dash_duration = 45  # 대시 지속시간 증가(3초)
                self.dash_cooldown = 30  # 더 짧은 쿨타임(2초)

    def move(self, food_list, snakes, tick):
        """보스 이동 처리"""
        if self.move_delay > 0:
            self.move_delay -= 1
            return
            
        # 다음 위치 계산
        head_x, head_y = self.get_head()
        next_x, next_y = head_x, head_y
        
        # 2페이즈일 때 속도 절반으로 감소
        base_speed = CELL_SIZE * (1.5 if self.is_dashing else 1)
        if self.phase == 2:
            base_speed *= 0.5
            
        if self.direction == 'RIGHT': next_x += base_speed
        elif self.direction == 'LEFT': next_x -= base_speed
        elif self.direction == 'DOWN': next_y += base_speed
        elif self.direction == 'UP': next_y -= base_speed
        
        # 벽 충돌 방지
        next_x = max(0, min(next_x, WIDTH - CELL_SIZE))
        next_y = max(0, min(next_y, HEIGHT - CELL_SIZE))
        
        # 새로운 머리 위치 추가
        self.body.insert(0, [next_x, next_y])
        
        # 음식 충돌 체크
        foods_to_remove = []
        for food in food_list:
            food_x, food_y = food.get_pos()
            distance = math.sqrt((food_x - next_x)**2 + (food_y - next_y)**2)
            
            if distance < CELL_SIZE * self.size_multiplier:
                foods_to_remove.append(food)
                if self.phase == 1:  # 1페이즈에서만 성장
                    # 일반 음식은 1, 황금 음식은 2만큼 성장
                    growth = 2 if food.is_item else 1
                    for _ in range(growth):
                        self.body.append(self.body[-1][:])
                break
        
        # 음식 제거
        for food in foods_to_remove:
            if food in food_list:
                food_list.remove(food)
        
        if not foods_to_remove:  # 음식을 먹지 않았을 때만 꼬리 제거
            self.body.pop()
        
        # 무한 스태미나 유지
        self.energy = float('inf')
        
        # 2페이즈일 때 이동 후 딜레이 추가
        if self.phase == 2:
            self.move_delay = 1  # 1틱 대기

def handle_boss_collision(boss, player):
    """보스 충돌 처리"""
    if not boss.alive or not player.alive:
        return
    head_x, head_y = boss.get_head()
    player_x, player_y = player.get_head()
    
    # 전체 공격 데미지 처리
    if boss.is_global_attack:
        if boss.safe_zone:
            safe_x, safe_y, safe_width, safe_height = boss.safe_zone
            # 플레이어가 안전 구역 밖에 있으면 데미지
            if not (safe_x <= player_x <= safe_x + safe_width and 
                   safe_y <= player_y <= safe_y + safe_height):
                player.alive = False
                player.message = "전체 공격에 당했습니다!"
                player.message_duration = 60
                return
    
    # 투사체와 플레이어 충돌 체크
    for projectile in boss.projectiles[:]:
        distance = math.hypot(projectile.x - player_x, projectile.y - player_y)
        if distance < CELL_SIZE:
            player.alive = False
            player.message = "보스의 투사체에 맞았습니다!"
            player.message_duration = 60
            boss.projectiles.remove(projectile)
            return
    
    # 플레이어와 보스 충돌
    distance = math.hypot(player_x - head_x, player_y - head_y)
    if distance < CELL_SIZE * boss.size_multiplier:
        # 돌진 모드일 때만 보스에게 데미지
        if getattr(player, 'is_charging', False):
            prev_health = boss.health  # 이전 체력 저장
            boss.health -= 10 
            player.message = f"보스에게 10 데미지! (체력: {prev_health} -> {boss.health})"
            player.message_duration = 45
            if boss.health <= 0:
                boss.alive = False
                boss.message = "보스가 쓰러졌습니다!"
                boss.message_duration = 60
        else:
            # 돌진이 아니면 플레이어 즉사
            player.alive = False
            player.message = "보스에게 부딪혀 사망!"
            player.message_duration = 60

def draw_boss_ui(screen, boss, player):
    """보스 UI 그리기"""
    # 보스 체력바
    bar_width = 400
    height = 20
    x = (WIDTH - bar_width) // 2
    y = 20
    
    # 체력바 배경
    pygame.draw.rect(screen, (50, 50, 50), (x-2, y-2, bar_width+4, height+4))
    
    # 체력바
    health_ratio = boss.health / boss.max_health
    health_width = int(bar_width * health_ratio)
    health_color = BOSS_PATTERNS[boss.pattern]["color"]
    pygame.draw.rect(screen, health_color, (x, y, health_width, height))
    
    # 보스 정보
    fm = get_font_manager()
    font = fm.get_font('small', 20)
    phase_text = font.render(f"Phase {boss.phase}", True, WHITE)
    pattern_text = font.render(f"Pattern: {boss.pattern}", True, BOSS_PATTERNS[boss.pattern]["color"])
    
    screen.blit(phase_text, (x, y + height + 5))
    screen.blit(pattern_text, (x + 100, y + height + 5))
    
    # 생존 시간
    time_text = font.render(f"Time: {boss.survival_time//15}s", True, WHITE)
    screen.blit(time_text, (x + 250, y + height + 5))
    
    # 투사체 그리기
    for projectile in boss.projectiles:
        pygame.draw.rect(screen, projectile.color, 
                        (projectile.x, projectile.y, projectile.size, projectile.size))    
    # 안전 구역 그리기
    if boss.safe_zone:
        safe_x, safe_y, safe_width, safe_height = boss.safe_zone
        if boss.is_warning:  # 경고 중에는 초록색
            safe_color = (0, 255, 0, 128)
        else:  # 공격 중에는 파란색
            safe_color = (0, 0, 255, 128)
        safe_surface = pygame.Surface((safe_width, safe_height), pygame.SRCALPHA)
        safe_surface.fill(safe_color)
        screen.blit(safe_surface, (safe_x, safe_y))
        # 테두리 그리기
        pygame.draw.rect(screen, (255, 255, 255), 
                        (safe_x, safe_y, safe_width, safe_height), 2)
