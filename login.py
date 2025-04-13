import pygame
import csv,hashlib
import math,time
import uuid
from typing import Tuple
from dataclasses import dataclass
from config import Config

# Constants
FPS = 60

# Color palette
COLORS = {
    "bg": (234, 232, 205),       # Cream parchment
    "text": (88, 72, 56),        # Dark brown
    "active": (113, 179, 113),   # Leaf green
    "inactive": (181, 172, 156), # Stone gray
    "button": (242, 191, 96),    # Golden wheat
    "error": (219, 88, 86),      # Tomato red
    "success": (106, 168, 79),   # Apple green
    "transition": (255, 228, 181) # Light orange
}

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
            self.data_file = "Data/user_credentials.csv"
    
    def _initialize_system(self):
        """Initialize all system components."""
        self._init_pygame()
        self._load_assets()
        self._setup_ui()
        self._reset_state()
        self.current_user_id = None  # Track logged in user
    
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
            pygame.draw.circle(self.eye_open, (100, 100, 100), (15, 10), 8)
            pygame.draw.circle(self.eye_open, (50, 50, 150), (15, 10), 5)
            pygame.draw.circle(self.eye_open, (0, 0, 0), (15, 10), 2)
            pygame.draw.arc(self.eye_open, (100, 100, 100), (5, 0, 20, 20), 0, math.pi, 2)
            
            self.eye_closed = pygame.Surface((30, 20), pygame.SRCALPHA)
            pygame.draw.line(self.eye_closed, (100, 100, 100), (5, 10), (25, 10), 3)
    
    def _load_background(self):
        """Load background image or create a drawn one."""
        self.background = pygame.image.load("assets/bgimages/login_bg.png").convert()
        self.background = pygame.transform.scale(self.background, Config.get('window'))
    
    def _setup_ui(self):
        """Set up UI elements and positions."""
        # Input fields
        field_width = 300
        field_height = 40
        start_y = 200
        
        self.fields = {
            "username": InputField(
                rect=pygame.Rect(Config.get('wx')//2 - field_width//2, start_y, field_width, field_height)
            ),
            "password": InputField(
                rect=pygame.Rect(Config.get('wx')//2 - field_width//2, start_y + 70, field_width, field_height),
                secret=True
            )
        }
        
        # Buttons
        button_width = 200
        button_height = 40
        
        # Centered submit button
        self.buttons = {
            "submit": pygame.Rect(Config.get('wx')//2 - button_width//2, start_y + 140, button_width, button_height),
            "toggle_password": pygame.Rect(Config.get('wx')//2 + field_width//2 - 35, start_y + 70, 30, 20)
        }
        
        # Text link for mode toggle (positioned below the button)
        self.mode_toggle_rect = pygame.Rect(0, start_y + 190, Config.get('wx'), 30)
    
    def _reset_state(self):
        """Reset the system state."""
        self.auth_mode = "login"  # "login" or "register"
        self.message = ""
        self.message_color = COLORS["text"]
        self.transition_progress = 1
        self.transition_speed = 0.08
        self.transition_alpha = 0
        
        # Reset input fields
        for field in self.fields.values():
            field.text = ""
            field.active = False
            field.visible = False
    
    def _ensure_data_file(self):
        """Ensure the credentials file exists."""
        if not self.data_file.exists():
            with open(self.data_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["user_id", "username", "password_hash"])
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_user_id(self) -> str:
        """Generate a unique user ID."""
        return str(uuid.uuid4())
    
    def _validate_credentials(self, username: str, password: str) -> Tuple[bool, str]:
        """Check if credentials match stored data and return user ID."""
        with open(self.data_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row[1] == username and row[2] == self._hash_password(password):
                    return True, row[0]  # Return success and user_id
        return False, None
    
    def _username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        with open(self.data_file, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                if row[1] == username:
                    return True
        return False
    
    def _register_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Register a new user and return (success, user_id)."""
        if self._username_exists(username):
            return False, None
        
        user_id = self._generate_user_id()
        with open(self.data_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, username, self._hash_password(password)])
        return True, user_id
    
    def _handle_login(self):
        """Handle login attempt."""
        username = self.fields["username"].text
        password = self.fields["password"].text
        
        if not username or not password:
            self.message = "Please fill in all fields"
            self.message_color = COLORS["error"]
            return
        
        success, user_id = self._validate_credentials(username, password)
        if success:
            self.message = "Login successful!"
            self.message_color = COLORS["success"]
            self.current_user_id = user_id  # Store the logged in user's ID
            self._start_transition()
        else:
            self.message = "Invalid username or password"
            self.message_color = COLORS["error"]
    
    def _handle_register(self):
        """Handle registration attempt."""
        username = self.fields["username"].text
        password = self.fields["password"].text
        
        if not username or not password:
            self.message = "Please fill in all fields"
            self.message_color = COLORS["error"]
            return
        
        if len(password) < 6:
            self.message = "Password must be at least 6 characters"
            self.message_color = COLORS["error"]
            return
        
        success, user_id = self._register_user(username, password)
        if success:
            self.message = "Registration successful! Please login"
            self.message_color = COLORS["success"]
            self.auth_mode = "login"
            self.current_user_id = user_id  # Store the new user's ID
        else:
            self.message = "Username already exists"
            self.message_color = COLORS["error"]
    
    def _start_transition(self):
        """Start the transition animation."""
        self.transition_progress = 0
        self.transition_alpha = 0
    
    def _draw_ui(self):
        """Draw all UI elements."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw title
        title = self.fonts["title"].render(
            "Bunny is on farm", True, COLORS["text"])
        self.screen.blit(title, (Config.get('wx')//2 - title.get_width()//2, 80))
        
        # Draw subtitle (login/register)
        subtitle_text = "Register" if self.auth_mode == "register" else "Login"
        subtitle = self.fonts["subtitle"].render(
            subtitle_text, True, COLORS["text"])
        self.screen.blit(subtitle, (Config.get('wx')//2 - subtitle.get_width()//2, 140))
        
        # Draw input fields
        self._draw_input_fields()
        
        # Draw submit button (centered)
        pygame.draw.rect(self.screen, COLORS["button"], self.buttons["submit"], 0, 5)
        pygame.draw.rect(self.screen, COLORS["text"], self.buttons["submit"], 2, 5)
        
        submit_text = "Register" if self.auth_mode == "register" else "Login"
        text_surface = self.fonts["button"].render(submit_text, True, COLORS["text"])
        self.screen.blit(text_surface, 
                        (self.buttons["submit"].centerx - text_surface.get_width()//2,
                         self.buttons["submit"].centery - text_surface.get_height()//2))
        
        # Draw mode toggle text (below the button)
        toggle_text = "Already have an account? Login" if self.auth_mode == "register" else "Don't have an account? Register"
        text_surface = self.fonts["message"].render(toggle_text, True, COLORS["text"])
        text_rect = text_surface.get_rect(center=(Config.get('wx')//2, self.buttons["submit"].bottom + 25))
        self.screen.blit(text_surface, text_rect)
        
        # Draw message
        if self.message:
            msg_surface = self.fonts["message"].render(
                self.message, True, self.message_color)
            message_y = self.fields["password"].rect.bottom + 20
            self.screen.blit(msg_surface, (Config.get('wx')//2 - msg_surface.get_width()//2, message_y))
        
        # Draw transition overlay if active
        if self.transition_progress < 1:
            overlay = pygame.Surface(Config.get('window'), pygame.SRCALPHA)
            radius = int(self.transition_progress * (Config.get('wx') * 1.5))
            pygame.draw.circle(overlay, (*COLORS["transition"], self.transition_alpha), 
                             (Config.get('wx')//2, Config.get('wy')//2), radius)
            self.screen.blit(overlay, (0, 0))
    
    
    def _draw_input_fields(self):
        """Draw all input fields."""
        for name, field in self.fields.items():
            # Field background
            color = COLORS["active"] if field.active else COLORS["inactive"]
            pygame.draw.rect(self.screen, color, field.rect, 0, 5)
            pygame.draw.rect(self.screen, COLORS["text"], field.rect, 2, 5)
            
            # Field label
            label = self.fonts["field"].render(
                name.replace("_", " ").title() + ":", True, COLORS["text"])
            self.screen.blit(label, (field.rect.left, field.rect.top - 25))
            
            # Field text
            text = field.text
            if field.secret and not field.visible:
                text = "*" * len(text)
            
            text_surface = self.fonts["field"].render(text, True, COLORS["text"])
            text_rect = text_surface.get_rect(
                midleft=(field.rect.left + 10, field.rect.centery))
            
            # Ensure text doesn't overflow
            max_width = field.rect.width - 20
            if text_surface.get_width() > max_width:
                # Create a subsurface to show only the visible part
                visible_text = pygame.Surface((max_width, text_surface.get_height()), pygame.SRCALPHA)
                visible_text.blit(text_surface, (0, 0), 
                                (text_surface.get_width() - max_width, 0, max_width, text_surface.get_height()))
                self.screen.blit(visible_text, 
                               (field.rect.right - max_width - 10, text_rect.y))
            else:
                self.screen.blit(text_surface, text_rect)
            
            # Draw eye icon for password fields
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
                self._handle_mouse_click(event.pos)
            
            elif event.type == pygame.KEYDOWN:
                self._handle_key_press(event)
    
    def _handle_mouse_click(self, pos: Tuple[int, int]):
        """Handle mouse click events."""
        # Check input fields
        for name, field in self.fields.items():
            if field.rect.collidepoint(pos):
                field.active = True
                self.active_field = name
            else:
                field.active = False
        
        # Check password visibility toggle
        if self.buttons["toggle_password"].collidepoint(pos):
            self.fields["password"].visible = not self.fields["password"].visible
        
        # Check submit button
        if self.buttons["submit"].collidepoint(pos):
            if self.auth_mode == "login":
                self._handle_login()
            else:
                self._handle_register()
        
        # Check mode toggle text
        if self.mode_toggle_rect.collidepoint(pos):
            self.auth_mode = "register" if self.auth_mode == "login" else "login"
            self.message = ""
    
    def _handle_key_press(self, event: pygame.event.Event):
        """Handle keyboard events."""
        if self.active_field:
            field = self.fields[self.active_field]
            
            if event.key == pygame.K_RETURN:
                if self.auth_mode == "login":
                    self._handle_login()
                else:
                    self._handle_register()
            
            elif event.key == pygame.K_BACKSPACE:
                field.text = field.text[:-1]
            
            elif event.key == pygame.K_TAB:
                # Cycle through fields
                field_names = list(self.fields.keys())
                current_index = field_names.index(self.active_field)
                next_index = (current_index + 1) % len(field_names)
                
                field.active = False
                self.fields[field_names[next_index]].active = True
                self.active_field = field_names[next_index]
            
            elif event.unicode.isprintable():
                field.text += event.unicode
    
    def run(self):
        """Main game loop."""
        while self.running:
            self._handle_events()
            self._draw_ui()
            
            pygame.display.flip()
            self.clock.tick(FPS)
            
            # Check if transition is complete
            if self.transition_progress >= 1 and self.message == "Login successful!":
                time.sleep(1)  # Show success message briefly
                self.running = False
        
        pygame.quit()
        return self.current_user_id  # Return the user ID when done

if __name__ == "__main__":
    auth = AuthSystem()
    user_id = auth.run()
    print(f"Logged in with user ID: {user_id}")  # You can use this ID to save game data