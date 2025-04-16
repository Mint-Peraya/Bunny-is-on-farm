import pygame
import random
from config import Config
from object import *

class Tile:
    def __init__(self, tile_type='dirt', x=0, y=0):
        self.type = tile_type
        self.dug = False
        self.tile_x = x
        self.tile_y = y
        self.health = 10 if tile_type in ('tree', 'stone') else 0
        self.max_health = 10 if tile_type in ('tree', 'stone') else 0
        self.interactables = []
        self.plant = None
        self.watered = False
        self.last_watered = 0

    def water(self):
        self.watered = True
        self.last_watered = pygame.time.get_ticks()
    
    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y


    def dig(self):
        if self.type == 'dirt':
            self.dug = True
            return True
        return False

    def take_damage(self, amount):
        if self.type in ('tree', 'stone'):
            self.health = max(0, self.health - amount)
            return self.health <= 0
        return False

    def draw(self, screen, camera_x, camera_y):
        size = Config.get('bun_size')
        x = self.tile_x * size - camera_x
        y = self.tile_y * size - camera_y
        
        colors = {
            'dirt': (139, 69, 19),
            'stone': (120, 120, 120),
            'tree': (34, 139, 34),
            'stump': (60, 30, 10)
        }
        
        color = colors.get(self.type, (160, 100, 50)) if not self.dug else (160, 100, 50)
        pygame.draw.rect(screen, color, (x, y, size, size))
        
        if self.type in ('tree', 'stone') and self.health < self.max_health:
            bar_width = size - 10
            bar_height = 5
            health_percent = self.health / self.max_health
            pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, int(bar_width * health_percent), bar_height))
        if self.watered:
            water_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            water_overlay.fill((0, 100, 255, 60))
            screen.blit(water_overlay, (x, y))

    def update(self):
        if self.watered and pygame.time.get_ticks() - self.last_watered > 10000:  # 10 sec
            self.watered = False

class Farm:
    def __init__(self, game, width=50, height=30):
        self.game = game
        self.width = width
        self.height = height
        self.tiles = [[Tile('dirt', x, y) for x in range(width)] for y in range(height)]
        self.interactables = []
        
        # Initialize terrain
        self._generate_terrain()
        
    def _generate_terrain(self):
        """Generate trees, stones, and other terrain features"""
        # Add some trees
        for _ in range(10):
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            self.tiles[y][x].type = 'tree'
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10
        
        # Add some stones
        for _ in range(8):
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            self.tiles[y][x].type = 'stone'
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.game.bunny.check_for_interaction(self.interactables, self.game)

    def update(self):
        for obj in self.interactables:
            if hasattr(obj, 'update'):
                obj.update()

    def draw(self, screen, camera_x, camera_y):
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, camera_x, camera_y)
        
        # Draw interactables
        for obj in self.interactables:
            if hasattr(obj, 'draw'):
                obj.draw(screen, camera_x, camera_y)
        


class Plant:
    def __init__(self, growth_stages, grow_time=300):
        self.growth_stages = growth_stages  # list of images or colors
        self.grow_time = grow_time  # ms per stage
        self.stage = 0
        self.planted_time = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if self.stage < len(self.growth_stages) - 1:
            if now - self.planted_time > self.grow_time:
                self.stage += 1
                self.planted_time = now

    def draw(self, screen, x, y, tile_size):
        color = self.growth_stages[self.stage]
        pygame.draw.rect(screen, color, (x, y, tile_size, tile_size))
