import pygame
import os

class FontManager:
    """크로스 플랫폼 폰트 관리 클래스"""
    
    def __init__(self):
        self.local_font_path = "fonts/NotoSansKR-Variable.ttf"
        self.font_available = os.path.exists(self.local_font_path)
        
        if self.font_available:
            print(f"✅ 로컬 폰트 파일 발견: {self.local_font_path}")
        else:
            print(f"❌ 로컬 폰트 파일 없음, 시스템 폰트 사용")
    
    def get_font(self, font_type, size, bold=False):
        """지정된 타입과 크기의 폰트 반환"""
        try:
            if self.font_available:
                return pygame.font.Font(self.local_font_path, size)
            else:
                return pygame.font.SysFont("Arial", size, bold=bold)
        except:
            return pygame.font.Font(None, size)

# 전역 폰트 매니저 인스턴스
font_manager = None

def get_font_manager():
    """폰트 매니저 싱글톤 반환"""
    global font_manager
    if font_manager is None:
        font_manager = FontManager()
    return font_manager 