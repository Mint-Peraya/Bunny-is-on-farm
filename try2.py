import pygame
from config import *

class Bunny:
    def __init__(self, x, y,mode='farming'):
        self.x, self.y = x, y
        self.speed = 0.1  # Base speed (fraction of a cell per frame)
        self.target_x = x  # Target position for smooth movement
        self.target_y = y
        self.health = 100
        self.mode =mode
        self.rect = pygame.Rect(self.x, self.y, 64, 64)  # Collision detection
        self.attack_cooldown = 0  # Cooldown for attacks

        # Load sprite sheets
        self.load_bunny()

        self.frames_front = [self.sheet['front_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_back = [self.sheet['back_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_right = [self.sheet['right_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
        self.frames_left = [self.sheet['left_sheet'].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
    
        self.current_direction = 'front'
        self.current_frame = 0
        self.frame_time = 60
        self.last_update_time = pygame.time.get_ticks()
        self.attacking = False

    def load_bunny(self):
        """Load all sprite sheets."""
        self.sheet = Config.get("bun_sheet")
        self.frames = {
            "front": [self.sheet["front_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "back": [self.sheet["back_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "left": [self.sheet["left_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "right": [self.sheet["right_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "front_damage": [self.sheet["front_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "back_damage": [self.sheet["back_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "left_damage": [self.sheet["left_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "right_damage": [self.sheet["right_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
        }

    def move(self, keys, maze):
        """Update bunny's position based on key presses and maze walls."""
        moving = False
        current_time = pygame.time.get_ticks()
        new_direction = self.current_direction  # Track if direction changes

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