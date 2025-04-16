import pygame
import random
from config import Config

class Tile:
    def __init__(self, tile_type='dirt'):
        self.type = tile_type
        self.dug = False

    def dig(self):
        if self.type == 'dirt':
            self.dug = True

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


class Farm:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile('dirt') for _ in range(width)] for _ in range(height)]

        self.populate_obstacles()

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

    def draw(self, screen, camera_x, camera_y):
        size = Config.get('bun_size')
        for y in range(self.height):
            for x in range(self.width):
                screen_x = x * size - camera_x
                screen_y = y * size - camera_y

                # Only draw visible tiles
                if -size < screen_x < Config.get('wx') and -size < screen_y < Config.get('wy'):
                    self.tiles[y][x].draw(screen, screen_x, screen_y)

    def dig_tile_at(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            tile = self.tiles[tile_y][tile_x]
            if tile.type == 'dirt':
                tile.dig()
