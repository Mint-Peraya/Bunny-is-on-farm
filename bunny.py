import pygame
from config import Config
import random

class Frame():
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
        self.x = x
        self.y = y
        self.normal_speed = 5  # Base speed
        self.speed = self.normal_speed
        self.health = 100
        self.rect = pygame.Rect(self.x, self.y, 64, 64)  # Collision detection
        self.attack_cooldown = 0  

        # Speed Boost Variables
        self.speed_boost_active = False
        self.speed_boost_start_time = 0
        self.speed_boost_duration = 5000  # 5 seconds (5000 ms)

        # Cooldown Variables
        self.speed_boost_cooldown = False
        self.speed_boost_cooldown_time = 3000  # 3 seconds (3000 ms)
        self.speed_boost_cooldown_start = 0

        # Load sprite sheets
        self.front_sheet = Frame(pygame.image.load('BunnyWalk-Sheet.png').convert_alpha())
        self.back_sheet = Frame(pygame.image.load('BunnyWalkBack-Sheet.png').convert_alpha())
        self.right_sheet = Frame(pygame.image.load('BunnyWalkright-Sheet.png').convert_alpha())
        self.left_sheet = Frame(pygame.image.load('BunnyWalkleft-Sheet.png').convert_alpha())

        self.frames_front = [self.front_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_back = [self.back_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_right = [self.right_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
        self.frames_left = [self.left_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]

        self.current_direction = 'front'
        self.current_frame = 0
        self.frame_time = 60
        self.last_update_time = pygame.time.get_ticks()

    def move(self, keys):
        """Update bunny's position based on key presses."""
        moving = False
        current_time = pygame.time.get_ticks()
        new_direction = self.current_direction  # Track if direction changes

        # Handle Speed Boost Cooldown
        if self.speed_boost_cooldown and current_time - self.speed_boost_cooldown_start >= self.speed_boost_cooldown_time:
            self.speed_boost_cooldown = False

        if keys[pygame.K_f] and not self.speed_boost_active and not self.speed_boost_cooldown:
            self.speed_boost_active = True
            self.speed_boost_start_time = current_time
            self.speed = self.normal_speed * 2  

        if self.speed_boost_active and current_time - self.speed_boost_start_time >= self.speed_boost_duration:
            self.speed_boost_active = False
            self.speed = self.normal_speed  
            self.speed_boost_cooldown = True  
            self.speed_boost_cooldown_start = current_time  

        # Movement & Direction Change Detection
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
            new_direction = 'left'
            moving = True
        elif keys[pygame.K_RIGHT]:
            self.x += self.speed
            new_direction = 'right'
            moving = True
        elif keys[pygame.K_UP]:
            self.y -= self.speed
            new_direction = 'back'
            moving = True
        elif keys[pygame.K_DOWN]:
            self.y += self.speed
            new_direction = 'front'
            moving = True

        # If direction changed, reset animation frame
        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0  # Reset frame to avoid out-of-range issues

        self.rect.topleft = (self.x, self.y)
        return moving




    def attack(self, enemies):
        """Attack enemies in range."""
        if self.attack_cooldown == 0:
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):  # Check if bunny is colliding with an enemy
                    enemy.take_damage()
            self.attack_cooldown = 20  # Cooldown frames before next attack

    def update(self):
        """Update bunny's status."""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def draw(self, screen):
        """Draw the bunny's current frame on the screen."""
        # Draw the current frame based on direction
        if self.current_direction == 'front':
            screen.blit(self.frames_front[self.current_frame], (self.x, self.y))
        elif self.current_direction == 'left':
            screen.blit(self.frames_left[self.current_frame], (self.x, self.y))
        elif self.current_direction == 'right':
            screen.blit(self.frames_right[self.current_frame], (self.x, self.y))
        elif self.current_direction == 'back':
            screen.blit(self.frames_back[self.current_frame], (self.x, self.y))

        # Draw health bar
        self.draw_health_bar(screen)

    def draw_health_bar(self, screen):
        """Draw the bunny's health bar on the screen."""
        pygame.draw.rect(screen, (255, 0, 0), (self.x +8, self.y - 10, 50, 5))  # Red health bar background
        pygame.draw.rect(screen, (0, 255, 0), (self.x +8, self.y - 10, self.health / 2, 5))  # Green health bar

    def take_damage(self):
        """Reduce health when taking damage."""
        self.health -= 1
        if self.health <= 0:
            print("Game Over!")
            pygame.quit()
            exit()

    def update_animation(self, moving):
        """Update the frame if moving."""
        current_time = pygame.time.get_ticks()
        
        if moving and current_time - self.last_update_time > self.frame_time:
            frame_dict = {
                'front': self.frames_front,
                'left': self.frames_left,
                'right': self.frames_right,
                'back': self.frames_back
            }
            
            if self.current_direction in frame_dict:
                max_frames = len(frame_dict[self.current_direction])  # Get correct frame count
                if max_frames > 0:
                    self.current_frame = (self.current_frame + 1) % max_frames  # Prevent IndexError
            
            self.last_update_time = current_time  # Update time





# Initialize pygame
pygame.init()

# Screen dimensions
screen = pygame.display.set_mode(Config.get('window'))

# Create bunny instance
bunny = Bunny(Config.get('wx')// 2, Config.get('wy') // 2)

rect_size = 64
rect_x = (800 ) // 2
rect_y = (600 ) // 2

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Get key presses
    keys = pygame.key.get_pressed()
    moving = bunny.move(keys)
    bunny.update_animation(moving)
    bunny.update()

    # Clear the screen (MUST come before drawing objects)
    screen.fill((100, 100, 100))

    # Draw the red rectangle in the center (AFTER filling the screen)
    pygame.draw.rect(screen, (255, 0, 0), (rect_x, rect_y, rect_size, rect_size)) 

    # Draw the bunny
    bunny.draw(screen)

    # Update the display
    pygame.display.update()

    # Cap the frame rate
    pygame.time.Clock().tick(60)

pygame.quit()
