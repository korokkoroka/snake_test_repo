"""
Snake Game - 메인 게임 파일
게임의 실행과 UI를 담당하는 메인 파일

기능:
1. 게임 모드 선택 (클래식, 진화, 시뮬레이션)
2. 게임 루프 관리
3. 이벤트 처리
4. UI 렌더링
"""

import subprocess
import sys
import pygame
import random
import math
from module import (
    Snake, Food, SpecialItem, spawn_food, spawn_ai_snake,
    draw_energy_bar, draw_snake, draw_leaderboard, handle_collisions,
    draw_status_ui, draw_stats, draw_minimap, spawn_special_item,
    WIDTH, HEIGHT, CELL_SIZE, LEADERBOARD_FILE,
    save_score, BLACK, WHITE, GREEN, ORANGE, RED, YELLOW, EVOLUTION_FORMS,
    GRAY, MAX_STAT_LEVEL, get_angle_from_direction, EMOTIONS,
    # 보스전 관련 임포트
    BossSnake, draw_boss_ui, handle_boss_collision, BOSS_PATTERNS
)

# 추가 색상 정의
BLUE = (0, 0, 255)
LIGHT_BLUE = (100, 149, 237)  # 더 부드러운 파란색

def install_requirements():
    """
    게임 실행에 필요한 패키지 설치
    
    Returns:
        None
    """
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print("패키지 설치 중 오류 발생:", e)
        sys.exit(1)

def draw_evolution_ui(screen, snake):
    """
    진화 선택 UI를 화면에 표시하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        snake: Snake - 진화 가능한 뱀 객체
        
    반환값:
        bool - UI가 활성화되어 있는지 여부
        
    기능:
        - 반투명 오버레이로 배경 어둡게 처리
        - 진화 가능한 형태 목록 표시
        - 각 진화 형태의 능력치 정보 표시
        - 선택 방법 안내 메시지 표시
    """
    if not snake.can_evolve():
        return False

    # 반투명 오버레이 (투명도 조정)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))  # 알파값을 180으로 설정 (0-255)
    screen.blit(overlay, (0, 0))

    # 진화 메뉴 배경
    menu_width, menu_height = 600, 400
    menu_x = (WIDTH - menu_width) // 2
    menu_y = (HEIGHT - menu_height) // 2
    
    # 메뉴 배경 (밝은 색상으로 변경)
    pygame.draw.rect(screen, (240, 240, 240), (menu_x, menu_y, menu_width, menu_height))
    pygame.draw.rect(screen, (100, 100, 100), (menu_x, menu_y, menu_width, menu_height), 3)

    # 제목
    font_large = pygame.font.SysFont("malgun gothic", 36)
    font = pygame.font.SysFont("malgun gothic", 24)
    title = font_large.render("진화 선택", True, BLACK)
    screen.blit(title, (menu_x + (menu_width - title.get_width()) // 2, menu_y + 20))

    # 진화 옵션 표시
    available_forms = []
    if snake.level >= 10:
        available_forms = ["ULTIMATE"]
    elif snake.level >= 5:
        available_forms = ["SPEEDER", "TANK", "HUNTER"]

    for i, form in enumerate(available_forms):
        form_data = EVOLUTION_FORMS[form]
        y_pos = menu_y + 100 + i * 80
        
        # 선택 박스 배경 (더 밝은 배경)
        pygame.draw.rect(screen, (250, 250, 250), 
                        (menu_x + 20, y_pos - 10, menu_width - 40, 70))
        pygame.draw.rect(screen, form_data["color"], 
                        (menu_x + 20, y_pos - 10, menu_width - 40, 70), 2)
        
        # 진화 형태 이름 (더 큰 폰트와 진한 색상)
        name_text = font.render(f"{i+1}. {form}", True, BLACK)
        screen.blit(name_text, (menu_x + 40, y_pos))
        
        # 능력 목록 (색상 구분)
        abilities_text = font.render(" | ".join(form_data["abilities"]), True, form_data["color"])
        screen.blit(abilities_text, (menu_x + 40, y_pos + 30))

    # 안내 메시지 (하이라이트 추가)
    guide_box = pygame.Surface((400, 40), pygame.SRCALPHA)
    guide_box.fill((0, 0, 0, 50))
    screen.blit(guide_box, (menu_x + (menu_width - 400) // 2, menu_y + menu_height - 50))
    
    guide = font.render("1-3 키로 선택하거나 ESC로 취소", True, BLACK)
    screen.blit(guide, (menu_x + (menu_width - guide.get_width()) // 2, 
                       menu_y + menu_height - 40))

    return True

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

def mode_select_screen():
    """
    게임 모드 선택 화면 표시
    
    Returns:
        str: 선택된 게임 모드 ("CLASSIC", "EVOLUTION", "BOSS")
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("게임 모드 선택")
    font = pygame.font.SysFont("malgun gothic", 24)
    clock = pygame.time.Clock()

    while True:
        screen.fill(BLACK)
        title = font.render("게임 모드 선택", True, WHITE)
        mode1 = font.render("1. 클래식 모드 (대시 기능)", True, WHITE)
        mode2 = font.render("2. 진화 모드", True, WHITE)
        mode3 = font.render("3. 보스전 모드", True, WHITE)
        
        screen.blit(title, (WIDTH//2 - 100, HEIGHT//4))
        screen.blit(mode1, (WIDTH//2 - 150, HEIGHT//2 - 50))
        screen.blit(mode2, (WIDTH//2 - 150, HEIGHT//2))
        screen.blit(mode3, (WIDTH//2 - 150, HEIGHT//2 + 50))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "CLASSIC"
                elif event.key == pygame.K_2:
                    return "EVOLUTION"
                elif event.key == pygame.K_3:
                    return "BOSS"
        clock.tick(30)

def handle_evolution(screen, player, event):
    """진화 선택을 처리하는 함수"""
    if event.type != pygame.KEYDOWN:
        return True
        
    if event.key == pygame.K_ESCAPE:
        return False
    
    if player.level >= 10 and event.key == pygame.K_1:
        player.evolve("ULTIMATE")
        return False
    elif player.level >= 5:
        if event.key == pygame.K_1:
            player.evolve("SPEEDER")
            return False
        elif event.key == pygame.K_2:
            player.evolve("TANK")
            return False
        elif event.key == pygame.K_3:
            player.evolve("HUNTER")
            return False
            
    return True  # 유효한 키가 아니면 UI 유지

def game_loop(game_mode):
    """
    게임의 메인 루프를 실행하는 함수
    
    매개변수:
        game_mode: str - 게임 모드 ("CLASSIC", "EVOLUTION", "BOSS")
        
    기능:
        - 게임 초기화 및 설정
        - 게임 객체 생성 및 관리
        - 이벤트 처리 및 게임 상태 업데이트
        - 화면 렌더링
    """
    # 초기 설정
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    caption = {
        "CLASSIC": "Snake Game - Classic Mode",
        "EVOLUTION": "Snake Game - Evolution Mode",
        "BOSS": "Snake Game - Boss Mode"
    }
    pygame.display.set_caption(caption[game_mode])
    clock = pygame.time.Clock()

    # 게임 객체 초기화
    if game_mode == "BOSS":
        player = Snake(WIDTH//4, HEIGHT//2, color=GREEN, name="YOU", is_ai=False)
        boss = BossSnake(WIDTH*3//4, HEIGHT//2)
        snakes = [player, boss]
    else:
        player = Snake(WIDTH//4, HEIGHT//2, color=GREEN, name="YOU")
        snakes = [player]
    
    food_list = []  # food_list 초기화
    
    # AI 스네이크 초기화
    if game_mode == "CLASSIC":
        spawn_ai_snake(snakes)
    elif game_mode == "BOSS":
        # 보스 모드에서는 추가 AI 스네이크 생성하지 않음
        pass
    else:
        for _ in range(3):
            spawn_ai_snake(snakes)

    # 초기 음식 생성
    for _ in range(10):
        spawn_food(food_list, snakes)

    # 게임 상태 변수 초기화
    ai_timer = 0
    ai_check_timer = 0
    item_timer = 225  # 게임 시작 시 바로 아이템 생성 가능하도록 설정
    special_item_timer = 225  # 게임 시작 시 바로 특수 아이템 생성 가능하도록 설정
    tick = 0
    evolution_ui_active = False
    evolution_ui_just_activated = False
    running = True

    # 메인 게임 루프
    while running:
        screen.fill(BLACK)
        tick += 1
        
        # 타이머 업데이트
        ai_timer += 1
        ai_check_timer += 1
        
        # 보스 모드일 때는 아이템 타이머 별도 관리
        if game_mode == "BOSS":
            item_timer += 1
            special_item_timer += 1
        
        # 게임 상태 업데이트
        if not evolution_ui_active:
            # AI 관리 (클래식 모드 제외)
            if game_mode == "EVOLUTION":
                update_ai_population(snakes, ai_check_timer, ai_timer)
                item_timer += 1
                special_item_timer += 1
                # 진화 모드 아이템 생성 (일반: 15초, 특수: 30초)
                if item_timer >= 225:  # 15초 (15fps * 15)
                    normal_item_count = sum(1 for food in food_list if food.is_item and not isinstance(food, SpecialItem))
                    if normal_item_count < 3:  # 최대 3개
                        spawn_food(food_list, snakes, is_item=True)
                    item_timer = 0
                if special_item_timer >= 450:  # 30초 (15fps * 30)
                    special_item_count = sum(1 for food in food_list if isinstance(food, SpecialItem))
                    if special_item_count < 3:  # 최대 3개
                        spawn_special_item(food_list, snakes)
                    special_item_timer = 0

            # 아이템 생성 (보스 모드)
            elif game_mode == "BOSS":
                item_timer += 1
                special_item_timer += 1
                update_items(food_list, snakes, item_timer, special_item_timer)

            # 보스 모드 특수 처리
            if game_mode == "BOSS":
                boss = snakes[1]  # 보스는 항상 두 번째 뱀
                boss.update_boss_state(player)
                boss.boss_ai_behavior(player, food_list)
                boss.update_projectiles()  # 보스 투사체 이동 및 관리
                # 보스와의 충돌 처리 추가
                handle_boss_collision(boss, player)
                
                # 보스를 처치하면 게임 승리
                if not boss.alive:
                    player.message = "보스 처치"
                    player.message_duration = 60
                    running = False
                    break

            # 모든 뱀 업데이트
            update_snakes(snakes, food_list, tick, game_mode)

            # 충돌 처리
            handle_collisions(snakes)

            # 음식 보충
            if len(food_list) < 10:
                spawn_food(food_list, snakes)

        # 화면 그리기
        draw_game_objects(screen, food_list, snakes, game_mode)
        
        # UI 그리기
        draw_game_ui(screen, player, snakes, game_mode, food_list)
        
        # 보스 UI 그리기 (보스 모드)
        if game_mode == "BOSS":
            draw_boss_ui(screen, boss, player)
        
        # 진화 UI 처리 (진화 모드와 보스 모드)
        if game_mode in ["EVOLUTION", "BOSS"]:
            evolution_ui_active, evolution_ui_just_activated = handle_evolution_ui(
                screen, player, evolution_ui_active, evolution_ui_just_activated)

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_mode == "BOSS" and event.key == pygame.K_f:
                    if not hasattr(player, 'is_charging') or not player.is_charging:
                        if player.energy >= 30:
                            player.energy -= 30
                            player.is_charging = True
                            player.charge_timer = 15  # 1초간 돌진
                            player.collision_immune = True  # 5초 무적 시작
                            player.invincible_time = 75
                else:
                    evolution_ui_active = handle_keydown(event, game_mode, player, evolution_ui_active, screen)

        # 게임 오버 체크
        if not player.alive:
            if game_mode == "BOSS":
                player.message = "보스에게 패배했습니다..."
                player.message_duration = 60
            next_action = handle_game_over(screen, player, game_mode)
            if next_action == "restart":
                return "restart"
            elif next_action == "mode_select":
                return "mode_select"
            running = False

        # 돌진 모드 타이머 관리 (BOSS 모드에서만)
        if game_mode == "BOSS" and hasattr(player, 'is_charging') and player.is_charging:
            player.charge_timer -= 1
            if player.charge_timer <= 0:
                player.is_charging = False

        pygame.display.flip()
        clock.tick(15)

def update_ai_population(snakes, ai_check_timer, ai_timer):
    """
    AI 뱀 개체 수를 관리하는 함수
    
    매개변수:
        snakes: list - 게임 내 모든 뱀 목록
        ai_check_timer: int - AI 체크 타이머
        ai_timer: int - AI 생성 타이머
        
    기능:
        - 현재 AI 뱀 개체 수 확인
        - 필요한 경우 새로운 AI 뱀 생성
        - 최소 AI 개체 수 유지
    """
    current_ai_count = sum(1 for s in snakes if s.is_ai and s.alive)
    
    if ai_check_timer >= 150:
        if current_ai_count < 7:
            spawn_ai_snake(snakes)
        ai_check_timer = 0
    
    if current_ai_count < 3:
        spawn_ai_snake(snakes)
        ai_timer = 0
        ai_check_timer = 0

def update_items(food_list, snakes, item_timer, special_item_timer):
    """
    아이템 생성을 관리하는 함수
    
    매개변수:
        food_list: list - 게임 내 모든 음식/아이템 목록
        snakes: list - 게임 내 모든 뱀 목록
        item_timer: int - 일반 아이템 생성 타이머
        special_item_timer: int - 특수 아이템 생성 타이머
    """
    # 일반 아이템과 특수 아이템 개수 확인
    normal_item_count = sum(1 for food in food_list if food.is_item and not isinstance(food, SpecialItem))
    special_item_count = sum(1 for food in food_list if isinstance(food, SpecialItem))
    
    # 일반 아이템 생성 (최대 3개)
    if item_timer >= 225:  # 15초 (15fps * 15)
        if normal_item_count < 3:
            spawn_food(food_list, snakes, is_item=True)
        item_timer = 0
        
    # 특수 아이템 생성 (최대 3개)
    if special_item_timer >= 225:  # 15초
        if special_item_count < 3:
            spawn_special_item(food_list, snakes)
        special_item_timer = 0

def update_snakes(snakes, food_list, tick, game_mode):
    """
    모든 뱀의 상태를 업데이트하는 함수
    
    매개변수:
        snakes: list - 게임 내 모든 뱀 목록
        food_list: list - 게임 내 모든 음식/아이템 목록
        tick: int - 현재 게임 틱
        game_mode: str - 현재 게임 모드
        
    기능:
        - 각 뱀의 효과 상태 업데이트
        - 각 뱀의 이동 처리
    """
    for snake in snakes:
        if snake.alive:
            snake.update_effects()
            snake.move(food_list, snakes, tick)

def draw_game_objects(screen, food_list, snakes, game_mode):
    """
    게임 오브젝트를 화면에 렌더링하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        food_list: list - 게임 내 모든 음식/아이템 목록
        snakes: list - 게임 내 모든 뱀 목록
        game_mode: str - 현재 게임 모드
        
    기능:
        - 일반 음식과 아이템 렌더링
        - 특수 아이템 렌더링
        - 모든 뱀 렌더링
    """
    # 음식 그리기
    for food in food_list:
        if isinstance(food, SpecialItem):
            pygame.draw.rect(screen, food.color, 
                           pygame.Rect(food.x, food.y, 6, 6))
        else:
            color = ORANGE if food.is_item else WHITE
            size = 4 if food.is_item else CELL_SIZE
            pygame.draw.rect(screen, color, 
                           pygame.Rect(food.x, food.y, size, size))

    # 뱀 그리기
    for snake in snakes:
        draw_snake(screen, snake)

def draw_snake(screen, snake):
    """뱀 그리기"""
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
    
    # 뱀 그리기
    for segment in snake.body:
        s = pygame.Surface((CELL_SIZE, CELL_SIZE))
        s.fill(snake.color)
        s.set_alpha(alpha)
        screen.blit(s, (segment[0], segment[1]))

def draw_game_ui(screen, player, snakes, game_mode, food_list=None):
    """게임 UI 그리기"""
    # 기본 UI (보스 모드가 아닐 때만 리더보드 표시)
    if game_mode != "BOSS":
        draw_leaderboard(screen, snakes)
    draw_energy_bar(screen, player)
    
    # 메시지 표시
    for snake in snakes:
        if snake.message and snake.message_duration > 0:
            font = pygame.font.SysFont("malgun gothic", 24)
            text = font.render(snake.message, True, YELLOW)
            # 화면 중앙 상단에서 체력바 아래로 메시지 위치 이동
            x = (WIDTH - text.get_width()) // 2
            y = 80  # 체력바(20) + 여유 공간(60)
            
            # 메시지 배경 추가
            padding = 10
            background = pygame.Surface((text.get_width() + padding * 2, text.get_height() + padding * 2), pygame.SRCALPHA)
            background.fill((0, 0, 0, 180))  # 반투명 검은색 배경
            
            # 배경과 텍스트 표시
            screen.blit(background, (x - padding, y - padding))
            screen.blit(text, (x, y))
            snake.update_message()
    
    # 진화 모드와 보스 모드 UI
    if game_mode in ["EVOLUTION", "BOSS"]:
        # 미니맵을 먼저 그려서 다른 UI 요소들이 미니맵 위에 표시되도록 함
        if food_list is not None:
            draw_minimap(screen, snakes, food_list)
            
        draw_stats(screen, player)
        draw_status_ui(screen, player)
        
        # 도움말 메시지 초기화
        messages = []
        tank_messages = []  # Tank 관련 메시지 별도 관리
        font = pygame.font.SysFont("malgun gothic", 20)
        
        # 기본 조작 도움말
        messages.append(("SPACE: 대시 사용", WHITE))
        
        # 보스전 전용 도움말
        if game_mode == "BOSS":
            messages.append(("F: 돌진 공격 (스테미너 30 소모)", YELLOW))
        
        # 스탯 포인트가 있을 때 도움말 메시지
        if player.stat_points > 0:
            messages.append(("TAB: 스탯 찍기", (255, 255, 0)))
            
        # Tank 형태의 면역 관련 메시지
        if player.evolution_form == "TANK":
            if player.tank_immunity_active:
                tank_messages.append(("면역 상태 (일회용)", RED))
            elif player.tank_immunity_cooldown > 0:
                tank_messages.append((f"면역 쿨다운: {player.tank_immunity_cooldown//15}초", GRAY))
            elif not player.tank_immunity_used:
                tank_messages.append(("E: 피해 면역 사용", GREEN))
        
        # 대시 쿨다운 메시지
        if player.dash_cooldown > 0:
            messages.append((f"대시 쿨다운: {player.dash_cooldown}", YELLOW))
        
        # 메시지 렌더링 함수
        def render_message_box(msgs, x, y, alpha=180):
            if not msgs:
                return 0
                
            total_height = len(msgs) * 25
            max_width = max(font.render(msg, True, color).get_width() for msg, color in msgs)
            
            padding = 10
            background_width = max_width + padding * 2
            background = pygame.Surface((background_width, total_height + padding * 2), pygame.SRCALPHA)
            background.fill((0, 0, 0, alpha))
            
            screen.blit(background, (x, y))
            
            for i, (msg, color) in enumerate(msgs):
                text_surface = font.render(msg, True, color)
                text_x = x + padding
                text_y = y + padding + i * 25
                screen.blit(text_surface, (text_x, text_y))
            
            return total_height + padding * 2
        
        # 기본 도움말 렌더링
        if messages:
            base_x = 20
            base_y = HEIGHT - 150  # 기본 도움말 위치
            render_message_box(messages, base_x, base_y)
        
        # Tank 도움말 렌더링 (더 위쪽에 표시)
        if tank_messages:
            tank_x = 20
            tank_y = HEIGHT - 220  # Tank 도움말 위치 (기본 도움말보다 위에)
            render_message_box(tank_messages, tank_x, tank_y)
    
    # 클래식 모드 UI
    elif game_mode == "CLASSIC":
        if player.dash_cooldown > 0:
            font = pygame.font.SysFont(None, 24)
            cooldown_text = font.render(f"Dash: {player.dash_cooldown}", True, YELLOW)
            screen.blit(cooldown_text, (20, 60))

    # 보스 모드 추가 UI
    if game_mode == "BOSS":
        pass  # 돌진 공격 도움말은 이미 위에서 표시됨

def handle_evolution_ui(screen, player, evolution_ui_active, evolution_ui_just_activated):
    """
    진화 UI 상태를 처리하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        player: Snake - 플레이어 객체
        evolution_ui_active: bool - 진화 UI 활성화 상태
        evolution_ui_just_activated: bool - 진화 UI가 방금 활성화되었는지 여부
        
    반환값:
        tuple - (evolution_ui_active, evolution_ui_just_activated)
        
    기능:
        - 진화 가능 상태 확인
        - 진화 UI 활성화/비활성화 상태 관리
        - 진화 UI 표시
    """
    if player.can_evolve():
        if not evolution_ui_active and not evolution_ui_just_activated:
            evolution_ui_active = True
            evolution_ui_just_activated = True
    else:
        evolution_ui_active = False
        evolution_ui_just_activated = False

    if evolution_ui_active:
        evolution_ui_active = draw_evolution_ui(screen, player)
        if not evolution_ui_active:  # 진화 선택이 완료되면
            evolution_ui_just_activated = False
    
    return evolution_ui_active, evolution_ui_just_activated

def draw_stat_window(screen, snake):
    """
    스탯 업그레이드 창을 표시하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        snake: Snake - 스탯을 표시할 뱀 객체
    """
    # 창 크기와 위치 설정 (높이 감소)
    window_width = 300
    window_height = 300  # 400에서 300으로 감소
    x = (WIDTH - window_width) // 2
    y = (HEIGHT - window_height) // 2
    
    # 반투명 창 배경
    window_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    pygame.draw.rect(window_surface, (50, 50, 50, 180), (0, 0, window_width, window_height))
    pygame.draw.rect(window_surface, (255, 255, 255, 180), (0, 0, window_width, window_height), 2)
    
    # 제목
    font_large = pygame.font.SysFont("malgun gothic", 30)
    font = pygame.font.SysFont("malgun gothic", 20)
    title = font_large.render("스탯 업그레이드", True, (255, 255, 255, 180))
    title_surface = pygame.Surface(title.get_size(), pygame.SRCALPHA)
    title_surface.blit(title, (0, 0))
    window_surface.blit(title_surface, ((window_width - title.get_width()) // 2, 20))
    
    # 스탯 포인트 표시
    points_text = font.render(f"남은 스탯 포인트: {snake.stat_points}", True, (255, 255, 255, 180))
    points_surface = pygame.Surface(points_text.get_size(), pygame.SRCALPHA)
    points_surface.blit(points_text, (0, 0))
    window_surface.blit(points_surface, (20, 70))
    
    # 스탯 목록 (방어력과 공격력 제거)
    stats = [
        ("이동속도 (1)", "SPEED", "이동속도 20% 증가"),
        ("에너지 (2)", "ENERGY", "최대 에너지 20 증가, 소모량 15% 감소")
    ]
    
    for i, (name, stat, desc) in enumerate(stats):
        y_pos = 120 + i * 60
        
        # 스탯 이름과 레벨
        stat_text = font.render(f"{name}: {snake.stats[stat]}/{MAX_STAT_LEVEL}", True, (255, 255, 255, 180))
        stat_surface = pygame.Surface(stat_text.get_size(), pygame.SRCALPHA)
        stat_surface.blit(stat_text, (0, 0))
        window_surface.blit(stat_surface, (20, y_pos))
        
        # 설명
        desc_text = font.render(desc, True, (200, 200, 200, 180))
        desc_surface = pygame.Surface(desc_text.get_size(), pygame.SRCALPHA)
        desc_surface.blit(desc_text, (0, 0))
        window_surface.blit(desc_surface, (20, y_pos + 25))
        
        # 레벨 바 (반투명)
        bar_width = 200
        bar_surface = pygame.Surface((bar_width, 5), pygame.SRCALPHA)
        pygame.draw.rect(bar_surface, (100, 100, 100, 180), (0, 0, bar_width, 5))
        pygame.draw.rect(bar_surface, (0, 255, 0, 180), 
                        (0, 0, bar_width * (snake.stats[stat] / MAX_STAT_LEVEL), 5))
        window_surface.blit(bar_surface, (20, y_pos + 45))
    
    # 안내 메시지
    guide = font.render("ESC: 닫기", True, (255, 255, 255, 180))
    guide_surface = pygame.Surface(guide.get_size(), pygame.SRCALPHA)
    guide_surface.blit(guide, (0, 0))
    window_surface.blit(guide_surface, (20, window_height - 40))
    
    # 최종 창을 화면에 표시
    screen.blit(window_surface, (x, y))

def handle_keydown(event, game_mode, player, evolution_ui_active, screen):
    """키 입력을 처리하는 함수"""
    if game_mode in ["EVOLUTION", "BOSS"] and evolution_ui_active:
        evolution_ui_active = handle_evolution(screen, player, event)
        return evolution_ui_active
    else:
        if event.key in [pygame.K_UP, pygame.K_w]: player.direction = 'UP'
        elif event.key in [pygame.K_DOWN, pygame.K_s]: player.direction = 'DOWN'
        elif event.key in [pygame.K_LEFT, pygame.K_a]: player.direction = 'LEFT'
        elif event.key in [pygame.K_RIGHT, pygame.K_d]: player.direction = 'RIGHT'
        elif event.key == pygame.K_SPACE:
            player.dash()
        elif event.key == pygame.K_e and game_mode in ["EVOLUTION", "BOSS"]:
            player.activate_tank_immunity()
        elif event.key == pygame.K_TAB and game_mode in ["EVOLUTION", "BOSS"]:
            # 스탯 창 표시
            draw_stat_window(screen, player)
            pygame.display.flip()
            waiting_for_close = True
            while waiting_for_close:
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            waiting_for_close = False
                        elif e.key in [pygame.K_1, pygame.K_2]:  # 3, 4 키 제거
                            if e.key == pygame.K_1: player.upgrade_stat("SPEED")
                            elif e.key == pygame.K_2: player.upgrade_stat("ENERGY")
                            draw_stat_window(screen, player)
                            pygame.display.flip()
                    elif e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
        return evolution_ui_active

def handle_game_over(screen, player, game_mode):
    """
    게임 오버 상태를 처리하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        player: Snake - 플레이어 객체
        game_mode: str - 현재 게임 모드
    
    반환값:
        str: 다음 행동 ("restart", "mode_select", "quit", None)
    """
    # 보스 모드가 아닐 때만 점수 저장
    if game_mode != "BOSS":
        save_score(player.name, player.score)
    
    # 반투명 오버레이
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # 게임 오버 텍스트
    font_large = pygame.font.SysFont("malgun gothic", 72)
    font = pygame.font.SysFont("malgun gothic", 36)
    
    game_over_text = font_large.render("GAME OVER", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//3))
    
    # 점수 표시
    score_text = font.render(f"점수: {player.score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//3 + 100))
    
    # 버튼 설정
    button_width, button_height = 180, 50
    button_margin = 20
    buttons_y = HEIGHT//3 + 200
    total_buttons_width = button_width * 3 + button_margin * 2
    start_x = WIDTH//2 - total_buttons_width//2
    
    # 재시작 버튼
    restart_button = pygame.Rect(start_x, buttons_y, button_width, button_height)
    pygame.draw.rect(screen, GREEN, restart_button)
    pygame.draw.rect(screen, WHITE, restart_button, 2)
    restart_text = font.render("재시작", True, BLACK)
    screen.blit(restart_text, (restart_button.centerx - restart_text.get_width()//2, 
                              restart_button.centery - restart_text.get_height()//2))
    
    # 모드 선택 버튼
    mode_button = pygame.Rect(start_x + button_width + button_margin, buttons_y, button_width, button_height)
    pygame.draw.rect(screen, LIGHT_BLUE, mode_button)
    pygame.draw.rect(screen, WHITE, mode_button, 2)
    mode_text = font.render("모드 선택", True, BLACK)
    screen.blit(mode_text, (mode_button.centerx - mode_text.get_width()//2, 
                           mode_button.centery - mode_text.get_height()//2))
    
    # 끝내기 버튼
    quit_button = pygame.Rect(start_x + (button_width + button_margin) * 2, buttons_y, button_width, button_height)
    pygame.draw.rect(screen, RED, quit_button)
    pygame.draw.rect(screen, WHITE, quit_button, 2)
    quit_text = font.render("끝내기", True, WHITE)
    screen.blit(quit_text, (quit_button.centerx - quit_text.get_width()//2, 
                           quit_button.centery - quit_text.get_height()//2))
    
    # 단축키 안내
    shortcut_font = pygame.font.SysFont("malgun gothic", 20)
    shortcuts = [
        ("R: 재시작", GREEN),
        ("M: 모드 선택", LIGHT_BLUE),
        ("ESC: 끝내기", RED)
    ]
    
    shortcut_y = buttons_y + button_height + 30
    for i, (text, color) in enumerate(shortcuts):
        shortcut_text = shortcut_font.render(text, True, color)
        x = start_x + (button_width + button_margin) * i + button_width//2 - shortcut_text.get_width()//2
        screen.blit(shortcut_text, (x, shortcut_y))
    
    pygame.display.flip()
    
    # 버튼 클릭 처리
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if restart_button.collidepoint(mouse_pos):
                    return "restart"
                elif mode_button.collidepoint(mouse_pos):
                    return "mode_select"
                elif quit_button.collidepoint(mouse_pos):
                    return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                elif event.key == pygame.K_m:
                    return "mode_select"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
    
    return None

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
    font = pygame.font.SysFont("malgun gothic", 20)
    
    # 정보 텍스트 렌더링
    phase_text = font.render(f"Phase {boss.phase}", True, WHITE)
    pattern_text = font.render(f"{boss.pattern}", True, BOSS_PATTERNS[boss.pattern]["color"])
    time_text = font.render(f"Time: {boss.survival_time//15}s", True, WHITE)
    
    # 텍스트 위치 계산 (체력바 아래 좌우로 분산 배치)
    text_y = y + height + 5
    screen.blit(phase_text, (x, text_y))  # 왼쪽
    screen.blit(pattern_text, (x + bar_width - pattern_text.get_width(), text_y))  # 오른쪽
    screen.blit(time_text, (x + (bar_width - time_text.get_width()) // 2, text_y))  # 중앙
    
    # 투사체 그리기
    for projectile in boss.projectiles:
        pygame.draw.rect(screen, projectile.color, 
                        (projectile.x, projectile.y, projectile.size, projectile.size))

def main():
    """
    게임 메인 함수
    게임 초기화 및 실행을 담당
    """
    install_requirements()
    
    while True:
        game_mode = mode_select_screen()
        next_action = game_loop(game_mode)
        
        if next_action == "mode_select":
            continue
        elif next_action == "restart":
            game_loop(game_mode)
        elif next_action == "quit":
            break
        else:
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()