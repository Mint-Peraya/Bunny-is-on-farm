import pygame
from config import Config
from login import *
from maze import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.running = True
        self.reset_game()

    def reset_game(self):
        # Initialize the maze
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.bunny = Bunny(1, 1, mode='maze')
        self.exit_x, self.exit_y = self.maze.get_random_exit()  # Use Maze's method to get a valid exit
        self.game_over = False
        self.camera_x, self.camera_y = 0, 0

    def update(self):
        keys = pygame.key.get_pressed()
        moving = self.bunny.move(keys, self.maze)
        self.bunny.update_animation(moving)

        # Update camera position
        self.camera_x += (self.bunny.x * Config.get('bun_size') - Config.get('wx') // 2 - self.camera_x) * 0.1
        self.camera_y += (self.bunny.y * Config.get('bun_size') - Config.get('wy') // 2 - self.camera_y) * 0.1

    def draw_text(self, text, font_size, color, position):
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw_compass(self):
        dx, dy = self.exit_x - int(self.bunny.x), self.exit_y - int(self.bunny.y)
        if dx == 0 and dy == 0:
            angle = 0
        else:
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

    def render(self):
        self.screen.fill(Config.get('black'))

        # Draw the maze
        self.maze.draw(self.screen, self.camera_x, self.camera_y)

        # Draw the begin portal
        pygame.draw.rect(self.screen, Config.get('purple'), (
            1 * Config.get('bun_size') - self.camera_x, 1 * Config.get('bun_size') - self.camera_y, 
            Config.get('bun_size'), Config.get('bun_size')), 0)

        # Draw the bunny
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)

        # Draw the exit portal
        pygame.draw.rect(self.screen, Config.get('purple'), (
            self.exit_x * Config.get('bun_size') - self.camera_x, 
            self.exit_y * Config.get('bun_size') - self.camera_y, 
            Config.get('bun_size'), Config.get('bun_size')), 0)

        # Draw the compass
        self.draw_compass()

        # Check for win condition using integer positions
        if int(self.bunny.x) == self.exit_x and int(self.bunny.y) == self.exit_y:
            self.game_over = True
            self.draw_text("You Win!", 55, Config.get('green'), 
                          (Config.get('wx') // 2 - 70, Config.get('wy') // 2 - 30))
            pygame.display.flip()
            pygame.time.wait(2000)
            self.reset_game()

        # Display health
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

    def opening_scene(self):
        while self.running:
            self.screen.fill(Config.get('black'))
        pygame.quit()


# Game().opening_scene()
# Game().run()


