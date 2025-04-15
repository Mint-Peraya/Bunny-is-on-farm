import pygame
import random
import sys
import math
from config import Config
from try2 import Bunny

class Maze:
    DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]
        self.generate_maze(1, 1)
        self.add_loops(10)

        # Load and scale images with convert_alpha()
        self.bush_tile = pygame.image.load("assets/picture/bush_dun1.png").convert_alpha()
        self.dirt_tile = pygame.image.load("assets/picture/dirt_dun.png").convert_alpha()
        tile_size = Config.get('bun_size')
        self.bush_tile = pygame.transform.scale(self.bush_tile, (tile_size, tile_size))
        self.dirt_tile = pygame.transform.scale(self.dirt_tile, (tile_size, tile_size))

    def get_tile_type(self, x, y):
        if self.grid[y][x] == 1:
            return "stone"  # wall (optional, if you want)
        else:
            return "dirt"  # change this based on your tiles
    
    def generate_maze(self, x, y):
        self.grid[y][x] = 0
        directions = self.DIRECTIONS.copy()
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 1:
                self.grid[y + dy][x + dx] = 0
                self.generate_maze(nx, ny)

    def add_loops(self, num_loops):
        for _ in range(num_loops):
            x, y = random.randint(1, self.cols - 2), random.randint(1, self.rows - 2)
            if self.grid[y][x] == 1:
                self.grid[y][x] = 0

    def get_random_exit(self, min_distance=2):
        """Generate a random exit position on a walkable tile."""
        while True:
            x, y = random.randint(1, self.cols - 2), random.randint(1, self.rows - 2)
            if self.grid[y][x] == 0:  # Ensure the exit is on a walkable tile
                return x, y

    def draw(self, screen, camera_x, camera_y):
        for y in range(self.rows):
            for x in range(self.cols):
                tile_image = self.bush_tile if self.grid[y][x] == 1 else self.dirt_tile
                screen.blit(tile_image, (x * Config.get('bun_size') - camera_x, y * Config.get('bun_size') - camera_y))

    def is_walkable(self, x, y):
        return 0 <= x < len(self.grid[0]) and 0 <= y < len(self.grid) and self.grid[y][x] == 0

