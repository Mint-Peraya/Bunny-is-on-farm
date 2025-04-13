import pygame
import csv
import hashlib
import os
import sys
import math
from pathlib import Path
from config import Config

class AuthSystem:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.data_file = Path("user_credentials.csv")
            self._ensure_data_file()
            pygame.init()
            self.screen = pygame.display.set_mode(Config.get('window'))
            pygame.display.set_caption("Bunny is on farm - Welcome!")
            self.clock = pygame.time.Clock()
            self.running = True
            
            # Initialize all attributes
            self.message = ""
            self.message_color = (0, 0, 0)
            self.auth_mode = "login"
            self.username = ""
            self.password = ""
            self.confirm_password = ""
            self.active_field = None
            self.show_password = False
            
            # Color palette
            self.BG_COLOR = (234, 232, 205)  # Cream parchment
            self.TEXT_COLOR = (88, 72, 56)   # Dark brown
            self.ACTIVE_COLOR = (113, 179, 113)  # Leaf green
            self.INACTIVE_COLOR = (181, 172, 156)  # Stone gray
            self.BUTTON_COLOR = (242, 191, 96)  # Golden wheat
            self.ERROR_COLOR = (219, 88, 86)   # Tomato red
            self.SUCCESS_COLOR = (106, 168, 79)  # Apple green
            self.TRANSITION_COLOR = (255, 228, 181)  # Light orange for transition
            
            # Fonts
            self._load_fonts()
            
            # UI Setup
            self._setup_ui_positions()
            
            # Animation
            self.bunny_frame = 0
            self.bunny_animation_time = 0
            self.cloud_pos = -200
            self.transition_progress = 1  # Start with no transition
            self.transition_speed = 0.08  # Faster transition
            self.transition_alpha = 0

            # Create all visual elements
            self._create_visual_elements()

    def _create_visual_elements(self):
        """Create all visual elements with image fallbacks"""
        # Try to load bunny frames from images
        self.bunny_frames = []
        try:
            for i in range(4):
                img = pygame.image.load(f"assets/images/bunny_frame_{i}.png").convert_alpha()
                img = pygame.transform.scale(img, (80, 80))
                self.bunny_frames.append(img)
        except:
            # Fallback to drawn bunny frames if images not found
            self.bunny_frames = []
            for i in range(4):
                surf = pygame.Surface((80, 80), pygame.SRCALPHA)
                # Draw bunny body
                pygame.draw.ellipse(surf, (200, 200, 200), (10, 20, 60, 50))
                # Draw head
                pygame.draw.circle(surf, (220, 220, 220), (40, 30), 20)
                # Draw ears (animate them)
                ear_y_offset = 5 * math.sin(i * math.pi/2)
                pygame.draw.ellipse(surf, (220, 220, 220), (25, 5 - ear_y_offset, 10, 25))
                pygame.draw.ellipse(surf, (220, 220, 220), (45, 5 + ear_y_offset, 10, 25))
                # Draw face
                pygame.draw.circle(surf, (0, 0, 0), (30, 25), 3)  # Left eye
                pygame.draw.circle(surf, (0, 0, 0), (50, 25), 3)  # Right eye
                pygame.draw.arc(surf, (0, 0, 0), (30, 35, 20, 10), 0, math.pi, 2)  # Mouth
                self.bunny_frames.append(surf)
        
        # Try to load cloud image
        try:
            self.cloud = pygame.image.load("assets/images/cloud.png").convert_alpha()
            self.cloud = pygame.transform.scale(self.cloud, (200, 100))
        except:
            # Fallback to drawn cloud
            self.cloud = pygame.Surface((200, 100), pygame.SRCALPHA)
            pygame.draw.ellipse(self.cloud, (250, 250, 250), (0, 20, 180, 60))
            pygame.draw.ellipse(self.cloud, (250, 250, 250), (20, 0, 160, 80))
        
        # Try to load fence image
        try:
            self.fence = pygame.image.load("assets/images/fence.png").convert_alpha()
            self.fence = pygame.transform.scale(self.fence, (800, 60))
        except:
            # Fallback to drawn fence
            self.fence = pygame.Surface((800, 60), pygame.SRCALPHA)
            for x in range(0, 800, 50):
                pygame.draw.rect(self.fence, (150, 100, 50), (x, 10, 30, 50), 0, 5)
                pygame.draw.rect(self.fence, (100, 70, 30), (x, 10, 30, 50), 2, 5)
        
        # Try to load carrot image
        try:
            self.carrot = pygame.image.load("assets/images/carrot.png").convert_alpha()
            self.carrot = pygame.transform.scale(self.carrot, (40, 40))
        except:
            # Fallback to drawn carrot
            self.carrot = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(self.carrot, (255, 140, 0), [(20, 0), (5, 35), (35, 35)])
            pygame.draw.rect(self.carrot, (50, 120, 50), (18, 0, 4, 10))
        
        # Eye icon for password visibility
        try:
            self.eye_open = pygame.image.load("assets/images/eye_open.png").convert_alpha()
            self.eye_open = pygame.transform.scale(self.eye_open, (30, 20))
            self.eye_closed = pygame.image.load("assets/images/eye_closed.png").convert_alpha()
            self.eye_closed = pygame.transform.scale(self.eye_closed, (30, 20))
        except:
            # Fallback to drawn eye icons
            self.eye_open = pygame.Surface((30, 20), pygame.SRCALPHA)
            pygame.draw.circle(self.eye_open, (100, 100, 100), (15, 10), 8)
            pygame.draw.circle(self.eye_open, (50, 50, 150), (15, 10), 5)
            pygame.draw.circle(self.eye_open, (0, 0, 0), (15, 10), 2)
            pygame.draw.arc(self.eye_open, (100, 100, 100), (5, 0, 20, 20), 0, math.pi, 2)
            
            self.eye_closed = pygame.Surface((30, 20), pygame.SRCALPHA)
            pygame.draw.line(self.eye_closed, (100, 100, 100), (5, 10), (25, 10), 3)
        
        # Background
        try:
            self.field_bg = pygame.image.load("assets/images/field_bg.png").convert()
            self.field_bg = pygame.transform.scale(self.field_bg, Config.get('window'))
        except:
            # Fallback to drawn background
            self.field_bg = pygame.Surface(Config.get('window'))
            self.field_bg.fill(self.BG_COLOR)
            # Draw some grass
            for x in range(0, Config.get('window')[0], 10):
                pygame.draw.line(self.field_bg, (140, 190, 100), (x, Config.get('window')[1]), 
                                (x + 5, Config.get('window')[1] - 10), 2)

    # ... [rest of the methods remain exactly the same as in the previous version] ...

if __name__ == "__main__":
    auth = AuthSystem()
    auth.run()