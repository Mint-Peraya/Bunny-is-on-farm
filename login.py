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
        """Create all visual elements with improved fallbacks"""
        # Bunny animation frames
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
        
        # Cloud
        self.cloud = pygame.Surface((200, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(self.cloud, (250, 250, 250), (0, 20, 180, 60))
        pygame.draw.ellipse(self.cloud, (250, 250, 250), (20, 0, 160, 80))
        
        # Fence
        self.fence = pygame.Surface((800, 60), pygame.SRCALPHA)
        for x in range(0, 800, 50):
            pygame.draw.rect(self.fence, (150, 100, 50), (x, 10, 30, 50), 0, 5)
            pygame.draw.rect(self.fence, (100, 70, 30), (x, 10, 30, 50), 2, 5)
        
        # Carrot
        self.carrot = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.carrot, (255, 140, 0), [(20, 0), (5, 35), (35, 35)])
        pygame.draw.rect(self.carrot, (50, 120, 50), (18, 0, 4, 10))
        
        # Background
        self.field_bg = pygame.Surface(Config.get('window'))
        self.field_bg.fill(self.BG_COLOR)
        # Draw some grass
        for x in range(0, Config.get('window')[0], 10):
            pygame.draw.line(self.field_bg, (140, 190, 100), (x, Config.get('window')[1]), 
                            (x + 5, Config.get('window')[1] - 10), 2)

    def _load_fonts(self):
        """Load fonts with better fallbacks"""
        try:
            self.title_font = pygame.font.Font("assets/fonts/pixel.ttf", 42)
            self.input_font = pygame.font.Font("assets/fonts/pixel.ttf", 28)
            self.button_font = pygame.font.Font("assets/fonts/pixel.ttf", 24)
            self.small_font = pygame.font.Font("assets/fonts/pixel.ttf", 20)
        except:
            # Create pixel-style fonts using pygame's default
            self.title_font = pygame.font.Font(None, 42)
            self.input_font = pygame.font.Font(None, 28)
            self.button_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 20)

    def _setup_ui_positions(self):
        """Initialize UI element positions with better spacing"""
        self.field_width = 350
        self.login_positions = {
            "username": pygame.Rect(225, 200, self.field_width, 40),
            "password": pygame.Rect(225, 280, self.field_width, 40),
            "confirm": pygame.Rect(225, 360, self.field_width, 40),
            "button": pygame.Rect(300, 450, 200, 50),
            "switch": pygame.Rect(250, 520, 300, 30)
        }
        self.signup_positions = {
            "username": pygame.Rect(225, 150, self.field_width, 40),
            "password": pygame.Rect(225, 230, self.field_width, 40),
            "confirm": pygame.Rect(225, 310, self.field_width, 40),
            "button": pygame.Rect(300, 400, 200, 50),
            "switch": pygame.Rect(250, 470, 300, 30)
        }
        self.current_positions = {k: v.copy() for k,v in self.login_positions.items()}

    def _ensure_data_file(self):
        """Create credentials file if missing"""
        if not self.data_file.exists():
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['username', 'password_hash'])

    def _hash_password(self, password, salt=None):
        """Securely hash password with PBKDF2"""
        if salt is None:
            salt = os.urandom(16).hex()
        iterations = 100000
        return f"{hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations).hex()}:{salt}:{iterations}"

    def _verify_password(self, stored_hash, input_password):
        """Verify password against stored hash"""
        try:
            hash_value, salt, iterations = stored_hash.split(':')
            new_hash = hashlib.pbkdf2_hmac(
                'sha256', 
                input_password.encode(),
                salt.encode(),
                int(iterations)
            ).hex()
            return hash_value == new_hash
        except:
            return False

    def register_user(self, username, password):
        """Register new user"""
        if self.user_exists(username):
            return False, "Username already taken!"
        with open(self.data_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, self._hash_password(password)])
        return True, "Welcome to Bunny Harvest!"

    def user_exists(self, username):
        """Check if username exists"""
        if not self.data_file.exists():
            return False
        with open(self.data_file, 'r') as f:
            return any(row and row[0] == username for row in csv.reader(f))

    def authenticate(self, username, password):
        """Verify login credentials"""
        with open(self.data_file, 'r') as f:
            for row in csv.reader(f):
                if row and row[0] == username:
                    if self._verify_password(row[1], password):
                        return True, "Welcome back!"
                    return False, "Wrong password!"
        return False, "Farmer not found!"

    def handle_events(self):
        """Process all events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

    def _handle_click(self, pos):
        """Handle mouse clicks"""
        self.active_field = None
        if self.current_positions["username"].collidepoint(pos):
            self.active_field = "username"
        elif self.current_positions["password"].collidepoint(pos):
            self.active_field = "password"
        elif self.auth_mode == "signup" and self.current_positions["confirm"].collidepoint(pos):
            self.active_field = "confirm"
        elif self.current_positions["button"].collidepoint(pos):
            self.attempt_auth()
        elif self.current_positions["switch"].collidepoint(pos):
            self.switch_mode()

    def _handle_keydown(self, event):
        """Handle keyboard input"""
        if not self.active_field:
            return
            
        # Map UI fields to actual attributes
        field_attr_map = {
            "username": "username",
            "password": "password",
            "confirm": "confirm_password"
        }
        
        field_attr = field_attr_map.get(self.active_field)
        if not field_attr:
            return
            
        max_len = 16 if field_attr == "username" else 20
        
        if event.key == pygame.K_RETURN:
            if self.active_field == "username":
                self.active_field = "password"
            elif self.active_field == "password" and self.auth_mode == "signup":
                self.active_field = "confirm"
            else:
                self.attempt_auth()
        elif event.key == pygame.K_BACKSPACE:
            setattr(self, field_attr, getattr(self, field_attr)[:-1])
        elif len(getattr(self, field_attr)) < max_len:
            setattr(self, field_attr, getattr(self, field_attr) + event.unicode)

    def switch_mode(self):
        """Toggle between login/signup with visual feedback"""
        self.auth_mode = "signup" if self.auth_mode == "login" else "login"
        self.transition_progress = 0
        self.transition_alpha = 255  # Start transition overlay
        
        if self.auth_mode == "signup":
            self.username = self.username[:16]
            self.password = self.password[:20]
        else:
            self.username = self.password = self.confirm_password = ""
        self.message = ""

    def attempt_auth(self):
        """Handle authentication attempts"""
        if not self.username:
            self.message = "Need a farmer name!"
            self.message_color = self.ERROR_COLOR
            return
        if not self.password:
            self.message = "Need a secret password!"
            self.message_color = self.ERROR_COLOR
            return
            
        if self.auth_mode == "signup":
            if self.password != self.confirm_password:
                self.message = "Passwords don't match!"
                self.message_color = self.ERROR_COLOR
                return
            if len(self.password) < 6:
                self.message = "Password too short! (min 6)"
                self.message_color = self.ERROR_COLOR
                return
                
            success, msg = self.register_user(self.username, self.password)
            self.message = msg
            self.message_color = self.SUCCESS_COLOR if success else self.ERROR_COLOR
            if success:
                pygame.time.delay(1500)
                self.switch_mode()
        else:
            success, msg = self.authenticate(self.username, self.password)
            self.message = msg
            self.message_color = self.SUCCESS_COLOR if success else self.ERROR_COLOR
            if success:
                pygame.time.delay(1000)
                self.quit()

    def update(self):
        """Update animations and transitions"""
        # Bunny animation
        self.bunny_animation_time += 1
        if self.bunny_animation_time >= 8:
            self.bunny_animation_time = 0
            self.bunny_frame = (self.bunny_frame + 1) % len(self.bunny_frames)
        
        # Cloud movement
        self.cloud_pos = (self.cloud_pos + 0.7) % (Config.get('window')[0] + 200)
        
        # Transition animation
        if self.transition_progress < 1:
            self.transition_progress = min(1, self.transition_progress + self.transition_speed)
            for key in self.current_positions:
                start = self.login_positions if self.auth_mode == "signup" else self.signup_positions
                end = self.signup_positions if self.auth_mode == "signup" else self.login_positions
                self.current_positions[key].y = start[key].y + (end[key].y - start[key].y) * self.transition_progress
            
            # Fade transition overlay
            self.transition_alpha = max(0, self.transition_alpha - 15)

    def draw(self):
        """Draw all game elements"""
        # Draw background
        self.screen.blit(self.field_bg, (0, 0))
        
        # Draw scenery
        self._draw_scenery()
        
        # Draw title with shadow
        self._draw_title()
        
        # Draw input fields
        self._draw_input_fields()
        
        # Draw bunny
        self._draw_bunny()
        
        # Draw transition overlay if active
        if self.transition_alpha > 0:
            overlay = pygame.Surface(Config.get('window'), pygame.SRCALPHA)
            overlay.fill((*self.TRANSITION_COLOR, self.transition_alpha))
            self.screen.blit(overlay, (0, 0))
        
        pygame.display.flip()

    def _draw_scenery(self):
        """Draw background elements"""
        # Cloud
        self.screen.blit(self.cloud, (self.cloud_pos, 50))
        self.screen.blit(self.cloud, (self.cloud_pos - 300, 80))  # Second cloud
        
        # Fence at bottom
        self.screen.blit(self.fence, (0, Config.get('window')[1] - 60))
        
        # Carrot icon near username
        self.screen.blit(self.carrot, (self.current_positions["username"].x - 50, 
                                     self.current_positions["username"].y))

    def _draw_title(self):
        """Draw game title with nice shadow"""
        title_text = "Bunny is on farm"
        shadow = self.title_font.render(title_text, True, (100, 100, 100))
        text = self.title_font.render(title_text, True, self.TEXT_COLOR)
        
        # Center the title
        x = Config.get('window')[0] // 2 - text.get_width() // 2
        y = 80
        
        # Draw shadow first
        self.screen.blit(shadow, (x + 3, y + 3))
        # Then draw main text
        self.screen.blit(text, (x, y))

    def _draw_input_fields(self):
        """Draw all UI input elements"""
        # Fields
        for field in ["username", "password"]:
            self._draw_field(field)
        if self.auth_mode == "signup" or self.transition_progress < 1:
            self._draw_field("confirm")
        
        # Button with hover effect
        button_rect = self.current_positions["button"]
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = button_rect.collidepoint(mouse_pos)
        
        # Fixed button color - no more invalid values
        button_color = self.BUTTON_COLOR
        if is_hovered:
            # Lighten the color safely
            button_color = (
                min(255, self.BUTTON_COLOR[0] + 30),
                min(255, self.BUTTON_COLOR[1] + 30),
                min(255, self.BUTTON_COLOR[2] + 30)
            )
        
        pygame.draw.rect(self.screen, button_color, button_rect, 0, 10)
        pygame.draw.rect(self.screen, (150, 100, 50), button_rect, 2, 10)  # Border
        
        btn_text = "Join Farm" if self.auth_mode == "signup" else "Enter Farm"
        text = self.button_font.render(btn_text, True, self.TEXT_COLOR)
        self.screen.blit(text, (button_rect.centerx - text.get_width()//2, 
                              button_rect.centery - text.get_height()//2))
        
        # Mode switch text with hover effect
        switch_text = "Already farming? Log in" if self.auth_mode == "signup" else "New farmer? Sign up"
        switch_rect = self.current_positions["switch"]
        is_switch_hovered = switch_rect.collidepoint(mouse_pos)
        
        switch_color = self.ACTIVE_COLOR
        if is_switch_hovered:
            # Lighten the color safely
            switch_color = (
                min(255, self.ACTIVE_COLOR[0] + 30),
                min(255, self.ACTIVE_COLOR[1] + 30),
                min(255, self.ACTIVE_COLOR[2] + 30)
            )
        
        text = self.small_font.render(switch_text, True, switch_color)
        underline = 1 if is_switch_hovered else 0
        pygame.draw.line(self.screen, switch_color, 
                        (switch_rect.x, switch_rect.y + switch_rect.height),
                        (switch_rect.x + switch_rect.width, switch_rect.y + switch_rect.height),
                        underline)
        
        self.screen.blit(text, (switch_rect.centerx - text.get_width()//2,
                              switch_rect.centery - text.get_height()//2))
        
        # Message
        if self.message:
            text = self.small_font.render(self.message, True, self.message_color)
            self.screen.blit(text, (Config.get('window')[0] // 2 - text.get_width() // 2, 420))

    def _draw_field(self, field):
        """Draw a single input field"""
        rect = self.current_positions[field]
        labels = {
            "username": "Farmer Name",
            "password": "Password", 
            "confirm": "Confirm Password"
        }
        
        # Label
        text = self.small_font.render(labels[field], True, self.TEXT_COLOR)
        self.screen.blit(text, (rect.x, rect.y - 25))
        
        # Field background - more pronounced when active
        is_active = self.get_active_rect() == rect
        border_color = (
            max(0, self.ACTIVE_COLOR[0] - 20),
            max(0, self.ACTIVE_COLOR[1] - 20),
            max(0, self.ACTIVE_COLOR[2] - 20)
        ) if is_active else self.INACTIVE_COLOR
        border_width = 3 if is_active else 2
        
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 0, 5)
        pygame.draw.rect(self.screen, border_color, rect, border_width, 5)
        
        # Text content
        value = getattr(self, "username" if field == "username" else 
                    "password" if field == "password" else 
                    "confirm_password")
        display = value if field == "username" else "*" * len(value)
        text = self.input_font.render(display, True, self.TEXT_COLOR)
        
        # Calculate centered position
        text_y = rect.y + (rect.height - text.get_height()) // 2
        self.screen.blit(text, (rect.x + 10, text_y))

    def _draw_bunny(self):
        """Draw the animated bunny character with shadow"""
        bunny_img = self.bunny_frames[self.bunny_frame]
        y_offset = 550 - 128 * (1 - self.transition_progress)
        
        # Draw shadow
        shadow = pygame.Surface((80, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 80, 20))
        self.screen.blit(shadow, (400 - 40, y_offset + 100))
        
        # Draw bunny
        self.screen.blit(bunny_img, (400 - 40, y_offset))

    def get_active_rect(self):
        """Get currently active field"""
        return next((v for k,v in self.current_positions.items() 
                   if k == self.active_field), None)

    def quit(self):
        """Clean shutdown"""
        self.running = False
        pygame.quit()
        sys.exit()

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    auth = AuthSystem()
    auth.run()