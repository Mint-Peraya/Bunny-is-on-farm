import pygame
import random,math
from config import Config
from bunny import Bunny

class PVPSpace:
    def __init__(self):
        self.grid_size = 20  # 20x20 grid
        self.enemies = [Enemy(random.randint(0, 19)*64, random.randint(0, 19)*64) for _ in range(5)]
        self.portal = Portal(random.randint(15, 19)*64, random.randint(15, 19)*64)
        self.items = []
        self.walls = self.generate_walls()

    def generate_walls(self):
        # Create border walls
        walls = []
        for x in range(20):
            walls.append(pygame.Rect(x*64, 0, 64, 64))            # Top
            walls.append(pygame.Rect(x*64, 19*64, 64, 64))        # Bottom
        for y in range(1, 19):
            walls.append(pygame.Rect(0, y*64, 64, 64))            # Left
            walls.append(pygame.Rect(19*64, y*64, 64, 64))        # Right
        return walls

    def update(self, bunny):
        for enemy in self.enemies[:]:
            enemy.update(bunny)
            if enemy.health <= 0:
                self.enemies.remove(enemy)
                self.items.append(Item(enemy.x, enemy.y))

        for item in self.items[:]:
            if bunny.rect.colliderect(item.rect):
                bunny.collect_item(item)
                self.items.remove(item)

    def draw(self, screen, camera_x, camera_y):
        # Draw background
        screen.fill((30, 30, 30))
        
        # Draw walls
        for wall in self.walls:
            pygame.draw.rect(screen, (100, 100, 100), wall.move(-camera_x, -camera_y))
        
        # Draw portal
        self.portal.draw(screen, camera_x, camera_y)
        
        # Draw enemies and items
        for enemy in self.enemies:
            enemy.draw(screen, camera_x, camera_y)
        for item in self.items:
            item.draw(screen, camera_x, camera_y)

class Portal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 64)
    
    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, (200, 0, 200), self.rect.move(-camera_x, -camera_y))

class Item:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.type = random.choice(["health", "speed", "damage"])
    
    def draw(self, screen, camera_x, camera_y):
        color = {
            "health": (0, 255, 0),
            "speed": (0, 0, 255),
            "damage": (255, 0, 0)
        }[self.type]
        pygame.draw.rect(screen, color, self.rect.move(-camera_x, -camera_y))

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3
        self.health = 50
        self.rect = pygame.Rect(x, y, 64, 64)
        self.state = "patrol"
        self.patrol_target = (random.randint(0, 19)*64, random.randint(0, 19)*64)

    def update(self, bunny):
        if self.state == "chase":
            dx = bunny.rect.x - self.x
            dy = bunny.rect.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                self.x += dx/distance * self.speed
                self.y += dy/distance * self.speed
        else:
            # Patrol logic
            dx = self.patrol_target[0] - self.x
            dy = self.patrol_target[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                self.x += dx/distance * self.speed/2
                self.y += dy/distance * self.speed/2
                if distance < 10:
                    self.patrol_target = (random.randint(0, 19)*64, random.randint(0, 19)*64)

        self.rect.topleft = (int(self.x), int(self.y))

    def draw(self, screen, camera_x, camera_y):
        pygame.draw.rect(screen, (255, 0, 0), self.rect.move(-camera_x, -camera_y))
