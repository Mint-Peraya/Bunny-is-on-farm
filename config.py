import pygame
import random

class Frame:
    def __init__(self, image):
        self.sheet = image

    def get_image(self, frame, width, height, scale, colour):
        image = pygame.Surface((width, height)).convert_alpha()
        image.blit(self.sheet, (0, 0), ((frame * width), 0, width, height))
        image = pygame.transform.scale(image, (width * scale, height * scale))
        image.set_colorkey(colour)
        return image
    
# Initialize pygame before loading images
pygame.init()
pygame.display.set_mode((1, 1))

class ResourceItem:
    def __init__(self, name, image_path):
        self.name = name
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except:
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.image.fill((50, 50, 50, 255))  # dark gray background

            # Render the name on the fallback surface
            font = pygame.font.SysFont("arial", 10, bold=True)
            text_surface = font.render(self.name, True, (255, 255, 255))  # white text

            # Center the text
            text_rect = text_surface.get_rect(center=(16, 16))
            self.image.blit(text_surface, text_rect)


class Config:
    """Configuration class to store game settings and images."""
    # Store basic configurations
    __ALL_CONFIGS = {
        'window': (800, 600),
        'wx': 800,
        'wy': 600,
        'FPS': 60,
        'bun_size': 64,
        'bun_exact': 32,
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'gray':(70,70,70),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'peach': (255, 200, 200),
        'sky': (200, 255, 255),
        'purple': (200, 0, 210),
        'dark_purple':(52, 0, 112),
        'brown': (60,5,25),
        'maze': 50 * 64,  # Maze size (50x50 grid)
        'grid': 50,
        'yellow': (200, 200, 0),
        'font':"assets/fonts/pixel.ttf",
        'FPS': 60,
        'environ':{
        'dirt': pygame.image.load('assets/picture/grass1.png').convert_alpha(),
        'soil_overlay': pygame.image.load('assets/picture/soil_overlay.png').convert_alpha(),
        'tree': pygame.image.load('assets/picture/tree.png').convert_alpha(),
        'stone': pygame.image.load('assets/picture/stone.png').convert_alpha(),
        'house': pygame.image.load("assets/bgimages/home.png").convert_alpha()
    }
    }

    # config.py - Add to RESOURCE_ITEMS
    RESOURCE_ITEMS = {
        "wood": ResourceItem("wood", "assets/items/wood.png"),
        "stone": ResourceItem("stone", "assets/items/stone.png"),
        "carrot": ResourceItem("carrot", "assets/items/carrot.png"),
        "axe": ResourceItem("axe", "assets/items/axe.png"),
        "pickaxe": ResourceItem("pickaxe", "assets/items/pickaxe.png"),
        "seed": ResourceItem("seed", "assets/items/seed.png"),
        "carrot_seed": ResourceItem("carrot seed", "assets/plants/carrot_seed.png"),
    }

    PLANT_CONFIG = {
    "carrot": {
        "stages": 3,
        "grow_time": 3000,
        "seasons": ["Spring","Summer", "Fall"],
        "harvest_item": "carrot",
        "harvest_amount": 2
    }}

    # Store images separately to prevent premature loading
    __bun_sheet = {}

    @classmethod
    def load_images(cls):
        """Load all game images with error handling"""
        try:
            # Environment images
            cls.__ALL_CONFIGS['environ']['dirt'] = pygame.image.load('assets/picture/grass1.png').convert_alpha()
            cls.__ALL_CONFIGS['environ']['soil_overlay'] = pygame.image.load('assets/picture/soil_overlay.png').convert_alpha()
            cls.__ALL_CONFIGS['environ']['tree'] = pygame.image.load('assets/picture/tree.png').convert_alpha()
            cls.__ALL_CONFIGS['environ']['stone'] = pygame.image.load('assets/picture/stone.png').convert_alpha()
            
            # Plant stages
            for crop in cls.PLANT_CONFIG:
                for i in range(1, cls.PLANT_CONFIG[crop]["stages"] + 1):
                    try:
                        cls.__ALL_CONFIGS['environ'][f'{crop}_stage{i}'] = pygame.image.load(
                            f'assets/plants/{crop}_stage{i}.png').convert_alpha()
                    except:
                        print(f"Failed to load {crop}_stage{i}.png")
                        # Create placeholder
                        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                        surf.fill((random.randint(50,200), random.randint(50,200), random.randint(50,200)))
                        cls.__ALL_CONFIGS['environ'][f'{crop}_stage{i}'] = surf
                        
        except Exception as e:
            print(f"Error loading images: {e}")
            """Load images and store them in the dictionary."""
        cls.__bun_sheet = {
            'front_sheet': Frame(pygame.image.load('assets/picture/BunnyWalk-Sheet.png').convert_alpha()),
            'back_sheet': Frame(pygame.image.load('assets/picture/BunnyWalkBack-Sheet.png').convert_alpha()),
            'right_sheet': Frame(pygame.image.load('assets/picture/BunnyWalkright-Sheet.png').convert_alpha()),
            'left_sheet': Frame(pygame.image.load('assets/picture/BunnyWalkleft-Sheet.png').convert_alpha()),
            'front_damage_sheet': Frame(pygame.image.load('assets/picture/bunny_front_damage.png').convert_alpha()),
            'back_damage_sheet': Frame(pygame.image.load('assets/picture/bunny_back_damage.png').convert_alpha()),
            'left_damage_sheet': Frame(pygame.image.load('assets/picture/bunny_left_damage.png').convert_alpha()),
            'right_damage_sheet': Frame(pygame.image.load('assets/picture/bunny_right_damage.png').convert_alpha())
        }
    
 

    @classmethod
    def get(cls, key):
        """Retrieve a configuration value by key."""
        if key == 'bun_sheet':
            return cls.__bun_sheet  # Return images separately
        return cls.__ALL_CONFIGS.get(key, None)  # Return other settings

# Load images once before the game starts
Config.load_images()

class BigScene:  
    def __init__(self,screen,clock,story_text, font, font_size, typing_speed=0.03):
        self.screen = screen
        self.clock = clock
        self.story = story_text
        self.speed = typing_speed
        self.displayed_text = ""
        self.text_index = 0
        self.timer = 0
        self.done_typing = False
        self.font = pygame.font.Font(font, font_size)
        self.littlefont = pygame.font.Font(font, font_size-5)
    
    def run(self):
        
        press_text = self.littlefont.render("-Press Space to continue-", True, (200, 200, 200))
        press_rect = press_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        
        while True:
            dt = self.clock.tick(60) / 1000  # Time passed in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if self.done_typing and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return  # Exit story screen

            # Typing effect
            if not self.done_typing:
                self.timer += dt
                if self.timer >= self.speed and self.text_index < len(self.story):
                    self.displayed_text += self.story[self.text_index]
                    self.text_index += 1
                    self.timer = 0
                if self.text_index == len(self.story):
                    self.done_typing = True

            # Drawing
            self.screen.fill((0,0,0)) #black bg
            
            wrapped_lines = self.wrap_text(self.displayed_text, self.screen.get_width() - 100)
            for i, line in enumerate(wrapped_lines):
                line_surface = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(line_surface, (50, 200 + i * 40))

            if self.done_typing:
                self.screen.blit(press_text, press_rect)

            pygame.display.flip()

        
    def wrap_text(self,text, max_width):
        """Helper function to wrap long text lines within max_width."""
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)
        return lines

