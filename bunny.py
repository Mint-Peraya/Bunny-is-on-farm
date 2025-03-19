import pygame
from config import Config
from pathlib import Path
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

class Bunny:
    def __init__(self, x, y):
        self.x = x  # Grid position (column)
        self.y = y  # Grid position (row)
        self.normal_speed = 0.1  # Base speed (fraction of a cell per frame)
        self.speed = self.normal_speed
        self.target_x = x  # Target position for smooth movement
        self.target_y = y
        self.health = 100
        self.rect = pygame.Rect(self.x, self.y, 64, 64)  # Collision detection
        self.attack_cooldown = 0  # Cooldown for attacks
        SCRIPT_DIR = Path(__file__).parent
        self.IMAGE_FOLDER = SCRIPT_DIR / "picture"

        # Speed Boost Variables
        self.speed_boost_active = False
        self.speed_boost_start_time = 0
        self.speed_boost_duration = 5000  # 5 seconds (5000 ms)

        # Cooldown Variables
        self.speed_boost_cooldown = False
        self.speed_boost_cooldown_time = 3000  # 3 seconds (3000 ms)
        self.speed_boost_cooldown_start = 0

        # Load sprite sheets
        self.sheet = {
        'front_sheet': Frame(pygame.image.load(self.IMAGE_FOLDER/'BunnyWalk-Sheet.png').convert_alpha()),
        'back_sheet' : Frame(pygame.image.load(self.IMAGE_FOLDER/'BunnyWalkBack-Sheet.png').convert_alpha()),
        'right_sheet': Frame(pygame.image.load(self.IMAGE_FOLDER/'BunnyWalkright-Sheet.png').convert_alpha()),
        'left_sheet' : Frame(pygame.image.load(self.IMAGE_FOLDER/'BunnyWalkleft-Sheet.png').convert_alpha())
        }

        self.frames_front = [self.sheet['front_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_back = [self.sheet['back_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_right = [self.sheet['right_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
        self.frames_left = [self.sheet['left_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
    
        self.current_direction = 'front'
        self.current_frame = 0
        self.frame_time = 60
        self.last_update_time = pygame.time.get_ticks()
        self.attacking = False

    def move(self, keys, maze):
        """Update bunny's position based on key presses and maze walls."""
        moving = False
        current_time = pygame.time.get_ticks()
        new_direction = self.current_direction  # Track if direction changes

        # Handle Speed Boost Cooldown
        if self.speed_boost_cooldown and current_time - self.speed_boost_cooldown_start >= self.speed_boost_cooldown_time:
            self.speed_boost_cooldown = False

        if keys[pygame.K_f] and not self.speed_boost_active and not self.speed_boost_cooldown:
            self.speed_boost_active = True
            self.speed_boost_start_time = current_time
            self.speed = self.normal_speed * 1.5

        if self.speed_boost_active and current_time - self.speed_boost_start_time >= self.speed_boost_duration:
            self.speed_boost_active = False
            self.speed = self.normal_speed  
            self.speed_boost_cooldown = True  
            self.speed_boost_cooldown_start = current_time  

        # Movement & Direction Change Detection
        if self.x == self.target_x and self.y == self.target_y:  # Only move if bunny has reached the target
            if keys[pygame.K_LEFT]:
                new_x = self.x - 1
                if 0 <= new_x < Config.get('grid') and maze.grid[self.y][new_x] == 0:
                    self.target_x = new_x
                    new_direction = 'left'
                    moving = True
            elif keys[pygame.K_RIGHT]:
                new_x = self.x + 1
                if 0 <= new_x < Config.get('grid') and maze.grid[self.y][new_x] == 0:
                    self.target_x = new_x
                    new_direction = 'right'
                    moving = True
            elif keys[pygame.K_UP]:
                new_y = self.y - 1
                if 0 <= new_y < Config.get('grid') and maze.grid[new_y][self.x] == 0:
                    self.target_y = new_y
                    new_direction = 'back'
                    moving = True
            elif keys[pygame.K_DOWN]:
                new_y = self.y + 1
                if 0 <= new_y < Config.get('grid') and maze.grid[new_y][self.x] == 0:
                    self.target_y = new_y
                    new_direction = 'front'
                    moving = True

        # Smoothly move towards the target position
        if self.x < self.target_x:
            self.x = min(self.x + self.speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.speed, self.target_x)
        if self.y < self.target_y:
            self.y = min(self.y + self.speed, self.target_y)
        elif self.y > self.target_y:
            self.y = max(self.y - self.speed, self.target_y)

        # If direction changed, reset animation frame
        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0  # Reset frame to avoid out-of-range issues

        self.rect.topleft = (self.x * Config.get('bun_size'), self.y * Config.get('bun_size'))
        return moving

    def attack(self, enemies):
        """Attack enemies in range."""
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_cooldown > 500:  # 500 ms cooldown
            self.attacking = True
            self.attack_cooldown = current_time
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy.take_damage(10)  # Deal 10 damage to the enemy

    def take_damage(self, amount):
        """Reduce bunny's health by the specified amount."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            # Handle game over logic here

    def heal(self, amount):
        """Increase bunny's health by the specified amount."""
        self.health += amount
        if self.health > 100:
            self.health = 100

    def draw(self, screen, camera_x, camera_y):
        """Draw the bunny's current frame on the screen."""
        # Draw the current frame based on direction
        frame_dict = {
            'front': self.frames_front,
            'left': self.frames_left,
            'right': self.frames_right,
            'back': self.frames_back,
            # 'attack': self.frames_attack
        }

        # Ensure current_frame is within bounds
        frames = frame_dict.get(self.current_direction, [])
        if frames:
            self.current_frame = self.current_frame % len(frames)  # Prevent IndexError
            screen.blit(frames[self.current_frame], (self.x * Config.get('bun_size') - camera_x, self.y * Config.get('bun_size') - camera_y))

        # Draw health bar
        self.draw_health_bar(screen, camera_x, camera_y)

    def draw_health_bar(self, screen, camera_x, camera_y):
        """Draw the bunny's health bar on the screen."""
        pygame.draw.rect(screen, (255, 0, 0), (self.x * Config.get('bun_size') - camera_x + 8, self.y * Config.get('bun_size') - camera_y - 10, 50, 5))  # Red health bar background
        pygame.draw.rect(screen, (0, 255, 0), (self.x * Config.get('bun_size') - camera_x + 8, self.y * Config.get('bun_size') - camera_y - 10, self.health / 2, 5))  # Green health bar

    def update_animation(self, moving):
        """Update the frame if moving."""
        current_time = pygame.time.get_ticks()
        
        if (moving or self.attacking) and current_time - self.last_update_time > self.frame_time:
            frame_dict = {
                'front': self.frames_front,
                'left': self.frames_left,
                'right': self.frames_right,
                'back': self.frames_back,
                # 'attack': self.frames_attack
            }
            
            if self.current_direction in frame_dict:
                frames = frame_dict[self.current_direction]
                if frames:
                    self.current_frame = (self.current_frame + 1) % len(frames)  # Prevent IndexError
                    if self.attacking and self.current_frame == 0:
                        self.attacking = False  # Reset attacking state after animation
            
            self.last_update_time = current_time  # Update time
    
    # Add to existing class
    def collect_item(self, item):
        if item.type == "health":
            self.heal(20)
        elif item.type == "speed":
            self.speed_boost_duration = 10000
        elif item.type == "damage":
            self.attack_power = 20