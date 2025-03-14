import pygame
import random
import sys
import math
from bunny import Bunny
from config import Config



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


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.running = True
        self.reset_game()

    def reset_game(self):
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.bunny = Bunny(1, 1)
        self.exit_x, self.exit_y = self.get_random_exit()
        self.game_over = False
        self.camera_x, self.camera_y = 0, 0

    def get_random_exit(self, min_distance=20):
        while True:
            x, y = random.randint(1, Config.get('grid') - 2), random.randint(1, Config.get('grid') - 2)
            if self.maze.grid[y][x] == 0 and abs(x - self.bunny.x) + abs(y - self.bunny.y) >= min_distance:
                return x, y

    def draw_text(self, text, font_size, color, position):
        font = pygame.font.SysFont(None, font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw_compass(self):
        dx, dy = self.exit_x - self.bunny.x, self.exit_y - self.bunny.y
        angle = math.atan2(dy, dx)
        compass_x, compass_y, compass_radius = Config.get('wx') - 100, 50, 40
        pygame.draw.circle(self.screen, Config.get('white'), (compass_x, compass_y), compass_radius, 2)
        arrow_end_x = compass_x + (compass_radius - 10) * math.cos(angle)
        arrow_end_y = compass_y + (compass_radius - 10) * math.sin(angle)
        pygame.draw.line(self.screen, Config.get('red'), (compass_x, compass_y), (arrow_end_x, arrow_end_y), 3)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and not self.game_over and event.key == pygame.K_r:
                self.reset_game()

    def update(self):
        keys = pygame.key.get_pressed()
        moving = self.bunny.move(keys, self.maze)
        self.bunny.update_animation(moving)
        self.camera_x += (self.bunny.x * Config.get('bun_size') - Config.get('wx') // 2 - self.camera_x) * 0.1
        self.camera_y += (self.bunny.y * Config.get('bun_size') - Config.get('wy') // 2 - self.camera_y) * 0.1

    def render(self):
        self.screen.fill(Config.get('black'))
        self.maze.draw(self.screen, self.camera_x, self.camera_y)
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)
        # portal
        pygame.draw.rect(self.screen, Config.get('purple'),
                         (1 * Config.get('bun_size') - self.camera_x, 1 * Config.get('bun_size') - self.camera_y, Config.get('bun_size'), Config.get('bun_size')))
        # chest
        pygame.draw.rect(self.screen, Config.get('peach'), (
        # portal
        self.exit_x * Config.get('bun_size') - self.camera_x, self.exit_y * Config.get('bun_size') - self.camera_y, Config.get('bun_size'), Config.get('bun_size')))
        pygame.draw.rect(self.screen, Config.get('purple'), (
        self.exit_x * Config.get('bun_size') - self.camera_x, self.exit_y * Config.get('bun_size') - self.camera_y, Config.get('bun_size'), Config.get('bun_size')), 3)
        
        self.draw_compass()
        if self.bunny.x == self.exit_x and self.bunny.y == self.exit_y:
            self.game_over = True
            self.draw_text("You Win!", 55, Config.get('green'), (Config.get('wx') // 2 - 70, Config.get('wy') // 2 - 30))
            pygame.display.flip()
            pygame.time.wait(2000)
            self.reset_game()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()