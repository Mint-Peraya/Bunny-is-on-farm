import pygame
import random
from config import Config

# Portal class
class Portal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 50, 50)
    
    def draw(self, screen):
        pygame.draw.rect(screen, Config.get('purple'), self.rect)
    
    def check_collision(self, bunny):
        return bunny.rect.colliderect(self.rect)

# Dungeon class
class Dungeon:
    def __init__(self):
        self.type = random.choice(["maze", "pvp"])
        self.enemies = [Enemy(random.randint(100, 700), random.randint(100, 500)) for _ in range(3)]
    
    def draw(self, screen):
        if self.type == "maze":
            screen.fill((30, 30, 30))  # Darker background for maze
        else:
            screen.fill((50, 50, 50))  # PVP dungeon background
        
        for enemy in self.enemies:
            enemy.draw(screen)
    
    def update(self, bunny):
        for enemy in self.enemies:
            enemy.update(bunny)
    
    def check_collision(self, bunny):
        for enemy in self.enemies:
            if bunny.rect.colliderect(enemy.rect) and enemy.state == "chase":
                bunny.take_damage()
                return True
        return False
    
# Enemy class
class Enemy():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.health = 2
        self.rect = pygame.Rect(self.x, self.y, 40, 40)
        self.original_position = (x, y)
        self.state = "chase"  # Possible states: "chase", "flee", "return"
        self.flee_timer = 0
    
    def update(self, bunny):
        if self.state == "chase":
            if self.x < bunny.x:
                self.x += self.speed
            elif self.x > bunny.x:
                self.x -= self.speed
            if self.y < bunny.y:
                self.y += self.speed
            elif self.y > bunny.y:
                self.y -= self.speed
        
        elif self.state == "flee":
            self.flee_timer -= 1
            if self.flee_timer <= 0:
                self.state = "return"
            else:
                self.x += random.choice([-3, 3])
                self.y += random.choice([-3, 3])
        
        elif self.state == "return":
            if abs(self.x - self.original_position[0]) < 5 and abs(self.y - self.original_position[1]) < 5:
                self.state = "chase"
            else:
                if self.x < self.original_position[0]:
                    self.x += self.speed
                elif self.x > self.original_position[0]:
                    self.x -= self.speed
                if self.y < self.original_position[1]:
                    self.y += self.speed
                elif self.y > self.original_position[1]:
                    self.y -= self.speed
        
        self.rect.topleft = (self.x, self.y)
    
    def flee(self):
        self.state = "flee"
        self.flee_timer = 60  # Frames to flee
    
    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            Dungeon.enemies.remove(self)
        else:
            self.flee()
    
    def draw(self, screen):
        pygame.draw.rect(screen, Config.get('bunny'), self.rect)
