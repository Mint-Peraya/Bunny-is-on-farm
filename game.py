import pygame
import math
from config import *
from maze import Maze
from bunny import Bunny
from farm import *

class Portal:
    def __init__(self, tile_x, tile_y, target_world='maze', target_pos=(1, 1)):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.target_world = target_world
        self.target_pos = target_pos
        self.size = Config.get('bun_size')
        self.interact_text = "Enter portal (SPACE)"

    def draw_interaction(self, screen):
        """Draw interaction prompt"""
        if self.interact_text:
            font = pygame.font.Font(Config.get('font'), 24)
            text_surface = font.render(self.interact_text, True, Config.get('white'))
            screen.blit(text_surface, (10, 10))

    def check_collision(self, bunny):
        """Check if bunny is touching the portal"""
        portal_rect = pygame.Rect(
            self.tile_x * self.size,
            self.tile_y * self.size,
            self.size,
            self.size
        )
        return bunny.rect.colliderect(portal_rect)

    def draw(self, screen, camera_x, camera_y):
        """Draw the portal with pulsing effect"""
        center_x = self.tile_x * self.size + self.size // 2 - camera_x
        center_y = self.tile_y * self.size + self.size // 2 - camera_y
        base_radius = self.size // 2 - 8

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
    
    def teleport(self, game):
        if self.target_world == 'maze':
            game.warp_to_maze()
        else:
            game.warp_to_farm()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.running = True
        self.interact_font = pygame.font.Font(Config.get('font'), 24)
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.reset_game()

    def init_portals(self):
        self.farm_portal = Portal(self.farm.width - 2, self.farm.height - 2, 'maze', (1, 1))
        self.maze_enterportal = Portal(1, 1, 'farm', (self.farm.width - 2 , self.farm.height - 2))
        self.exit = self.maze.get_random_exit()
        self.maze_exitportal = Portal(self.exit[0], self.exit[1], 'farm', (1, 1))

    def reset_game(self):
        self.farm = Farm(50, 30)
        self.bunny = Bunny(1, 1, mode='farm')
        self.init_portals()
        self.camera_x, self.camera_y = 0, 0
        self.game_over = False
        self.portal_cooldown = 0

    def update(self):
        keys = pygame.key.get_pressed()
        world = self.maze if self.bunny.mode == 'maze' else self.farm
        
        # Reset interactable
        self.bunny.current_interactable = None
        
        # Get position in front of bunny
        front_x, front_y = self.bunny.get_front_position()
        
        # Check for interactables in front
        if self.bunny.mode == 'farm':
            if (0 <= front_x < self.farm.width and 
                0 <= front_y < self.farm.height):
                tile = self.farm.tiles[front_y][front_x]
                if tile.type in ('tree', 'stone') and self.bunny.can_interact_with(tile, world):
                    self.bunny.current_interactable = tile
                    if keys[pygame.K_SPACE]:
                        self.handle_resource_interaction(front_x, front_y)
        
        # Check for portals (in both modes)
        portals = [self.farm_portal] if self.bunny.mode == 'farm' else [self.maze_enterportal, self.maze_exitportal]
        for portal in portals:
            if self.bunny.can_interact_with(portal, world):
                self.bunny.current_interactable = portal
                if keys[pygame.K_SPACE] and self.portal_cooldown <= 0:
                    portal.teleport(self)
                    self.portal_cooldown = 30

        # Update bunny's current action
        self.bunny.update_action()
        
        # Check if still facing the target
        if self.bunny.action_target:
            target_x, target_y = self.bunny.action_target.tile_x, self.bunny.action_target.tile_y
            front_x, front_y = self.bunny.get_front_position()
            if not (target_x == front_x and target_y == front_y):
                self.bunny.current_action = None
                self.bunny.action_target = None
                self.bunny.action_progress = 0

        # Movement and camera updates
        moving = self.bunny.move(keys, world)
        self.bunny.update_animation(moving)
        self.update_camera()
        
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1

    def handle_resource_interaction(self, x, y):
        """Handle gathering resources from farm tiles"""
        tile = self.farm.tiles[y][x]
        bunny = self.bunny
        
        if tile.type == 'tree' and bunny.current_action != 'cut':
            bunny.start_action('cut', tile)
        elif tile.type == 'stone' and bunny.current_action != 'mine':
            bunny.start_action('mine', tile)

    def fade_transition(self):
        fade_surface = pygame.Surface(Config.get('window'))
        fade_surface.fill((0, 0, 0))
        for alpha in range(0, 255, 25):
            fade_surface.set_alpha(alpha)
            self.render()  # Draw the current frame
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(30)

    def warp_to_maze(self):
        """Transition from farm to maze"""
        self.fade_transition()
        self.bunny.mode = 'maze'
        self.teleport_bunny(world=self.maze)
        self.game_over = False

    def warp_to_farm(self):
        """Transition from maze to farm"""
        self.fade_transition()
        self.bunny.mode = 'farm'
        self.teleport_bunny(world=self.farm)
        self.game_over = False

    def render_ui(self):
        """Render UI elements"""
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw HUD
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))
        mode_text = f"Mode: {self.bunny.mode.capitalize()}"
        self.draw_text(mode_text, 25, Config.get('white'), (10, 50))
        
        # Draw interaction prompt if near something
        if self.bunny.current_interactable:
            if hasattr(self.bunny.current_interactable, 'interact_text'):
                text = self.bunny.current_interactable.interact_text
            elif isinstance(self.bunny.current_interactable, Tile):
                if self.bunny.current_interactable.type == 'tree':
                    text = "Chop tree (SPACE)"
                elif self.bunny.current_interactable.type == 'stone':
                    text = "Mine stone (SPACE)"
            else:
                text = "Interact (SPACE)"
            
            self.draw_text(text, 24, Config.get('white'), (10, 80))
        
        # Draw inventory
        self.bunny.inventory.draw(self.screen)
        
        # Draw compass in maze mode
        if self.bunny.mode == 'maze' and not self.game_over:
            self.maze.draw_compass(self.screen, self.bunny, self.exit)

    def update_camera(self, instant=False):
        """Smoothly follow bunny with camera"""
        target_x = self.bunny.x * Config.get('bun_size') - Config.get('wx') // 2
        target_y = self.bunny.y * Config.get('bun_size') - Config.get('wy') // 2
        
        if instant:
            self.camera_x, self.camera_y = target_x, target_y
        else:
            self.camera_x += (target_x - self.camera_x) * 0.1
            self.camera_y += (target_y - self.camera_y) * 0.1

    def handle_events(self):
        """Process user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_m:  # Manual mode switch for testing
                    self.bunny.switch_mode()
                elif event.key == pygame.K_i:  # Toggle inventory view
                    self.bunny.inventory.toggle_inventory_view()
            # inside your scene's update or event handler
                elif event.key == pygame.K_SPACE:  # Assuming E is your interaction key
                    self.bunny.can_interact_with(self.interactables, self)



    def draw_text(self, text, font_size, color, position):
        """Helper method to draw text"""
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def render_farm(self):
        """Render farm mode"""
        self.farm.draw(self.screen, self.camera_x, self.camera_y)
        self.farm_portal.draw(self.screen, self.camera_x, self.camera_y)

    def render_maze(self):
        """Render maze mode"""
        self.maze.draw(self.screen, self.camera_x, self.camera_y)
        self.maze_enterportal.draw(self.screen, self.camera_x, self.camera_y)
        self.maze_exitportal.draw(self.screen, self.camera_x, self.camera_y)
        
        # Win condition check
        if int(self.bunny.x) == self.exit[0] and int(self.bunny.y) == self.exit[1]:
            self.game_over = True
            self.draw_text("You Win!", 55, Config.get('green'),
                          (Config.get('wx') // 2 - 70, Config.get('wy') // 2 - 30))

    def teleport_bunny(self, world):
        if world == 'maze' and self.bunny.can_move_to(1, 1, world):
            self.bunny.x = self.bunny.target_x = 1
            self.bunny.y = self.bunny.target_y = 1
            self.update_camera(instant=True)
            return True
        if world == 'farm' and self.bunny.can_move_to(self.farm.width - 2, self.farm.height - 2, world):
            self.bunny.x = self.bunny.target_x = self.farm.width - 2
            self.bunny.y = self.bunny.target_y = self.farm.height - 2
            self.update_camera(instant=True)
            return True


    def render(self):
        """Main render method"""
        self.screen.fill(Config.get('black'))
        
        if self.bunny.mode == 'farm':
            self.render_farm()
        else:
            self.render_maze()
        
        self.render_ui()
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    Game().run()