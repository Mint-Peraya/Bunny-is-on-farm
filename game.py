import pygame
import csv
from config import *
from maze import Maze
from bunny import Bunny
from farm import *
from object import *
from dungeon import Dungeon 


class Game:
    def __init__(self):
        self.start_time = None
        self.previous_exit = None
        self.has_warped = False
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.interact_font = pygame.font.Font(Config.get('font'), 24)
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.reset_game()
        self.bunny = Bunny(1, 1, mode='farm')  # Create the bunny object
        self.dungeon = Dungeon(30, 30, self.bunny)  # Pass the bunny into Dungeon

    def warp_to_dungeon(self):
        """Transition to dungeon mode"""
        self.fade_transition()
        self.bunny.mode = 'dungeon'
        self.dungeon_start_time = pygame.time.get_ticks()  # Start timer for dungeon mode
        self.has_warped = True
        self.game_over = False
        self.portal_cooldown = 30  # Add cooldown to prevent immediate return
        self.update_camera(instant=True)


    def warp_to_maze(self):
        self.fade_transition()
        self.bunny.mode = 'maze'
        # Warp bunny to maze at the enter portal position
        self.bunny.x = self.maze_enterportal.tile_x
        self.bunny.y = self.maze_enterportal.tile_y
        self.bunny.target_x = self.bunny.x
        self.bunny.target_y = self.bunny.y
        self.game_over = False
        self.start_time = pygame.time.get_ticks()
        self.previous_exit = None
        self.has_warped = True
        self.update_camera(instant=True)
        self.portal_cooldown = 30  # Add cooldown to prevent immediate return

    def warp_to_farm(self):
        self.fade_transition()
        self.bunny.mode = 'farm'
        # Use target_pos from whichever portal was used
        source = self.maze_enterportal if self.bunny.x == self.maze_enterportal.tile_x else self.maze_exitportal
        self.teleport_bunny(self.farm, source.target_pos)
        self.game_over = False
        self.has_warped = True  # Mark that the bunny has warped

    def render_maze(self):
        """Render maze mode"""
        self.maze.draw(self.screen, self.camera_x, self.camera_y)
        self.maze_enterportal.draw(self.screen, self.camera_x, self.camera_y)
        self.maze_exitportal.draw(self.screen, self.camera_x, self.camera_y)

        # Only check for exit if not just warped
        if not self.has_warped and int(self.bunny.x) == self.exit[0] and int(self.bunny.y) == self.exit[1]:
            print(f"Bunny reached the exit!")
            self.game_over = True
            self.success = True
            self.previous_exit = (self.exit[0], self.exit[1])
            self.exit = self.maze.get_random_exit()
            
            # Log the result
            end_time = pygame.time.get_ticks()
            time_taken = (end_time - self.start_time) / 1000
            self.log_to_csv(time_taken, self.success)
        

    def init_portals(self):
        self.farm_portal = Portal(self.farm.width - 2, self.farm.height - 2, 'maze', (1, 1))
        self.farm.interactables.append(self.farm_portal)
        self.maze_enterportal = Portal(1, 1, 'farm', (self.farm.width - 2 , self.farm.height - 2))
        self.exit = self.maze.get_random_exit()
        self.maze_exitportal = Portal(self.exit[0], self.exit[1], 'farm', (1, 1))
        self.maze.interactables.append(self.maze_enterportal)
        self.maze.interactables.append(self.maze_exitportal)

    def reset_game(self):
        self.farm = Farm(50, 30)  # No need to pass game instance
        self.bunny = Bunny(1, 1, mode='farm')
        self.init_portals()
        self.camera_x, self.camera_y = 0, 0
        self.game_over = False
        self.portal_cooldown = 0
        self.dungeon = Dungeon(30, 30, self.bunny)  # Reinitialize dungeon

    def handle_interactions(self):
        """Handle all interaction logic"""
        front_x, front_y = self.bunny.get_front_position()
        world = self.maze if self.bunny.mode == 'maze' else self.farm
        
        # Check for tile interactions in farm mode
        if self.bunny.mode == 'farm' and 0 <= front_x < self.farm.width and 0 <= front_y < self.farm.height:
            tile = self.farm.tiles[front_y][front_x]
            if tile.type == 'tree':
                self.bunny.start_action('cut', tile)
            elif tile.type == 'stone':
                self.bunny.start_action('mine', tile)
            elif tile.type == 'dirt':
                if not tile.dug:
                    self.bunny.start_action('dig', tile)
                elif tile.dug and tile.plant is None and self.bunny.held_item == 'seed':
                    if self.bunny.inventory.items["seed"] > 0:
                        stages = [Config.get('red'),Config.get('green'),Config.get('blue')]
                        tile.plant = Plant(stages)
                        self.bunny.inventory.items["seed"] -= 1
                        self.bunny.inventory.show_notification("Planted a seed!", (0, 255, 0))
                elif tile.dug and self.bunny.held_item != 'seed':
                    tile.water()
                    self.bunny.inventory.show_notification("Watered!", (100, 200, 255))

        
        # Check for portal interactions
        portals = [self.farm_portal] if self.bunny.mode == 'farm' else [self.maze_enterportal, self.maze_exitportal]
        for portal in portals:
            if portal.check_collision(self.bunny) and self.portal_cooldown <= 0:
                portal.teleport(self)
                self.portal_cooldown = 50000
                break

    def fade_transition(self):
        fade_surface = pygame.Surface(Config.get('window'))
        fade_surface.fill((0, 0, 0))
        for alpha in range(0, 255, 25):
            fade_surface.set_alpha(alpha)
            self.render()  # Draw the current frame
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(30)

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
                elif event.key == pygame.K_d:  # Example: switch to dungeon mode when pressing 'D'
                    self.warp_to_dungeon()  # Call the dungeon transition method

            # inside your scene's update or event handler
                elif event.key == pygame.K_SPACE:  # Assuming E is your interaction key
                    if self.bunny.mode == 'farm':
                        self.bunny.can_interact_with(self.farm.interactables, self)
                    elif self.bunny.mode =='maze':
                        self.bunny.can_interact_with(self.maze.interactables, self)

                elif pygame.K_1 <= event.key <= pygame.K_5:
                    index = event.key - pygame.K_1
                    item_list = list(self.bunny.inventory.items.keys())
                    if index < len(item_list):
                        self.bunny.held_item = item_list[index]
                        self.bunny.inventory.show_notification(f"Holding: {self.bunny.held_item}", (255, 255, 100))


    def draw_text(self, text, font_size, color, position):
        """Helper method to draw text"""
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def render_farm(self):
        """Render farm mode"""
        self.farm.draw(self.screen, self.camera_x, self.camera_y)
        self.farm_portal.draw(self.screen, self.camera_x, self.camera_y)

    def log_to_csv(self, time_taken, success):
        """Log game results (time, success/failure) into CSV file"""
        print(f"Logging to CSV: Time taken = {time_taken}, Success = {success}")  # Debugging line
        with open('maze_log.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([time_taken, success])

    def teleport_bunny(self, world, target_pos):
        tx, ty = target_pos
        if self.bunny.can_move_to(tx, ty, world):
            self.bunny.x = self.bunny.target_x = tx
            self.bunny.y = self.bunny.target_y = ty
            self.update_camera(instant=True)
            return True
        return False

    def render(self):
        """Main render method"""
        self.screen.fill(Config.get('black'))
        
        if self.bunny.mode == 'farm':
            self.render_farm()
        elif self.bunny.mode == 'maze':
            self.render_maze()
        elif self.bunny.mode == 'dungeon':
            self.render_dungeon()

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

    def update(self):
        """Update the game state based on current mode"""
        keys = pygame.key.get_pressed()
        
        # Determine current world based on mode
        if self.bunny.mode == 'maze':
            world = self.maze
        elif self.bunny.mode == 'farm':
            world = self.farm
        else:  # dungeon mode
            world = self.dungeon

        # Handle movement
        moving = self.bunny.move(keys, world)
        self.bunny.update_animation(moving)
        self.bunny.update_action()

        # Update world state
        if hasattr(world, 'update'):
            if self.bunny.mode == 'dungeon':
                world.update(self.bunny)
            else:
                world.update()

        # Handle interactions
        if keys[pygame.K_SPACE]:
            self.handle_interactions()

        # Update camera
        self.update_camera()

        # Update cooldowns
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1

    def render_dungeon(self):
        """Render dungeon layout and enemies"""
        self.dungeon.render(self.screen, self.camera_x, self.camera_y)

        # Check for win condition in the dungeon
        if (int(self.bunny.x) == self.dungeon.exit_x and 
            int(self.bunny.y) == self.dungeon.exit_y):
            self.game_over = True
            self.success = True
            end_time = pygame.time.get_ticks()
            time_taken = (end_time - self.dungeon_start_time) / 1000
            self.log_to_csv(time_taken, self.success)


if __name__ == "__main__":
    Game().run()
