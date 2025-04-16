import pygame
from config import Config
from login import *
from maze import *
from try2 import *

class Portal:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y

    def draw(self, screen, camera_x, camera_y):
        tile_size = Config.get('bun_size')
        center_x = self.tile_x * tile_size + tile_size // 2 - camera_x
        center_y = self.tile_y * tile_size + tile_size // 2 - camera_y
        base_radius = tile_size // 2 - 8

        time = pygame.time.get_ticks() / 300
        pulse = math.sin(time) * 3

        for i in range(3):
            aura_radius = base_radius + 6 + i * 4 + pulse
            alpha = 50 - i * 15
            aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(aura_surf, (*Config.get('dark_purple'), alpha),
                               (aura_radius, aura_radius), int(aura_radius))
            screen.blit(aura_surf, (center_x - aura_radius, center_y - aura_radius))

        pygame.draw.circle(screen, Config.get('dark_purple'), (center_x, center_y), int(base_radius))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.running = True
        self.reset_game()

    def reset_game(self):
        self.farm = Farm(5000,3000)
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.bunny = Bunny(1, 1, mode='maze')
        self.exit = self.maze.get_random_exit()
        self.start_portal = Portal(1, 1)
        self.exit_portal = Portal(self.exit[0], self.exit[1])
        self.game_over = False
        self.camera_x, self.camera_y = 0, 0

    def update(self):
        keys = pygame.key.get_pressed()
        moving = self.bunny.move(keys, self.maze)
        self.bunny.update_animation(moving)

        self.camera_x += (self.bunny.x * Config.get('bun_size') - Config.get('wx') // 2 - self.camera_x) * 0.1
        self.camera_y += (self.bunny.y * Config.get('bun_size') - Config.get('wy') // 2 - self.camera_y) * 0.1

    def draw_text(self, text, font_size, color, position):
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and not self.game_over and event.key == pygame.K_r:
                self.reset_game()

    def render(self):
        self.screen.fill(Config.get('black'))

        # Draw farm first as background
        self.farm.draw(self.screen, self.camera_x, self.camera_y)

        # Allow digging
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.farm.dig_tile_at(int(self.bunny.x), int(self.bunny.y))

        # Then maze on top of farm
        self.maze.draw(self.screen, self.camera_x, self.camera_y)

        # Draw portals
        self.start_portal.draw(self.screen, self.camera_x, self.camera_y)
        self.exit_portal.draw(self.screen, self.camera_x, self.camera_y)

        # Draw bunny and compass
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)
        self.maze.draw_compass(self.screen, self.bunny, self.exit)

        # Win condition
        if int(self.bunny.x) == self.exit[0] and int(self.bunny.y) == self.exit[1]:
            self.game_over = True
            self.draw_text("You Win!", 55, Config.get('green'),
                        (Config.get('wx') // 2 - 70, Config.get('wy') // 2 - 30))
            pygame.display.flip()
            pygame.time.wait(2000)
            self.reset_game()

        # UI
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))

        pygame.display.flip()

    def farm_render(self):
        # Draw the farm
        self.farm.draw(self.screen, self.camera_x, self.camera_y)

        # Handle digging (space key)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.farm.dig_tile_at(int(self.bunny.x), int(self.bunny.y))

        # Draw bunny, maze, portals
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)
        self.start_portal.draw(self.screen, self.camera_x, self.camera_y)
        self.exit_portal.draw(self.screen, self.camera_x, self.camera_y)
        self.maze.draw_compass(self.screen, self.bunny, self.exit)

        # Draw HUD
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))
        pygame.display.flip()



    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.farm_render()
            self.clock.tick(60)
        pygame.quit()

Game().run()


