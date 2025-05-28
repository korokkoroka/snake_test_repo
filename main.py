"""
Snake Game - 메인 게임 파일
게임의 실행과 UI를 담당하는 메인 파일입니다.

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
    GRAY, MAX_STAT_LEVEL
)

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
        str: 선택된 게임 모드 ("CLASSIC", "EVOLUTION", "SIMULATION")
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
        mode3 = font.render("3. 시뮬레이션 모드", True, WHITE)
        
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
                    return "SIMULATION"
        clock.tick(30)

def handle_evolution(screen, player, event):
    """진화 선택을 처리하는 함수"""
    if event.type != pygame.KEYDOWN:
        return True
        
    if event.key == pygame.K_ESCAPE:
        return False
    
    if player.level >= 10:
        if event.key == pygame.K_1:
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
        game_mode: str - 게임 모드 ("CLASSIC", "EVOLUTION", "SIMULATION")
        
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
        "SIMULATION": "Snake Game - Simulation Mode"
    }
    pygame.display.set_caption(caption[game_mode])
    clock = pygame.time.Clock()

    # 게임 객체 초기화
    player = Snake(WIDTH//4, HEIGHT//2, color=GREEN, name="YOU")
    snakes = [player]
    food_list = []  # food_list 초기화
    
    # AI 스네이크 초기화
    if game_mode == "CLASSIC":
        spawn_ai_snake(snakes)
    else:
        for _ in range(3):
            spawn_ai_snake(snakes)

    # 초기 음식 생성
    for _ in range(10):
        spawn_food(food_list, snakes)

    # 게임 상태 변수 초기화
    ai_timer = 0
    ai_check_timer = 0
    item_timer = 0
    special_item_timer = 0
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
        item_timer += 1
        special_item_timer += 1

        # 게임 상태 업데이트
        if not evolution_ui_active:
            # AI 관리 (클래식 모드 제외)
            if game_mode != "CLASSIC":
                update_ai_population(snakes, ai_check_timer, ai_timer)

            # 아이템 생성 (클래식 모드 제외)
            if game_mode != "CLASSIC":
                update_items(food_list, snakes, item_timer, special_item_timer)

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
        
        # 진화 UI 처리 (진화 모드)
        if game_mode == "EVOLUTION":
            evolution_ui_active, evolution_ui_just_activated = handle_evolution_ui(
                screen, player, evolution_ui_active, evolution_ui_just_activated)

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event, game_mode, player, evolution_ui_active, screen)

        # 게임 오버 체크
        if not player.alive:
            handle_game_over(screen, player)
            running = False

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
        
    기능:
        - 일정 시간마다 일반 아이템 생성
        - 일정 시간마다 특수 아이템 생성
    """
    if item_timer >= 400:
        spawn_food(food_list, snakes, is_item=True)
        item_timer = 0
        
    if special_item_timer >= 450:
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
        - 시뮬레이션 모드 여부에 따른 동작 조정
    """
    for snake in snakes:
        if snake.alive:
            snake.update_effects()
            snake.move(food_list, snakes, tick, game_mode == "SIMULATION")

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
        - 모든 뱀 렌더링 (시뮬레이션 모드에서는 감정 표현 포함)
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
        draw_snake(screen, snake, show_emotion=(game_mode == "SIMULATION"))

def draw_game_ui(screen, player, snakes, game_mode, food_list):
    """
    게임 UI를 화면에 표시하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        player: Snake - 플레이어 객체
        snakes: list - 게임 내 모든 뱀 목록
        game_mode: str - 현재 게임 모드
        food_list: list - 게임 내 모든 음식/아이템 목록
        
    기능:
        - 기본 UI 요소 표시 (리더보드, 에너지 바)
        - 게임 모드별 특수 UI 표시
        - 대시 쿨다운 표시 (해당하는 경우)
    """
    # 기본 UI
    draw_leaderboard(screen, snakes)
    draw_energy_bar(screen, player)
    
    # 진화 모드 UI
    if game_mode == "EVOLUTION":
        draw_stats(screen, player)
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
        evolution_ui_just_activated = False

    if evolution_ui_active:
        evolution_ui_active = draw_evolution_ui(screen, player)
    
    return evolution_ui_active, evolution_ui_just_activated

def draw_stat_window(screen, snake):
    """
    스탯 업그레이드 창을 표시하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        snake: Snake - 스탯을 표시할 뱀 객체
    """
    # 창 크기와 위치 설정
    window_width = 300
    window_height = 400
    x = (WIDTH - window_width) // 2
    y = (HEIGHT - window_height) // 2
    
    # 반투명 오버레이
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # 창 배경
    pygame.draw.rect(screen, (50, 50, 50), (x, y, window_width, window_height))
    pygame.draw.rect(screen, WHITE, (x, y, window_width, window_height), 2)
    
    # 제목
    font_large = pygame.font.SysFont("malgun gothic", 30)
    font = pygame.font.SysFont("malgun gothic", 20)
    title = font_large.render("스탯 업그레이드", True, WHITE)
    screen.blit(title, (x + (window_width - title.get_width()) // 2, y + 20))
    
    # 스탯 포인트 표시
    points_text = font.render(f"남은 스탯 포인트: {snake.stat_points}", True, WHITE)
    screen.blit(points_text, (x + 20, y + 70))
    
    # 스탯 목록
    stats = [
        ("이동속도 (1)", "SPEED", "이동속도 20% 증가"),
        ("에너지 (2)", "ENERGY", "최대 에너지 20 증가, 소모량 15% 감소"),
        ("공격력 (3)", "STRENGTH", "전투력 증가"),
        ("방어력 (4)", "DEFENSE", "충돌 내성 증가")
    ]
    
    for i, (name, stat, desc) in enumerate(stats):
        y_pos = y + 120 + i * 60
        
        # 스탯 이름과 레벨
        stat_text = font.render(f"{name}: {snake.stats[stat]}/{MAX_STAT_LEVEL}", True, WHITE)
        screen.blit(stat_text, (x + 20, y_pos))
        
        # 설명
        desc_text = font.render(desc, True, GRAY)
        screen.blit(desc_text, (x + 20, y_pos + 25))
        
        # 레벨 바
        bar_width = 200
        pygame.draw.rect(screen, (100, 100, 100), 
                        (x + 20, y_pos + 45, bar_width, 5))
        pygame.draw.rect(screen, GREEN, 
                        (x + 20, y_pos + 45, 
                         bar_width * (snake.stats[stat] / MAX_STAT_LEVEL), 5))
    
    # 안내 메시지
    guide = font.render("ESC: 닫기", True, WHITE)
    screen.blit(guide, (x + 20, y + window_height - 40))

def handle_keydown(event, game_mode, player, evolution_ui_active, screen):
    """
    키 입력을 처리하는 함수
    
    매개변수:
        event: pygame.event.Event - 키 이벤트
        game_mode: str - 현재 게임 모드
        player: Snake - 플레이어 객체
        evolution_ui_active: bool - 진화 UI 활성화 상태
        screen: pygame.Surface - 게임 화면
        
    기능:
        - 진화 모드에서의 진화 UI 관련 키 처리
        - 이동 방향 키 처리
        - 대시 키 처리
        - 진화 모드에서의 스탯 업그레이드 키 처리
    """
    if game_mode == "EVOLUTION" and evolution_ui_active:
        evolution_ui_active = handle_evolution(screen, player, event)
        if not evolution_ui_active:
            evolution_ui_just_activated = False
    else:
        if event.key in [pygame.K_UP, pygame.K_w]: player.direction = 'UP'
        elif event.key in [pygame.K_DOWN, pygame.K_s]: player.direction = 'DOWN'
        elif event.key in [pygame.K_LEFT, pygame.K_a]: player.direction = 'LEFT'
        elif event.key in [pygame.K_RIGHT, pygame.K_d]: player.direction = 'RIGHT'
        elif event.key == pygame.K_SPACE:
            player.dash()
        elif event.key == pygame.K_TAB and game_mode == "EVOLUTION":
            # 스탯 창 표시
            draw_stat_window(screen, player)
            pygame.display.flip()
            waiting_for_close = True
            while waiting_for_close:
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            waiting_for_close = False
                        elif e.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            if e.key == pygame.K_1: player.upgrade_stat("SPEED")
                            elif e.key == pygame.K_2: player.upgrade_stat("ENERGY")
                            elif e.key == pygame.K_3: player.upgrade_stat("STRENGTH")
                            elif e.key == pygame.K_4: player.upgrade_stat("DEFENSE")
                            draw_stat_window(screen, player)
                            pygame.display.flip()
                    elif e.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

def handle_game_over(screen, player):
    """
    게임 오버 상태를 처리하는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        player: Snake - 플레이어 객체
        
    기능:
        - 최종 점수 저장
        - 게임 오버 메시지 표시
        - 게임 종료 대기
    """
    save_score(player.name, player.score)
    font = pygame.font.SysFont(None, 72)
    text = font.render("GAME OVER", True, RED)
    screen.blit(text, (WIDTH//2 - 150, HEIGHT//2 - 36))
    pygame.display.flip()
    pygame.time.wait(3000)

def main():
    """
    게임 메인 함수
    게임 초기화 및 실행을 담당
    """
    install_requirements()
    game_mode = mode_select_screen()
    game_loop(game_mode)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()