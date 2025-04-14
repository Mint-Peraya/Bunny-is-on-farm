import pygame
from config import Config

class Bunny:
    def __init__(self, x, y, mode="farming"):
        self.x, self.y = x, y
        self.health = 100
        self.attack_power = 10
        self.speed = 0.1
        self.target_x, self.target_y = x, y

        self.current_direction = "front"
        self.mode = mode  # Modes: "maze", "farming", "dungeon"

        # Animation state
        self.current_frame = 0
        self.last_update_time = pygame.time.get_ticks()

        # Status Effects
        self.attacking = False
        self.damaged = False
        self.damage_start_time = 0
        self.damage_duration = 500  # 0.5 seconds
        self.attack_cooldown = 0

        # Speed Boost
        self._init_speed_boost()

        # Load Bunny sprites
        self.load_bunny()

        # Rect for collision
        tile_size = Config.get("bun_size")
        self.rect = pygame.Rect(self.x * tile_size, self.y * tile_size, tile_size, tile_size)

    def load_bunny(self):
        """Load all sprite sheets."""
        self.sheet = Config.get("bun_sheet")
        self.frames = {
            "front": [self.sheet["front_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "back": [self.sheet["back_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "left": [self.sheet["left_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
            "right": [self.sheet["right_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
            "front_damage": [self.sheet["front_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "back_damage": [self.sheet["back_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "left_damage": [self.sheet["left_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
            "right_damage": [self.sheet["right_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
        }

    def switch_mode(self, new_mode):
        """Switch Bunny's mode (maze, farming, dungeon)."""
        if new_mode in ["maze", "farming", "dungeon"]:
            self.mode = new_mode
            print(f"Bunny switched to {new_mode} mode.")

    def heal(self, amount):
        """Heal the bunny, capping at 100 health."""
        self.health = min(self.health + amount, 100)

    def take_damage(self, amount):
        """Take damage and react accordingly."""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            print("Bunny has been defeated!")  # Handle death logic here
        else:
            self.damaged = True
            self.damage_start_time = pygame.time.get_ticks()

    def attack(self, enemies):
        """Attack nearby enemies."""
        if pygame.time.get_ticks() - self.attack_cooldown > 500:
            self.attacking = True
            self.attack_cooldown = pygame.time.get_ticks()
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy.take_damage(self.attack_power)

    def update_animation(self, moving):
        """Update animation based on movement and status effects."""
        if moving or self.attacking or self.damaged:
            if pygame.time.get_ticks() - self.last_update_time > 60:
                frame_type = f"{self.current_direction}_damage" if self.damaged else self.current_direction
                self.current_frame = (self.current_frame + 1) % len(self.frames[frame_type])

                if self.attacking and self.current_frame == 0:
                    self.attacking = False
                if self.damaged and pygame.time.get_ticks() - self.damage_start_time >= self.damage_duration:
                    self.damaged = False

                self.last_update_time = pygame.time.get_ticks()

    def _init_speed_boost(self):
        """Initialize speed boost attributes."""
        self.speed_boost_active = False
        self.speed_boost_start_time = 0
        self.speed_boost_duration = 5000  # 5 seconds
        self.speed_boost_cooldown = False
        self.speed_boost_cooldown_time = 3000  # 3 seconds
        self.speed_boost_cooldown_start = 0

    def move(self, keys, maze):
        """Handle Bunny's movement depending on mode."""
        moving = False
        new_direction = self.current_direction
        x, y = int(self.x), int(self.y)

        # Movement logic
        if keys[pygame.K_LEFT] and maze.grid[self.y][self.x - 1] == 0:
            self.target_x -= 1
            new_direction = "left"
            moving = True
        elif keys[pygame.K_RIGHT] and maze.grid[self.y][self.x + 1] == 0:
            self.target_x += 1
            new_direction = "right"
            moving = True
        elif keys[pygame.K_UP] and maze.grid[self.y - 1][self.x] == 0:
            self.target_y -= 1
            new_direction = "back"
            moving = True
        elif keys[pygame.K_DOWN] and maze.grid[self.y + 1][self.x] == 0:
            self.target_y += 1
            new_direction = "front"
            moving = True

        # Smooth movement interpolation
        self.x += (self.target_x - self.x) * self.speed
        self.y += (self.target_y - self.y) * self.speed

        # Update direction and frame
        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0

        # Update collision rect
        self.rect.topleft = (self.x * Config.get("bun_size"), self.y * Config.get("bun_size"))
        return moving

    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw the Bunny's current frame on the screen."""
        frame_type = f"{self.current_direction}_damage" if self.damaged else self.current_direction
        if self.frames[frame_type]:
            self.current_frame = self.current_frame % len(self.frames[frame_type])
            screen.blit(self.frames[frame_type][self.current_frame],
                        (self.x * Config.get("bun_size") - camera_x, self.y * Config.get("bun_size") - camera_y))
