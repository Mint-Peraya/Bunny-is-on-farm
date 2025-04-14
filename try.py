import pygame
import csv
import hashlib
import uuid
import math
import time
from datetime import datetime
from typing import Tuple
from dataclasses import dataclass
from pathlib import Path
from config import Config

@dataclass
class InputField:
    rect: pygame.Rect
    text: str = ""
    active: bool = False
    secret: bool = False
    visible: bool = False

class AuthSystem:
    """Singleton authentication system with animated UI."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._initialize_system()
            self.data_dir = Path("Data")
            self.data_dir.mkdir(exist_ok=True)  # Create Data directory if it doesn't exist
            self.credentials_file = self.data_dir / "users_credentials.csv"
            self.login_time_file = self.data_dir / "login_time.csv"
            self._ensure_data_files()
    
    def _ensure_data_files(self):
        """Ensure the data files exist with proper headers."""
        # For credentials
        if not self.credentials_file.exists():
            with open(self.credentials_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "username", "password_hash"])
        
        # For login times
        if not self.login_time_file.exists():
            with open(self.login_time_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "username", "timestamp"])
    
    def _log_login_time(self, user_id: str, username: str):
        """Record the login time for a user."""
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open(self.login_time_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, username, timestamp])
    
    def _initialize_system(self):
        """Initialize all system components."""
        self._init_pygame()
        self._load_assets()
        self._setup_ui()
        self._reset_state()
        self.current_user_id = None
        self.current_username = None
    
    def _init_pygame(self):
        """Initialize pygame and create window."""
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        pygame.display.set_caption("Bunny Farm Authentication")
        self.clock = pygame.time.Clock()
        self.running = True
    
    def _load_assets(self):
        """Load or create all visual assets."""
        self.fonts = {
            "title": pygame.font.Font(Config.get('font'), 48),
            "subtitle": pygame.font.Font(Config.get('font'), 32),
            "button": pygame.font.Font(Config.get('font'), 28),
            "field": pygame.font.Font(Config.get('font'), 24),
            "message": pygame.font.Font(Config.get('font'), 22),
        }

        self._load_eye_icons()
        self._load_background()

    def _load_eye_icons(self):
        """Load or create eye icons for password visibility."""
        try:
            self.eye_open = pygame.image.load("assets/image/eye_open.png").convert_alpha()
            self.eye_open = pygame.transform.scale(self.eye_open, (30, 20))
            self.eye_closed = pygame.image.load("assets/image/eye_closed.png").convert_alpha()
            self.eye_closed = pygame.transform.scale(self.eye_closed, (30, 20))
        except:
            self.eye_open = pygame.Surface((30, 20), pygame.SRCALPHA)
            pygame.draw.circle(self.eye_open, (255, 255, 255), (15, 10), 8)
            pygame.draw.circle(self.eye_open, (0, 0, 0), (15, 10), 5)
            pygame.draw.arc(self.eye_open, (0, 0, 0), (5, 0, 20, 20), 0, math.pi, 2)
            
            self.eye_closed = pygame.Surface((30, 20), pygame.SRCALPHA)
            pygame.draw.line(self.eye_closed, (0, 0, 0), (5, 10), (25, 10), 3)
    
    def _load_background(self):
        """Load background image or create a drawn one."""
        try:
            self.background = pygame.image.load("assets/bgimages/login_bg.png").convert()
            self.background = pygame.transform.scale(self.background, Config.get('window'))
        except:
            # Fallback background if image not found
            self.background = pygame.Surface(Config.get('window'))
            self.background.fill(Config.get('sky'))
    
    def _setup_ui(self):
        """Set up UI elements and positions."""
        field_width = 300
        field_height = 40
        start_y = 200
        
        self.fields = {
            "username": InputField(
                rect=pygame.Rect(Config.get('wx')//2 - field_width//2, start_y+20, field_width, field_height)
            ),
            "password": InputField(
                rect=pygame.Rect(Config.get('wx')//2 - field_width//2, start_y + 100, field_width, field_height),
                secret=True
            )
        }
        
        button_width = 200
        button_height = 40
        
        self.buttons = {
            "submit": pygame.Rect(Config.get('wx')//2 - button_width//2, start_y + 210, button_width, button_height),
            "toggle_password": pygame.Rect(Config.get('wx')//2 + field_width//2 - 35, start_y + 100, 30, 20)
        }
        
        self.mode_toggle_rect = pygame.Rect(0, start_y + 270, Config.get('wx'), 30)
    
    def _reset_state(self):
        """Reset the system state."""
        self.auth_mode = "login"
        self.message = ""
        self.message_color = Config.get('brown')
        self.transition_progress = 1
        self.transition_speed = 0.08
        self.transition_alpha = 0
        
        for field in self.fields.values():
            field.text = ""
            field.active = False
            field.visible = False
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_user_id(self) -> str:
        """Generate a unique user ID."""
        return str(uuid.uuid4())
    
    def _validate_credentials(self, username: str, password: str) -> Tuple[bool, str, str]:
        """Check credentials and return (success, user_id, username)."""
        with open(self.credentials_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[1] == username and row[2] == self._hash_password(password):
                    return True, row[0], row[1]
        return False, None, None
    
    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        with open(self.credentials_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[1] == username:
                    return True
        return False
    
    def _register_user(self, username: str, password: str) -> Tuple[bool, str, str]:
        """Register a new user and return (success, user_id, username)."""
        if self._username_exists(username):
            return False, None, None
        
        user_id = self._generate_user_id()
        with open(self.credentials_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, username, self._hash_password(password)])
        return True, user_id, username
    
    def _handle_login(self):
        """Handle login attempt."""
        username = self.fields["username"].text
        password = self.fields["password"].text
        
        if not username or not password:
            self.message = "Please fill in all fields"
            self.message_color = Config.get('red')
            return
        
        success, user_id, username = self._validate_credentials(username, password)
        if success:
            self.message = "Login successful!"
            self.message_color = Config.get('green')
            self.current_user_id = user_id
            self.current_username = username
            self._log_login_time(user_id, username)
            self._start_transition()
        else:
            self.message = "Invalid username or password"
            self.message_color = Config.get('red')
    
    def _handle_register(self):
        """Handle registration attempt."""
        username = self.fields["username"].text
        password = self.fields["password"].text
        
        if not username or not password:
            self.message = "Please fill in all fields"
            self.message_color = Config.get('red')
            return
        
        if len(password) < 6:
            self.message = "Password must be at least 6 characters"
            self.message_color = Config.get('red')
            return
        
        success, user_id, username = self._register_user(username, password)
        if success:
            self.message = "Registration successful! Please login"
            self.message_color = Config.get('green')
            self.auth_mode = "login"
        else:
            self.message = "Username already exists"
            self.message_color = Config.get('red')
    
    def _start_transition(self):
        """Start the transition animation."""
        self.transition_progress = 0
        self.transition_alpha = 0
    
    def _draw_ui(self):
        """Draw all UI elements."""
        self.screen.blit(self.background, (0, 0))
        
        title = self.fonts["title"].render(
            "Bunny is on farm", True, Config.get('brown'))
        self.screen.blit(title, (Config.get('wx')//2 - title.get_width()//2, 80))
        
        subtitle_text = "Register" if self.auth_mode == "register" else "Login"
        subtitle = self.fonts["subtitle"].render(
            subtitle_text, True, Config.get('brown'))
        self.screen.blit(subtitle, (Config.get('wx')//2 - subtitle.get_width()//2, 140))
        
        self._draw_input_fields()
        
        pygame.draw.rect(self.screen, Config.get('purple'), self.buttons["submit"], 0, 5)
        pygame.draw.rect(self.screen, Config.get('brown'), self.buttons["submit"], 2, 5)
        
        submit_text = "Register" if self.auth_mode == "register" else "Login"
        text_surface = self.fonts["button"].render(submit_text, True, Config.get('brown'))
        self.screen.blit(text_surface, 
                        (self.buttons["submit"].centerx - text_surface.get_width()//2,
                         self.buttons["submit"].centery - text_surface.get_height()//2))
        
        toggle_text = "Already have an account? Login" if self.auth_mode == "register" else "Don't have an account? Register"
        text_surface = self.fonts["message"].render(toggle_text, True, Config.get('brown'))
        text_rect = text_surface.get_rect(center=(Config.get('wx')//2, self.buttons["submit"].bottom + 25))
        self.screen.blit(text_surface, text_rect)
        
        if self.message:
            msg_surface = self.fonts["message"].render(
                self.message, True, self.message_color)
            message_y = self.fields["password"].rect.bottom + 20
            self.screen.blit(msg_surface, (Config.get('wx')//2 - msg_surface.get_width()//2, message_y))
        
        if self.transition_progress < 1:
            overlay = pygame.Surface(Config.get('window'), pygame.SRCALPHA)
            radius = int(self.transition_progress * (Config.get('wx') * 1.5))
            pygame.draw.circle(overlay, (*Config.get('brown'), self.transition_alpha), 
                             (Config.get('wx')//2, Config.get('wy')//2), radius)
            self.screen.blit(overlay, (0, 0))
    
    def _draw_input_fields(self):
        """Draw all input fields."""
        for name, field in self.fields.items():
            color = Config.get('peach') if field.active else Config.get('sky')
            pygame.draw.rect(self.screen, color, field.rect, 0, 5)
            pygame.draw.rect(self.screen, Config.get('brown'), field.rect, 2, 5)
            
            label = self.fonts["field"].render(
                name.replace("_", " ").title() + ":", True, Config.get('brown'))
            self.screen.blit(label, (field.rect.left, field.rect.top - 25))
            
            text = "*" * len(field.text) if field.secret and not field.visible else field.text
            text_surface = self.fonts["field"].render(text, True, Config.get('brown'))
            text_rect = text_surface.get_rect(
                midleft=(field.rect.left + 10, field.rect.centery))
            
            max_width = field.rect.width - 20
            if text_surface.get_width() > max_width:
                visible_text = pygame.Surface((max_width, text_surface.get_height()), pygame.SRCALPHA)
                visible_text.blit(text_surface, (0, 0), 
                                (text_surface.get_width() - max_width, 0, max_width, text_surface.get_height()))
                self.screen.blit(visible_text, 
                               (field.rect.right - max_width - 10, text_rect.y))
            else:
                self.screen.blit(text_surface, text_rect)
            
            if field.secret:
                eye_icon = self.eye_open if field.visible else self.eye_closed
                eye_pos = (field.rect.right - 35, field.rect.centery - 10)
                self.screen.blit(eye_icon, eye_pos)
    
    def _handle_events(self):
        """Handle all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for name, field in self.fields.items():
                    field.active = field.rect.collidepoint(pos)
                
                if self.buttons["toggle_password"].collidepoint(pos):
                    self.fields["password"].visible = not self.fields["password"].visible
                
                if self.buttons["submit"].collidepoint(pos):
                    if self.auth_mode == "login":
                        self._handle_login()
                    else:
                        self._handle_register()
                
                if self.mode_toggle_rect.collidepoint(pos):
                    self.auth_mode = "register" if self.auth_mode == "login" else "login"
                    self.message = ""
            
            elif event.type == pygame.KEYDOWN and self.active_field:
                field = self.fields[self.active_field]
                
                if event.key == pygame.K_RETURN:
                    if self.auth_mode == "login":
                        self._handle_login()
                    else:
                        self._handle_register()
                elif event.key == pygame.K_BACKSPACE:
                    field.text = field.text[:-1]
                elif event.key == pygame.K_TAB:
                    field_names = list(self.fields.keys())
                    current_index = field_names.index(self.active_field)
                    next_index = (current_index + 1) % len(field_names)
                    self.fields[self.active_field].active = False
                    self.active_field = field_names[next_index]
                    self.fields[self.active_field].active = True
                elif event.unicode.isprintable():
                    field.text += event.unicode
    
    def run(self):
        """Main game loop."""
        while self.running:
            self._handle_events()
            self._draw_ui()
            
            pygame.display.flip()
            self.clock.tick(Config.get('FPS'))
            
            if self.transition_progress >= 1 and self.message == "Login successful!":
                time.sleep(1)
                self.running = False
        
        pygame.quit()
        return {
            "user_id": self.current_user_id,
            "username": self.current_username
        }

if __name__ == "__main__":
    auth = AuthSystem()
    user_data = auth.run()
    print(f"Logged in with: {user_data}")