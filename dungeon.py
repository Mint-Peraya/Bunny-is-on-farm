import pygame
import random
from config import Config

class Dungeon:
    def __init__(self):
        self.type = random.choice(["maze", "pvp"])
        self.enemies = [Enemy(random.randint(100, 700), random.randint(100, 500)) for _ in range(3)]
        self.obstacles = []  # Add obstacles here

    def draw(self, screen):
        if self.type == "maze":
            screen.fill((30, 30, 30))  # Darker background for maze
        else:
            screen.fill((50, 50, 50))  # PVP dungeon background
        
        for enemy in self.enemies:
            enemy.draw(screen)
        
        for obstacle in self.obstacles:
            obstacle.draw(screen)

    def update(self, bunny):
        for enemy in self.enemies:
            enemy.update(bunny)
    
    def check_collision(self, bunny):
        for enemy in self.enemies:
            if bunny.rect.colliderect(enemy.rect) and enemy.state == "chase":
                bunny.take_damage(1)  # Bunny takes 10 damage
                return True
        return False

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 2
        self.health = 20
        self.rect = pygame.Rect(self.x, self.y, 40, 40)
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
        
        self.rect.topleft = (self.x, self.y)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            # Handle enemy death logic here

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect)  # Draw enemy as a red rectangle