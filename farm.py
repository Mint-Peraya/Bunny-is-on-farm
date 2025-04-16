import pygame
import random
from config import Config

class Tile:
    def __init__(self, tile_type='dirt', x=0, y=0):
        self.type = tile_type
        self.dug = False
        self.tile_x = x  # Track position
        self.tile_y = y
        self.health = 10 if tile_type in ('tree', 'stone') else 0
        self.max_health = 10 if tile_type in ('tree', 'stone') else 0
        self.interactables = []

    def dig(self):
        if self.type == 'dirt':
            self.dug = True

    def take_damage(self, amount):
        if self.type in ('tree', 'stone'):
            self.health = max(0, self.health - amount)
            return self.health <= 0
        return False

    def draw(self, screen, x, y):
        size = Config.get('bun_size')
        color = (139, 69, 19)  # Dirt

        if self.type == 'stone':
            color = (120, 120, 120)
        elif self.type == 'tree':
            color = (34, 139, 34)
        elif self.dug:
            color = (160, 100, 50)

        pygame.draw.rect(screen, color, (x, y, size, size))
        
        # Draw health bar for resources
        if self.type in ('tree', 'stone') and self.health < self.max_health:
            bar_width = size - 10
            bar_height = 5
            health_percent = self.health / self.max_health
            pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, int(bar_width * health_percent), bar_height))


class Farm:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile('dirt', x, y) for x in range(width)] for y in range(height)]
        self.populate_obstacles()
        self.interactables = []

        # Add more interactables like chests, beds, etc. if needed
        # self.chest = Chest(tile_x=3, tile_y=6)
        # self.interactables.append(self.chest)

    def populate_obstacles(self):
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self._get_home_area():  # Skip starting area
                    continue
                r = random.random()
                if r < 0.05:
                    self.tiles[y][x] = Tile('tree')
                elif r < 0.08:
                    self.tiles[y][x] = Tile('stone')

    def _get_home_area(self):
        # Protect a small 5x5 area around (1,1)
        return {(hx, hy) for hx in range(0, 5) for hy in range(0, 5)}

    # In Farm.draw() - optimize rendering
    def draw(self, screen, camera_x, camera_y):
        size = Config.get('bun_size')
        start_x = max(0, int(camera_x // size))
        end_x = min(self.width, int((camera_x + Config.get('wx')) // size + 1))
        start_y = max(0, int(camera_y // size))
        end_y = min(self.height, int((camera_y + Config.get('wy')) // size + 1))
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x = x * size - camera_x
                screen_y = y * size - camera_y
                self.tiles[y][x].draw(screen, screen_x, screen_y)

    def dig_tile_at(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            tile = self.tiles[tile_y][tile_x]
            if tile.type == 'dirt':
                tile.dig()
