"""
Snake Game - 모듈 파일
게임의 핵심 로직과 클래스들을 포함하는 모듈입니다.
"""

import pygame
import random
import math
import json
from datetime import datetime

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
DASH_ENERGY_COST = 1    # 초당 에너지 소모량 (절반으로 감소)

#############################################
# 진화 모드 상수
#############################################
# 스탯 시스템
MAX_STAT_LEVEL = 5
STAT_COSTS = {
    "SPEED": 1,
    "ENERGY": 1,
    "STRENGTH": 1,
    "DEFENSE": 1
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
        "abilities": ["체력 증가", "충돌 저항"],
        "description": "생존력 특화"
    },
    "HUNTER": {
        "color": PURPLE,
        "abilities": ["먹이 감지", "긴 대시"],
        "description": "사냥 특화"
    },
    "ULTIMATE": {
        "color": GOLD,
        "abilities": ["모든 능력", "무적 대시"],
        "description": "궁극의 형태"
    }
}

# 특수 아이템 정의
SPECIAL_ITEMS = {
    "SHIELD": {
        "color": (0, 191, 255),  # 하늘색
        "duration": 75,  # 5초
        "effect": "방어력 2배 증가"
    },
    "SPEED_BOOST": {
        "color": (255, 215, 0),  # 골드
        "duration": 60,  # 4초
        "effect": "이동속도 2배 증가"
    },
    "GHOST": {
        "color": (169, 169, 169),  # 회색
        "duration": 45,  # 3초
        "effect": "다른 뱀 통과 가능"
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
            "ENERGY": 1,
            "STRENGTH": 1,
            "DEFENSE": 1
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
            
        # 시뮬레이션 모드 속성
        if is_ai:
            self.init_simulation_attributes()

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

    def init_simulation_attributes(self):
        """시뮬레이션 모드 속성 초기화"""
        # 감정 시스템
        self.emotion = "NORMAL"
        self.emotion_timer = 0
        self.breed_cooldown = 0
        
        # 전투 시스템
        self.strength = random.uniform(20, 30)
        self.stunned = False
        self.stun_timer = 0
        
        # 기본 AI 특성
        self.move_delay = 0
        self.velocity_x = 0
        self.velocity_y = 0
        self.vision_range = VISION_RANGE
        self.vision_angle = VISION_ANGLE
        
        # 성별 및 번식
        self.gender = random.choice(["M", "F"])
        self.breed_cooldown = 130
        self.breed_energy_threshold = 50
        self.birth_count = 0
        self.max_births = 4 if self.gender == "F" else 0
        
        # 에너지 공유
        self.altruism = random.uniform(0, 10)
        self.stored_energy = 0
        self.energy_given_count = 0
        self.energy_received_count = 0
        
        # 성격
        self.aggression = random.uniform(0.5, 1.5)
        self.personality = random.choice(["CAUTIOUS", "AGGRESSIVE", "SOCIAL"])

    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.exp -= self.exp_to_level
        self.exp_to_level = int(self.exp_to_level * 1.5)
        self.evolution_points += 1
        self.stat_points += 2  # 레벨업 시 2개의 스탯 포인트 획득
        return self.level

    def can_evolve(self):
        if self.level >= 10 and self.evolution_form != "ULTIMATE":
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
            # 방어력 스탯과 쉴드 효과 적용
            shield_active = self.active_effects["SHIELD"] > 0
            self.collision_immune = (self.evolution_form in ["TANK", "ULTIMATE"] or 
                                   shield_active or 
                                   self.stats["DEFENSE"] >= MAX_STAT_LEVEL)

        # 대시 상태 업데이트
        if self.is_dashing:
            self.dash_duration -= 1
            self.energy -= DASH_ENERGY_COST  # 대시 중 에너지 소모
            
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

        # 시뮬레이션 모드에서는 감정 상태 업데이트
        if simulation_mode:
            self.update_emotion_state(snakes)
            
        if simulation_mode and self.is_ai:
            self.update_ai_behavior(food_list, snakes)
        elif self.is_ai:
            self.ai_decide_direction(food_list, snakes)

        # 회복 시스템 업데이트
        self.update_recovery()
        
        # 번식 쿨다운 감소
        if self.breed_cooldown > 0:
            self.breed_cooldown -= 1
        
        # 여분 에너지 저장
        self.store_extra_energy()
        
        # 근처 아군과 에너지 공유
        if simulation_mode:
            nearby_snakes = [s for s in snakes if s != self and s.alive and
                           math.hypot(s.get_head()[0] - self.get_head()[0],
                                    s.get_head()[1] - self.get_head()[1]) < 100]
            self.share_energy(nearby_snakes)
        
        # 이동 처리
        head_x, head_y = self.get_head()
        dx, dy = 0, 0
        
        if simulation_mode and self.is_ai:
            # 시뮬레이션 모드의 AI 이동
            speed = EMOTIONS[self.emotion]["speed_multiplier"] * (2 if self.is_dashing else 1)
            dx = self.velocity_x * speed
            dy = self.velocity_y * speed
        else:
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
        base_consume = EMOTIONS[self.emotion]["energy_consume"] * 0.5  # 기본 소모량을 절반으로 감소
        energy_efficiency = 1 - (self.stats["ENERGY"] - 1) * 0.15  # 스탯당 15% 에너지 소모 감소
        self.energy -= base_consume * energy_efficiency

        # 음식 충돌 체크 및 경험치 획득
        foods_to_remove = []
        for food in food_list:
            food_x, food_y = food.get_pos()
            distance = math.sqrt((food_x - new_head[0])**2 + (food_y - new_head[1])**2)
            
            if distance < CELL_SIZE:
                foods_to_remove.append(food)
                if isinstance(food, SpecialItem):
                    self.apply_special_item(food.type)
                    self.score += 20
                    self.add_exp(3000)
                else:
                    self.boost = 2 if food.is_item else 1
                    self.energy += 40 if food.is_item else 10
                    self.score += 10 if food.is_item else 1
                    self.add_exp(100 if food.is_item else 50)
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

    def update_ai_behavior(self, food_list, snakes):
        if not food_list:
            return
            
        head_x, head_y = self.get_head()
        
        # 가장 가까운 음식 찾기
        closest_food = None
        min_dist = float('inf')
        for food in food_list:
            dist = math.hypot(food.x - head_x, food.y - head_y)
            if dist < min_dist and dist < self.vision_range:
                angle = math.degrees(math.atan2(food.y - head_y, food.x - head_x))
                if abs(angle_diff(angle, get_angle_from_direction(self.direction))) < self.vision_angle/2:
                    min_dist = dist
                    closest_food = food

        # 가장 가까운 위험한 뱀 찾기
        closest_threat = None
        min_threat_dist = float('inf')
        for snake in snakes:
            if snake != self and snake.alive:
                threat_x, threat_y = snake.get_head()
                dist = math.hypot(threat_x - head_x, threat_y - head_y)
                if dist < min_threat_dist and dist < self.vision_range:
                    min_threat_dist = dist
                    closest_threat = snake

        # 행동 결정
        if closest_threat and min_threat_dist < 50:
            # 도망가기
            self.velocity_x = head_x - closest_threat.get_head()[0]
            self.velocity_y = head_y - closest_threat.get_head()[1]
            mag = math.hypot(self.velocity_x, self.velocity_y)
            if mag > 0:
                self.velocity_x /= mag
                self.velocity_y /= mag
        elif closest_food:
            # 음식을 향해 이동
            self.velocity_x = closest_food.x - head_x
            self.velocity_y = closest_food.y - head_y
            mag = math.hypot(self.velocity_x, self.velocity_y)
            if mag > 0:
                self.velocity_x /= mag
                self.velocity_y /= mag
        else:
            # 랜덤한 방향으로 이동
            if random.random() < 0.02:  # 2% 확률로 방향 변경
                angle = random.uniform(0, 2 * math.pi)
                self.velocity_x = math.cos(angle)
                self.velocity_y = math.sin(angle)

    def ai_decide_direction(self, food_list, snakes):
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
            
    def update_effects(self):
        """특수 아이템 효과 업데이트"""
        for effect in self.active_effects:
            if self.active_effects[effect] > 0:
                self.active_effects[effect] -= 1

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
    pygame.draw.rect(screen, WHITE, (x-2, y-2, bar_width+4, height+4), 1)
    fill = min(bar_width, max(0, int((snake.energy / 150) * bar_width)))
    pygame.draw.rect(screen, RED, (x, y, fill, height))
    font = pygame.font.SysFont(None, 24)
    txt = font.render(f"Energy: {int(snake.energy)}", True, WHITE)
    screen.blit(txt, (x, y + height + 4))

def draw_leaderboard(screen, snakes):
    font = pygame.font.SysFont(None, 24)
    sorted_snakes = sorted([s for s in snakes if s.alive], key=lambda s: s.score, reverse=True)
    title = font.render("Live Leaderboard:", True, GRAY)
    screen.blit(title, (WIDTH - 220, 10))
    for i, s in enumerate(sorted_snakes[:5]):
        text = font.render(f"{i+1}. {s.name} - {s.score}", True, GRAY)
        screen.blit(text, (WIDTH - 220, 40 + i * 25))

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
        
    # 무적 상태일 때 반짝이는 효과
    if snake.collision_immune:
        if pygame.time.get_ticks() % 200 < 100:  # 깜빡이는 효과
            alpha = 128
        else:
            alpha = 255
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
        font = pygame.font.SysFont(None, 18)
        emotion_color = EMOTIONS[snake.emotion]["color"]
        txt = font.render(snake.emotion, True, emotion_color)
        screen.blit(txt, (snake.get_head()[0] + 10, snake.get_head()[1] - 5))

def handle_collisions(snakes):
    for snake in snakes:
        if not snake.alive:
            continue
            
        head_x, head_y = snake.get_head()
        
        # 다른 뱀들과의 충돌 체크
        for other in snakes:
            if not other.alive or snake == other:
                continue
                
            # 머리끼리 충돌한 경우
            other_head_x, other_head_y = other.get_head()
            head_distance = math.sqrt((head_x - other_head_x)**2 + (head_y - other_head_y)**2)
            
            if head_distance < CELL_SIZE:
                # 두 뱀 모두 죽음
                if not snake.collision_immune:
                    snake.alive = False
                if not other.collision_immune:
                    other.alive = False
                continue
            
            # 다른 뱀의 몸통과 충돌
            for segment in other.body[1:]:  # 머리 제외한 몸통
                segment_x, segment_y = segment
                distance = math.sqrt((head_x - segment_x)**2 + (head_y - segment_y)**2)
                
                if distance < CELL_SIZE:
                    if not snake.collision_immune:  # 충돌 면역이 없으면 죽음
                        snake.alive = False
                        # 충돌한 뱀이 플레이어면 점수 획득
                        if not other.is_ai:
                            other.score += 50
                            other.add_exp(300)  # 플레이어가 AI를 죽이면 추가 경험치
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
        
    font = pygame.font.SysFont("malgun gothic", 20)
    x, y = 20, 180
    stats_text = [
        f"스탯 포인트: {snake.stat_points}",
        f"이동속도: {snake.stats['SPEED']}/{MAX_STAT_LEVEL}",
        f"에너지: {snake.stats['ENERGY']}/{MAX_STAT_LEVEL}",
        f"공격력: {snake.stats['STRENGTH']}/{MAX_STAT_LEVEL}",
        f"방어력: {snake.stats['DEFENSE']}/{MAX_STAT_LEVEL}"
    ]
    
    # 배경 패널
    panel_height = len(stats_text) * 25 + 10
    pygame.draw.rect(screen, (0, 0, 0, 128), 
                    (x-10, y-10, 200, panel_height))
    
    # 스탯 텍스트
    for i, text in enumerate(stats_text):
        surf = font.render(text, True, WHITE)
        screen.blit(surf, (x, y + i * 25))
        
    # 활성 효과 표시
    if any(snake.active_effects.values()):
        y += panel_height + 10
        effects_text = []
        for effect, duration in snake.active_effects.items():
            if duration > 0:
                effects_text.append(f"{effect}: {duration//15+1}초")
        
        if effects_text:
            pygame.draw.rect(screen, (0, 0, 0, 128), 
                           (x-10, y-10, 200, len(effects_text) * 25 + 10))
            for i, text in enumerate(effects_text):
                surf = font.render(text, True, WHITE)
                screen.blit(surf, (x, y + i * 25))

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
    
    # 진화 모드 UI
    if game_mode == "EVOLUTION":
        draw_stats(screen, player)
        if food_list is not None:  # food_list가 제공된 경우에만 미니맵 그리기
            draw_minimap(screen, snakes, food_list)
        draw_status_ui(screen, player)
        if player.dash_cooldown > 0:
            font = pygame.font.SysFont(None, 24)
            cooldown_text = font.render(f"Dash: {player.dash_cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 140))
    
    # 클래식 모드 UI
    elif game_mode == "CLASSIC":
        if player.dash_cooldown > 0:
            font = pygame.font.SysFont(None, 24)
            cooldown_text = font.render(f"Dash: {player.dash_cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 60))

def draw_status_ui(screen, snake):
    """
    플레이어의 상태 UI를 화면에 표시하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        snake: Snake - 상태를 표시할 뱀 객체
        
    기능:
        - 레벨과 경험치 정보 표시
        - 현재 진화 형태 표시
        - 경험치 바 시각화
    """
    # 상태 UI 배경
    status_width = 200
    pygame.draw.rect(screen, (0, 0, 0, 128), (20, 80, status_width, 100))
    
    # 레벨과 경험치 표시
    font = pygame.font.SysFont("malgun gothic", 20)
    level_text = font.render(f"Level: {snake.level}", True, WHITE)
    exp_text = font.render(f"EXP: {snake.exp}/{snake.exp_to_level}", True, WHITE)
    form_text = font.render(f"Form: {snake.evolution_form}", True, 
                           EVOLUTION_FORMS[snake.evolution_form]["color"])
    
    screen.blit(level_text, (30, 90))
    screen.blit(exp_text, (30, 115))
    screen.blit(form_text, (30, 140))
    
    # 경험치 바
    exp_ratio = snake.exp / snake.exp_to_level
    pygame.draw.rect(screen, (50, 50, 50), (30, 165, status_width - 20, 5))
    pygame.draw.rect(screen, (0, 255, 0), 
                    (30, 165, (status_width - 20) * exp_ratio, 5))