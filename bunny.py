import pygame
from config import Config

class Bunny:
    def __init__(self, x, y, mode="farming"):
        self.x, self.y = x, y
        self.health = 100
        self.attack_power = 10
        self.speed = 0.16
        self.target_x, self.target_y = x, y

        self.current_direction = "front"
        self.next_direction = None
        self.mode = mode  # Modes: "maze", "farming", "dungeon"

        # Animation state
        self.current_frame = 0
        self.movement_per_frame = 1/5
        self.last_frame_index = 0
        self.is_moving = False
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

#         self.sounds = {
#     "grass": pygame.mixer.Sound("assets/sounds/step_grass.wav"),
#     "dirt": pygame.mixer.Sound("assets/sounds/step_dirt.wav"),
#     "stone": pygame.mixer.Sound("assets/sounds/step_stone.wav")
# }

        # Rect for collision
        tile_size = Config.get("bun_size")
        self.rect = pygame.Rect(self.x * tile_size, self.y * tile_size, tile_size, tile_size)

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
        self.is_moving = moving

        if moving or self.attacking or self.damaged:
            if pygame.time.get_ticks() - self.last_update_time > 60:
                frame_type = f"{self.current_direction}_damage" if self.damaged else self.current_direction
                frames = self.frames[frame_type]
                self.current_frame = (self.current_frame + 1) % len(frames)

                # Check if we changed frame
                if self.current_frame != self.last_frame_index:
                    self._step_movement(frame_type)
                    self.last_frame_index = self.current_frame

                # Reset effects
                if self.attacking and self.current_frame == 0:
                    self.attacking = False
                if self.damaged and pygame.time.get_ticks() - self.damage_start_time >= self.damage_duration:
                    self.damaged = False

                self.last_update_time = pygame.time.get_ticks()
    
    def _step_movement(self, frame_type):
        """Move Bunny a little bit per frame step."""
        dx, dy = 0, 0
        step = self.movement_per_frame

        if self.target_x > self.x:
            dx = step
        elif self.target_x < self.x:
            dx = -step

        if self.target_y > self.y:
            dy = step
        elif self.target_y < self.y:
            dy = -step

        self.x += dx
        self.y += dy

        # Update collision rect
        self.rect.topleft = (self.x * Config.get("bun_size"), self.y * Config.get("bun_size"))

        # Play step sound (based on current tile type)
        # self._play_step_sound()


    def _init_speed_boost(self):
        """Initialize speed boost attributes."""
        self.speed_boost_active = False
        self.speed_boost_start_time = 0
        self.speed_boost_duration = 5000  # 5 seconds
        self.speed_boost_cooldown = False
        self.speed_boost_cooldown_time = 3000  # 3 seconds
        self.speed_boost_cooldown_start = 0

    def move(self, keys, maze):
        """Handle Bunny's movement with precise 0.1 grid steps, checking walkable tiles."""
        moving = False
        new_direction = self.current_direction
        
        # Get current grid position (integer)
        grid_x, grid_y = int(self.x), int(self.y)

        # Check if bunny is at a valid stopping point (0.1 grid increments)
        at_step_position = (
            abs(self.x - round(self.x, 1)) < 0.001 and 
            abs(self.y - round(self.y, 1)) < 0.001
        )
        
        if at_step_position:
            dx, dy = 0, 0
            
            if keys[pygame.K_LEFT]:
                dx = -0.1
                new_direction = "left"
            elif keys[pygame.K_RIGHT]:
                dx = 0.1
                new_direction = "right"
            elif keys[pygame.K_UP]:
                dy = -0.1
                new_direction = "back"
            elif keys[pygame.K_DOWN]:
                dy = 0.1
                new_direction = "front"
            
            # Only move if there's input
            if dx != 0 or dy != 0:
                # Check the NEXT FULL GRID CELL in movement direction
                check_x = grid_x + (1 if dx > 0 else (-1 if dx < 0 else 0))
                check_y = grid_y + (1 if dy > 0 else (-1 if dy < 0 else 0))
                
                # Verify target grid cell is walkable (dirt tile)
                if maze.is_walkable(check_x, check_y):  # 0 represents walkable dirt
                    self.x = round(self.x + dx, 1)  # Move exactly 0.1
                    self.y = round(self.y + dy, 1)
                    moving = True
                    # Advance animation frame with each step
                    frame_type = f"{new_direction}_damage" if self.damaged else new_direction
                    self.current_frame = (self.current_frame + 1) % len(self.frames[frame_type])
        
        # Update direction if changed
        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0
        
        # Update collision rect
        tile_size = Config.get("bun_size")
        self.rect.topleft = (self.x * tile_size, self.y * tile_size)
        
        return moving

    def update_animation(self, moving):
        current_time = pygame.time.get_ticks()

        # Damage and attack effects
        if self.damaged and current_time - self.damage_start_time >= self.damage_duration:
            self.damaged = False
        if self.attacking and current_time - self.attack_cooldown >= 500:
            self.attacking = False

        # Movement animation
        if moving:
            if current_time - self.last_update_time > 60:
                frame_type = f"{self.current_direction}_damage" if self.damaged else self.current_direction
                self.current_frame = (self.current_frame + 1) % len(self.frames[frame_type])
                self.last_update_time = current_time
    

    def has_reached_target(self):
        """Check if bunny has reached its target position."""
        return abs(self.x - self.target_x) < 0.01 and abs(self.y - self.target_y) < 0.01
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw the Bunny's current frame on the screen."""
        frame_type = f"{self.current_direction}_damage" if self.damaged else self.current_direction
        if self.frames[frame_type]:
            self.current_frame = self.current_frame % len(self.frames[frame_type])
            screen.blit(self.frames[frame_type][self.current_frame],
                        (self.x * Config.get("bun_size") - camera_x, self.y * Config.get("bun_size") - camera_y))
