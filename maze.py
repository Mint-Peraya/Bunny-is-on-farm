from config import Config
import random
import pygame

class Maze:
    DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]
        self.generate_maze(1, 1)
        self.add_loops(10)

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

    def draw(self, screen, camera_x, camera_y):
        for y in range(self.rows):
            for x in range(self.cols):
                color = Config.get('black') if self.grid[y][x] == 1 else Config.get('white')
                pygame.draw.rect(screen, color,
                                 (x * Config.get('bun_size') - camera_x, y * Config.get('bun_size') - camera_y, Config.get('bun_size'), Config.get('bun_size')))
