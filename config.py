import pygame
from pathlib import Path

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
# Define the script directory and image folder
SCRIPT_DIR = Path(__file__).parent
IMAGE_FOLDER = SCRIPT_DIR / "picture"
pygame.display.set_mode((1, 1))

class Config:
    """Configuration class to store game settings and images."""

    # Store basic configurations
    __ALL_CONFIGS = {
        'window': (800, 600),
        'wx': 800,
        'wy': 600,
        'bun_size': 64,
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'peach': (255, 200, 200),
        'sky': (200, 255, 255),
        'purple': (200, 0, 210),
        'maze': 50 * 64,  # Maze size (50x50 grid)
        'grid': 50,
        'yellow': (200, 200, 0)
    }

    # Store images separately to prevent premature loading
    __bun_sheet = {}

    @classmethod
    def load_images(cls):
        """Load images and store them in the dictionary."""
        cls.__bun_sheet = {
            'front_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'BunnyWalk-Sheet.png').convert_alpha()),
            'back_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'BunnyWalkBack-Sheet.png').convert_alpha()),
            'right_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'BunnyWalkright-Sheet.png').convert_alpha()),
            'left_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'BunnyWalkleft-Sheet.png').convert_alpha()),
            'front_damage_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'bunny_front_damage.png').convert_alpha()),
            'back_damage_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'bunny_back_damage.png').convert_alpha()),
            'left_damage_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'bunny_left_damage.png').convert_alpha()),
            'right_damage_sheet': Frame(pygame.image.load(IMAGE_FOLDER / 'bunny_right_damage.png').convert_alpha())
        }

    @classmethod
    def get(cls, key):
        """Retrieve a configuration value by key."""
        if key == 'bun_sheet':
            return cls.__bun_sheet  # Return images separately
        return cls.__ALL_CONFIGS.get(key, None)  # Return other settings

# Load images once before the game starts
Config.load_images()
