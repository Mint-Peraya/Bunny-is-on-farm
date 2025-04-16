import pygame
import math
from config import *
from maze import Maze
from bunny import Bunny
from try2 import *

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
        self.maze_enterportal = Portal(1, 1, 'farm', (1, 1))
        self.exit = self.maze.get_random_exit()
        self.maze_exitportal = Portal(self.exit[0], self.exit[1], 'farm', (1, 1))


    def reset_game(self):
        self.farm = Farm(50, 30)
        self.bunny = Bunny(1, 1, mode='farm')
        self.init_portals()

        self.camera_x, self.camera_y = 0, 0
        self.game_over = False

    def update(self):
        keys = pygame.key.get_pressed()
        world = self.maze if self.bunny.mode == 'maze' else self.farm
        
        # Check for nearby interactables
        self.bunny.current_interactable = None
        # First: Check for nearby resources
        if self.bunny.mode == 'farm':
            tile_x, tile_y = int(self.bunny.x), int(self.bunny.y)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    check_x, check_y = tile_x + dx, tile_y + dy
                    if (0 <= check_x < self.farm.width and 
                        0 <= check_y < self.farm.height):
                        tile = self.farm.tiles[check_y][check_x]
                        if tile.type in ('tree', 'stone') and self.bunny.can_interact_with(tile):
                            self.bunny.current_interactable = tile
                            if keys[pygame.K_SPACE]:
                                self.handle_resource_interaction(check_x, check_y)
                            break  # Prioritize first resource found

        # Then: Check for portals
        portals = [self.farm_portal] if self.bunny.mode == 'farm' else [self.maze_enterportal, self.maze_exitportal]

        for portal in portals:
            if self.bunny.can_interact_with(portal):
                # Only override if nothing else to interact with
                if self.bunny.current_interactable is None:
                    self.bunny.current_interactable = portal
                if keys[pygame.K_SPACE]:
                    portal.teleport(self)
                    self.portal_cooldown = 30

        moving = self.bunny.move(keys, world)
        self.bunny.update_animation(moving)
        self.update_camera()  # ✅ Always follow bunny!

        tile_x, tile_y = round(self.bunny.x), round(self.bunny.y)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                check_x, check_y = tile_x + dx, tile_y + dy
                if (0 <= check_x < self.farm.width and 0 <= check_y < self.farm.height):
                    tile = self.farm.tiles[check_y][check_x]
                    if tile.type in ('tree', 'stone'):
                        print(f"✅ Found {tile.type} at {check_x},{check_y}")
                        self.bunny.current_interactable = tile
                        if keys[pygame.K_SPACE]:
                            self.handle_resource_interaction(check_x, check_y)
                        break


    def handle_resource_interaction(self, x, y):
        """Handle gathering resources from farm tiles"""
        tile = self.farm.tiles[y][x]
        if tile.type == 'tree':
            self.bunny.add_to_inventory('wood')
            self.farm.tiles[y][x] = Tile('dirt')  # Remove the tree
        elif tile.type == 'stone':
            self.bunny.add_to_inventory('stone')
            self.farm.tiles[y][x] = Tile('dirt')  # Remove the stone
    
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
        """Transition from farm to maze (from portal at bottom right)"""
        self.fade_transition()
        self.bunny.mode = 'maze'
        # Try to land one tile below the entry portal at (1,1)
        self.teleport_bunny(preferred_x=1, preferred_y=2, world=self.maze)
        self.game_over = False


    def warp_to_farm(self):
        self.fade_transition()
        """Transition from maze to farm (return near bottom-right portal)"""
        self.bunny.mode = 'farm'
        tx, ty = self.farm_portal.tile_x, self.farm_portal.tile_y - 1  # Try just above the portal
        self.teleport_bunny(preferred_x=tx, preferred_y=ty, world=self.farm)
        self.game_over = False


    def render_ui(self):
        """Render UI elements common to both modes"""
        # Draw bunny in both modes
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

    def draw_text(self, text, font_size, color, position):
        """Helper method to draw text"""
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def render_farm(self):
        """Render farm mode"""
        self.farm.draw(self.screen, self.camera_x, self.camera_y)
        self.farm_portal.draw(self.screen, self.camera_x, self.camera_y)
        
        # Farm-specific controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.farm.dig_tile_at(int(self.bunny.x), int(self.bunny.y))

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

    def teleport_bunny(self, preferred_x, preferred_y, world):
        """Warp bunny to a nearby safe tile, skipping out-of-bound or blocked tiles."""
        # Determine world bounds
        max_x = world.width if hasattr(world, 'width') else Config.get('grid')
        max_y = world.height if hasattr(world, 'height') else Config.get('grid')

        candidate_offsets = [
            (0, 0), (1, 0), (0, 1), (-1, 0), (0, -1),
            (1, 1), (-1, -1), (1, -1), (-1, 1)
        ]

        for dx, dy in candidate_offsets:
            tx = preferred_x + dx
            ty = preferred_y + dy

            # 🔒 Safe bounds check first
            if 0 <= tx < max_x and 0 <= ty < max_y:
                if self.bunny.can_move_to(tx, ty, world):
                    self.bunny.x = self.bunny.target_x = tx
                    self.bunny.y = self.bunny.target_y = ty
                    self.update_camera(instant=True)
                    return True

        print(f"⚠️ No walkable tiles near ({preferred_x}, {preferred_y})")
        return False


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