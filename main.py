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
import json
import os
from datetime import datetime
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
from font_manager import get_font_manager

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

    fm = get_font_manager()

    # 부드러운 반투명 오버레이
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # 진화 메뉴 크기 및 위치 (높이 늘림)
    menu_width, menu_height = 700, 550
    menu_x = (WIDTH - menu_width) // 2
    menu_y = (HEIGHT - menu_height) // 2
    
    # 메인 패널 - 둥근 모서리와 그라데이션 효과
    panel_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
    
    # 배경 그라데이션 효과 (어두운 파란색에서 검은색으로)
    for i in range(menu_height):
        alpha = 200 - (i * 50 // menu_height)  # 위에서 아래로 점점 투명해짐
        color_intensity = 40 - (i * 20 // menu_height)  # 위에서 아래로 점점 어두워짐
        line_color = (color_intensity, color_intensity, color_intensity + 10, alpha)
        pygame.draw.line(panel_surface, line_color, (0, i), (menu_width, i))
    
    # 둥근 모서리 적용
    draw_rounded_rect(panel_surface, (30, 30, 45, 220), (0, 0, menu_width, menu_height), 20)
    
    # 테두리 (미묘한 글로우 효과)
    border_surface = pygame.Surface((menu_width + 4, menu_height + 4), pygame.SRCALPHA)
    draw_rounded_rect(border_surface, (100, 150, 255, 100), (0, 0, menu_width + 4, menu_height + 4), 22)
    screen.blit(border_surface, (menu_x - 2, menu_y - 2))
    screen.blit(panel_surface, (menu_x, menu_y))

    # 제목 - 한국어로 변경
    title_font = fm.get_font('title', 42, bold=True)
    subtitle_font = fm.get_font('button', 18)
    
    title_text = "진화 선택"
    subtitle_text = "다음 형태를 선택하세요"
    
    # 제목 그림자 효과
    title_shadow = title_font.render(title_text, True, (0, 0, 0, 150))
    screen.blit(title_shadow, (menu_x + (menu_width - title_shadow.get_width()) // 2 + 2, menu_y + 32))
    
    # 제목 메인 텍스트 (그라데이션 색상)
    title_main = title_font.render(title_text, True, (255, 255, 255))
    screen.blit(title_main, (menu_x + (menu_width - title_main.get_width()) // 2, menu_y + 30))
    
    # 서브타이틀
    subtitle_main = subtitle_font.render(subtitle_text, True, (180, 180, 200))
    screen.blit(subtitle_main, (menu_x + (menu_width - subtitle_main.get_width()) // 2, menu_y + 80))

    # 진화 옵션 표시
    available_forms = []
    if snake.level >= 10:
        available_forms = ["ULTIMATE"]
    elif snake.level >= 5:
        available_forms = ["SPEEDER", "TANK", "HUNTER"]

    # 옵션 카드들 (위치 조정)
    card_width = menu_width - 80
    card_height = 85  # 높이 약간 줄임
    start_y = menu_y + 120  # 시작 위치 조정
    
    name_font = fm.get_font('button', 24, bold=True)
    desc_font = fm.get_font('small', 16)
    key_font = fm.get_font('button', 20, bold=True)

    for i, form in enumerate(available_forms):
        form_data = EVOLUTION_FORMS[form]
        card_y = start_y + i * (card_height + 12)  # 카드 간격 줄임
        
        # 카드 배경 - 진화 형태 색상에 맞는 그라데이션
        card_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        
        # 형태별 배경색 (반투명)
        base_color = form_data["color"]
        bg_color = (base_color[0], base_color[1], base_color[2], 60)
        border_color = (base_color[0], base_color[1], base_color[2], 180)
        
        # 카드 배경
        draw_rounded_rect(card_surface, bg_color, (0, 0, card_width, card_height), 12)
        draw_rounded_rect(card_surface, border_color, (0, 0, card_width, card_height), 12)
        
        # 왼쪽 색상 스트라이프
        stripe_surface = pygame.Surface((8, card_height - 4), pygame.SRCALPHA)
        stripe_surface.fill(border_color)
        card_surface.blit(stripe_surface, (2, 2))
        
        screen.blit(card_surface, (menu_x + 40, card_y))
        
        # 키 번호 (왼쪽 상단 원형 배지)
        key_radius = 15
        key_center = (menu_x + 65, card_y + 20)
        pygame.draw.circle(screen, border_color, key_center, key_radius)
        pygame.draw.circle(screen, (255, 255, 255), key_center, key_radius - 2)
        
        key_text = key_font.render(str(i + 1), True, base_color)
        key_rect = key_text.get_rect(center=key_center)
        screen.blit(key_text, key_rect)
        
        # 진화 형태 이름
        name_x = menu_x + 95
        name_y = card_y + 12  # 위치 조정
        
        name_text = name_font.render(form, True, (255, 255, 255))
        screen.blit(name_text, (name_x, name_y))
        
        # 설명 텍스트
        desc_text = form_data["description"]
        desc_render = desc_font.render(desc_text, True, (200, 200, 220))
        screen.blit(desc_render, (name_x, name_y + 26))  # 위치 조정
        
        # 능력 목록 (작은 태그 형태)
        abilities_y = name_y + 48  # 위치 조정
        tag_x = name_x
        
        for j, ability in enumerate(form_data["abilities"]):
            # 각 능력을 작은 태그로 표시
            ability_text = desc_font.render(ability, True, (255, 255, 255))
            tag_width = ability_text.get_width() + 16
            tag_height = 18  # 높이 줄임
            
            # 태그 배경
            tag_surface = pygame.Surface((tag_width, tag_height), pygame.SRCALPHA)
            draw_rounded_rect(tag_surface, (base_color[0], base_color[1], base_color[2], 120), (0, 0, tag_width, tag_height), 9)
            screen.blit(tag_surface, (tag_x, abilities_y))
            
            # 태그 텍스트
            text_rect = ability_text.get_rect(center=(tag_x + tag_width // 2, abilities_y + tag_height // 2))
            screen.blit(ability_text, text_rect)
            
            tag_x += tag_width + 8  # 다음 태그 위치
            
            # 한 줄에 너무 많으면 다음 줄로
            if tag_x > menu_x + card_width - 100:
                break

    # 하단 안내 메시지 - 위치 조정하여 겹치지 않도록
    guide_y = menu_y + menu_height - 70  # 위치 조정
    guide_surface = pygame.Surface((menu_width - 40, 55), pygame.SRCALPHA)  # 크기 조정
    draw_rounded_rect(guide_surface, (0, 0, 0, 100), (0, 0, menu_width - 40, 55), 15)
    screen.blit(guide_surface, (menu_x + 20, guide_y))
    
    # 안내 텍스트들 - 한국어로 변경
    guide_font = fm.get_font('small', 18)
    guide_lines = [
        "숫자 키(1-3)를 눌러 진화 선택",
        "ESC: 취소하고 현재 형태 유지"
    ]
    
    for i, line in enumerate(guide_lines):
        if i == 0:  # 첫 번째 줄은 강조
            text_color = (255, 255, 100)
        else:  # 두 번째 줄은 부드럽게
            text_color = (180, 180, 200)
            
        guide_text = guide_font.render(line, True, text_color)
        text_x = menu_x + (menu_width - guide_text.get_width()) // 2
        text_y = guide_y + 10 + i * 20  # 간격 조정
        screen.blit(guide_text, (text_x, text_y))

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
    fm = get_font_manager()
    
    # 상태 UI 배경
    status_width = 200
    pygame.draw.rect(screen, (0, 0, 0, 128), (20, 80, status_width, 100))
    
    # 레벨과 경험치 표시
    font = fm.get_font('button', 20)
    level_text = font.render(f"Level: {snake.level}", True, WHITE)
    exp_text = font.render(f"EXP: {snake.exp}/{snake.exp_to_level}", True, WHITE)
    form_text = font.render(f"Form: {snake.evolution_form}", True, 
                           EVOLUTION_FORMS[snake.evolution_form]["color"])
    
    screen.blit(level_text, (30, 90))
    screen.blit(exp_text, (30, 115))
    screen.blit(form_text, (30, 140))
    
    # 경험치 바
    exp_ratio = snake.exp / snake.exp_to_level
    bar_bg_rect = (30, 165, status_width - 20, 5)
    bar_fill_rect = (30, 165, (status_width - 20) * exp_ratio, 5)
    
    # 둥근 모서리로 경험치 바 그리기
    draw_rounded_rect(screen, (50, 50, 50), bar_bg_rect, 3)
    draw_rounded_rect(screen, (0, 255, 0), bar_fill_rect, 3)

def mode_select_screen():
    """
    게임 모드 선택 화면 표시
    
    Returns:
        str: 선택된 게임 모드 ("CLASSIC", "EVOLUTION", "BOSS")
    """
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake Game - Mode Selection")
    clock = pygame.time.Clock()
    
    fm = get_font_manager()
    title_font = fm.get_font('title', 48, bold=True)
    button_font = fm.get_font('button', 24)
    desc_font = fm.get_font('small', 18)
    
    # 버튼 정보
    modes = [
        {"name": "클래식 모드", "desc": "기본 뱀 게임 + 대시 기능", "mode": "CLASSIC"},
        {"name": "진화 모드", "desc": "레벨업과 진화 시스템", "mode": "EVOLUTION"},
        {"name": "보스전 모드", "desc": "강력한 보스와의 전투", "mode": "BOSS"}
    ]
    
    selected_index = 0  # 현재 선택된 버튼 인덱스
    button_height = 80
    button_width = 400
    button_margin = 20
    
    # 버튼 위치 계산
    total_height = len(modes) * button_height + (len(modes) - 1) * button_margin
    start_y = (HEIGHT - total_height) // 2 + 50
    button_x = (WIDTH - button_width) // 2
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(modes)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(modes)
                elif event.key == pygame.K_RETURN:
                    return modes[selected_index]["mode"]
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # 숫자 키로도 선택 가능
                elif event.key == pygame.K_1:
                    return "CLASSIC"
                elif event.key == pygame.K_2:
                    return "EVOLUTION"
                elif event.key == pygame.K_3:
                    return "BOSS"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 왼쪽 클릭
                    for i, mode in enumerate(modes):
                        button_y = start_y + i * (button_height + button_margin)
                        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                        if button_rect.collidepoint(mouse_pos):
                            return mode["mode"]
            elif event.type == pygame.MOUSEMOTION:
                # 마우스가 버튼 위에 있으면 선택 상태 변경
                for i, mode in enumerate(modes):
                    button_y = start_y + i * (button_height + button_margin)
                    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                    if button_rect.collidepoint(mouse_pos):
                        selected_index = i
                        break
        
        # 화면 그리기
        screen.fill(BLACK)
        
        # 로고 이미지 표시
        try:
            logo_image = pygame.image.load("logo.png")
            # 로고 크기 조정 (원본 크기가 너무 클 경우를 대비)
            logo_rect = logo_image.get_rect()
            max_width = WIDTH // 2  # 화면 너비의 절반으로 제한
            max_height = HEIGHT // 4  # 화면 높이의 1/4로 제한
            
            # 비율을 유지하면서 크기 조정
            if logo_rect.width > max_width or logo_rect.height > max_height:
                scale_x = max_width / logo_rect.width
                scale_y = max_height / logo_rect.height
                scale = min(scale_x, scale_y)  # 더 작은 스케일 사용하여 비율 유지
                
                new_width = int(logo_rect.width * scale)
                new_height = int(logo_rect.height * scale)
                logo_image = pygame.transform.scale(logo_image, (new_width, new_height))
            
            # 로고를 화면 중앙 상단에 배치
            logo_rect = logo_image.get_rect(center=(WIDTH//2, HEIGHT//4))
            screen.blit(logo_image, logo_rect)
            
        except (pygame.error, FileNotFoundError):
            # 로고 파일이 없거나 로드할 수 없는 경우 기본 텍스트 표시
            title = title_font.render("뱀 게임", True, WHITE)
            title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//4))
            screen.blit(title, title_rect)
        
        # 버튼들 그리기
        for i, mode in enumerate(modes):
            button_y = start_y + i * (button_height + button_margin)
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # 선택된 버튼인지 확인
            is_selected = (i == selected_index)
            is_hovered = button_rect.collidepoint(mouse_pos)
            
            # 버튼 색상 결정
            if is_selected:
                button_color = (80, 120, 200)  # 파란색
                border_color = (120, 160, 255)  # 밝은 파란색
                text_color = WHITE
            elif is_hovered:
                button_color = (60, 60, 60)  # 어두운 회색
                border_color = (100, 100, 100)  # 회색
                text_color = WHITE
            else:
                button_color = (40, 40, 40)  # 매우 어두운 회색
                border_color = (70, 70, 70)  # 회색
                text_color = GRAY
            
            # 버튼 배경 (테두리 포함)
            draw_rounded_rect(screen, border_color, button_rect, 12)
            # 버튼 내부 (테두리를 위해 2픽셀 작게)
            inner_rect = (button_rect.x + 2, button_rect.y + 2, button_rect.width - 4, button_rect.height - 4)
            draw_rounded_rect(screen, button_color, inner_rect, 10)
            
            # 버튼 텍스트
            mode_text = button_font.render(mode["name"], True, text_color)
            desc_text = desc_font.render(mode["desc"], True, text_color)
            
            # 텍스트 중앙 정렬
            mode_rect = mode_text.get_rect(center=(button_rect.centerx, button_rect.centery - 12))
            desc_rect = desc_text.get_rect(center=(button_rect.centerx, button_rect.centery + 12))
            
            screen.blit(mode_text, mode_rect)
            screen.blit(desc_text, desc_rect)
            
            # 선택된 버튼에 화살표 표시
            if is_selected:
                arrow_font = fm.get_font('button', 24)
                left_arrow = arrow_font.render("▶", True, WHITE)
                right_arrow = arrow_font.render("◀", True, WHITE)
                screen.blit(left_arrow, (button_x - 30, button_rect.centery - 12))
                screen.blit(right_arrow, (button_x + button_width + 10, button_rect.centery - 12))
        
        # 조작 안내
        help_y = HEIGHT - 100
        help_texts = [
            "↑↓ 키: 선택",
            "Enter: 확인",
            "마우스: 클릭하여 선택",
            "ESC: 게임 종료"
        ]
        
        for i, help_text in enumerate(help_texts):
            help_surface = desc_font.render(help_text, True, GRAY)
            help_rect = help_surface.get_rect(center=(WIDTH//2, help_y + i * 20))
            screen.blit(help_surface, help_rect)
        
        pygame.display.flip()
        clock.tick(60)

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
                if event.key == pygame.K_ESCAPE and not evolution_ui_active:
                    # 일시정지 화면 표시
                    pause_action = draw_pause_screen(screen)
                    if pause_action == "restart":
                        return "restart"
                    elif pause_action == "quit":
                        return "mode_select"
                    # "resume"이면 계속 진행
                elif game_mode == "BOSS" and event.key == pygame.K_f:
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
    fm = get_font_manager()
    
    # 기본 UI (보스 모드가 아닐 때만 리더보드 표시)
    if game_mode != "BOSS":
        draw_leaderboard(screen, snakes)
    draw_energy_bar(screen, player)
    
    # 메시지 표시
    for snake in snakes:
        if snake.message and snake.message_duration > 0:
            font = fm.get_font('button', 24)
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
        font = fm.get_font('small', 20)
        
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
            font = fm.get_font('button', 24)
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
    # 창 크기와 위치 설정 (크기 증가)
    window_width = 450  # 300에서 450으로 증가
    window_height = 380  # 300에서 380으로 증가
    x = (WIDTH - window_width) // 2
    y = (HEIGHT - window_height) // 2
    
    # 반투명 창 배경
    window_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    pygame.draw.rect(window_surface, (50, 50, 50, 180), (0, 0, window_width, window_height))
    pygame.draw.rect(window_surface, (255, 255, 255, 180), (0, 0, window_width, window_height), 2)
    
    # 폰트 매니저 사용
    fm = get_font_manager()
    font_large = fm.get_font('title', 32, bold=True)  # 폰트 크기 증가
    font = fm.get_font('button', 22)  # 폰트 크기 증가
    
    title = font_large.render("스탯 업그레이드", True, (255, 255, 255, 180))
    title_surface = pygame.Surface(title.get_size(), pygame.SRCALPHA)
    title_surface.blit(title, (0, 0))
    window_surface.blit(title_surface, ((window_width - title.get_width()) // 2, 25))  # 위치 조정
    
    # 스탯 포인트 표시
    points_text = font.render(f"남은 스탯 포인트: {snake.stat_points}", True, (255, 255, 255, 180))
    points_surface = pygame.Surface(points_text.get_size(), pygame.SRCALPHA)
    points_surface.blit(points_text, (0, 0))
    window_surface.blit(points_surface, (30, 80))  # 여백 증가
    
    # 스탯 목록 (방어력과 공격력 제거)
    stats = [
        ("이동속도 (1)", "SPEED", "이동속도 20% 증가"),
        ("에너지 (2)", "ENERGY", "최대 에너지 20 증가, 소모량 15% 감소")
    ]
    
    for i, (name, stat, desc) in enumerate(stats):
        y_pos = 140 + i * 90  # 간격 증가 (60에서 90으로)
        
        # 스탯 이름과 레벨
        stat_text = font.render(f"{name}: {snake.stats[stat]}/{MAX_STAT_LEVEL}", True, (255, 255, 255, 180))
        stat_surface = pygame.Surface(stat_text.get_size(), pygame.SRCALPHA)
        stat_surface.blit(stat_text, (0, 0))
        window_surface.blit(stat_surface, (30, y_pos))  # 여백 증가
        
        # 설명 (텍스트와 설명 사이 간격 증가)
        desc_text = font.render(desc, True, (200, 200, 200, 180))
        desc_surface = pygame.Surface(desc_text.get_size(), pygame.SRCALPHA)
        desc_surface.blit(desc_text, (0, 0))
        window_surface.blit(desc_surface, (30, y_pos + 30))  # 간격 증가 (25에서 30으로)
        
        # 레벨 바 (반투명) - 설명과 게이지 사이 간격 증가
        bar_width = 320  # 바 길이 증가 (200에서 320으로)
        bar_surface = pygame.Surface((bar_width, 8), pygame.SRCALPHA)  # 바 높이 증가 (5에서 8로)
        
        # 둥근 모서리로 레벨 바 그리기
        draw_rounded_rect(bar_surface, (100, 100, 100, 180), (0, 0, bar_width, 8), 4)  # 반지름 증가
        fill_width = bar_width * (snake.stats[stat] / MAX_STAT_LEVEL)
        draw_rounded_rect(bar_surface, (0, 255, 0, 180), (0, 0, fill_width, 8), 4)  # 반지름 증가
        
        window_surface.blit(bar_surface, (30, y_pos + 55))  # 간격 증가 (45에서 55로)
    
    # 안내 메시지 (위치 조정)
    guide = font.render("ESC: 닫기", True, (255, 255, 255, 180))
    guide_surface = pygame.Surface(guide.get_size(), pygame.SRCALPHA)
    guide_surface.blit(guide, (0, 0))
    window_surface.blit(guide_surface, (30, window_height - 50))  # 여백 증가
    
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
    
    # 폰트 매니저 사용
    fm = get_font_manager()
    font_large = fm.get_font('title', 72, bold=True)
    font = fm.get_font('button', 36)
    
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
    draw_rounded_rect(screen, WHITE, restart_button, 8)
    inner_rect = (restart_button.x + 2, restart_button.y + 2, restart_button.width - 4, restart_button.height - 4)
    draw_rounded_rect(screen, GREEN, inner_rect, 6)
    restart_text = font.render("재시작", True, BLACK)
    restart_rect = restart_text.get_rect(center=restart_button.center)
    screen.blit(restart_text, restart_rect)
    
    # 모드 선택 버튼
    mode_button = pygame.Rect(start_x + button_width + button_margin, buttons_y, button_width, button_height)
    draw_rounded_rect(screen, WHITE, mode_button, 8)
    inner_rect = (mode_button.x + 2, mode_button.y + 2, mode_button.width - 4, mode_button.height - 4)
    draw_rounded_rect(screen, LIGHT_BLUE, inner_rect, 6)
    mode_text = font.render("모드 선택", True, BLACK)
    mode_rect = mode_text.get_rect(center=mode_button.center)
    screen.blit(mode_text, mode_rect)
    
    # 끝내기 버튼
    quit_button = pygame.Rect(start_x + (button_width + button_margin) * 2, buttons_y, button_width, button_height)
    draw_rounded_rect(screen, WHITE, quit_button, 8)
    inner_rect = (quit_button.x + 2, quit_button.y + 2, quit_button.width - 4, quit_button.height - 4)
    draw_rounded_rect(screen, RED, inner_rect, 6)
    quit_text = font.render("끝내기", True, WHITE)
    quit_rect = quit_text.get_rect(center=quit_button.center)
    screen.blit(quit_text, quit_rect)
    
    # 단축키 안내
    shortcut_font = fm.get_font('small', 20)
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
    bg_rect = (x-2, y-2, bar_width+4, height+4)
    draw_rounded_rect(screen, (50, 50, 50), bg_rect, 5)
    
    # 체력바
    health_ratio = boss.health / boss.max_health
    health_width = int(bar_width * health_ratio)
    health_color = BOSS_PATTERNS[boss.pattern]["color"]
    health_rect = (x, y, health_width, height)
    draw_rounded_rect(screen, health_color, health_rect, 4)
    
    # 보스 정보
    fm = get_font_manager()
    font = fm.get_font('small', 20)
    
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

def draw_pause_screen(screen):
    """
    일시정지 화면을 그리는 함수
    
    매개변수:
        screen: pygame.Surface - 게임 화면
        
    반환값:
        str: 사용자 선택 ("resume", "restart", "quit", None)
    """
    fm = get_font_manager()
    
    # 반투명 오버레이
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # 제목
    title_font = fm.get_font('title', 48, bold=True)
    pause_text = title_font.render("일시정지", True, WHITE)
    title_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//3))
    screen.blit(pause_text, title_rect)
    
    # 버튼 설정
    button_font = fm.get_font('button', 24)
    button_width, button_height = 200, 60
    button_margin = 20
    
    # 버튼 위치 계산
    total_width = button_width * 3 + button_margin * 2
    start_x = (WIDTH - total_width) // 2
    buttons_y = HEIGHT//2 + 50
    
    # 계속하기 버튼
    resume_button = pygame.Rect(start_x, buttons_y, button_width, button_height)
    draw_rounded_rect(screen, WHITE, resume_button, 8)
    inner_rect = (resume_button.x + 2, resume_button.y + 2, resume_button.width - 4, resume_button.height - 4)
    draw_rounded_rect(screen, GREEN, inner_rect, 6)
    resume_text = button_font.render("계속하기", True, BLACK)
    resume_rect = resume_text.get_rect(center=resume_button.center)
    screen.blit(resume_text, resume_rect)
    
    # 다시하기 버튼
    restart_button = pygame.Rect(start_x + button_width + button_margin, buttons_y, button_width, button_height)
    draw_rounded_rect(screen, WHITE, restart_button, 8)
    inner_rect = (restart_button.x + 2, restart_button.y + 2, restart_button.width - 4, restart_button.height - 4)
    draw_rounded_rect(screen, LIGHT_BLUE, inner_rect, 6)
    restart_text = button_font.render("다시하기", True, BLACK)
    restart_rect = restart_text.get_rect(center=restart_button.center)
    screen.blit(restart_text, restart_rect)
    
    # 시작화면으로 이동 버튼
    quit_button = pygame.Rect(start_x + (button_width + button_margin) * 2, buttons_y, button_width, button_height)
    draw_rounded_rect(screen, WHITE, quit_button, 8)
    inner_rect = (quit_button.x + 2, quit_button.y + 2, quit_button.width - 4, quit_button.height - 4)
    draw_rounded_rect(screen, RED, inner_rect, 6)
    quit_text = button_font.render("시작화면으로 이동", True, WHITE)
    quit_rect = quit_text.get_rect(center=quit_button.center)
    screen.blit(quit_text, quit_rect)
    
    # 단축키 안내
    help_font = fm.get_font('small', 18)
    help_y = buttons_y + button_height + 40
    shortcuts = [
        ("ESC: 계속하기", GREEN),
        ("R: 다시하기", LIGHT_BLUE),
        ("Q: 시작화면으로", RED)
    ]
    
    for i, (text, color) in enumerate(shortcuts):
        help_text = help_font.render(text, True, color)
        x = start_x + (button_width + button_margin) * i + button_width//2 - help_text.get_width()//2
        screen.blit(help_text, (x, help_y))
    
    pygame.display.flip()
    
    # 이벤트 처리
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 왼쪽 클릭
                    mouse_pos = event.pos
                    if resume_button.collidepoint(mouse_pos):
                        return "resume"
                    elif restart_button.collidepoint(mouse_pos):
                        return "restart"
                    elif quit_button.collidepoint(mouse_pos):
                        return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
                elif event.key == pygame.K_r:
                    return "restart"
                elif event.key == pygame.K_q:
                    return "quit"

def draw_rounded_rect(surface, color, rect, border_radius):
    """
    둥근 모서리를 가진 사각형을 그리는 함수
    
    매개변수:
        surface: pygame.Surface - 그릴 표면
        color: tuple - 색상 (R, G, B) 또는 (R, G, B, A)
        rect: tuple - (x, y, width, height)
        border_radius: int - 모서리 둥글기 정도
    """
    x, y, width, height = rect
    
    # 둥글기가 너무 클 경우 조정
    border_radius = min(border_radius, width // 2, height // 2)
    
    if border_radius <= 0:
        pygame.draw.rect(surface, color, rect)
        return
    
    # pygame 2.0 이상에서는 border_radius 매개변수를 직접 사용
    try:
        pygame.draw.rect(surface, color, rect, border_radius=border_radius)
    except TypeError:
        # pygame 1.x 버전에서는 수동으로 둥근 사각형 그리기
        # 중앙 사각형
        pygame.draw.rect(surface, color, (x + border_radius, y, width - 2 * border_radius, height))
        pygame.draw.rect(surface, color, (x, y + border_radius, width, height - 2 * border_radius))
        
        # 모서리 원
        pygame.draw.circle(surface, color, (x + border_radius, y + border_radius), border_radius)
        pygame.draw.circle(surface, color, (x + width - border_radius, y + border_radius), border_radius)
        pygame.draw.circle(surface, color, (x + border_radius, y + height - border_radius), border_radius)
        pygame.draw.circle(surface, color, (x + width - border_radius, y + height - border_radius), border_radius)

def main():
    """
    게임 메인 함수
    게임 초기화 및 실행을 담당
    """
    install_requirements()
    
    while True:
        game_mode = mode_select_screen()
        
        # 선택한 모드로 게임을 계속 실행
        while True:
            next_action = game_loop(game_mode)
            
            if next_action == "mode_select":
                break  # 모드 선택 화면으로 돌아가기
            elif next_action == "restart":
                continue  # 같은 모드로 다시 시작
            elif next_action == "quit":
                pygame.quit()
                sys.exit()
            else:
                pygame.quit()
                sys.exit()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()