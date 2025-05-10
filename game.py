import pygame
import csv
import json
from config import *
from maze import Maze
from bunny import *
from farm import *
from dungeon import Dungeon 
from stattk import *
import tkinter as tk
import subprocess
import sys
import os


class Game:
    def __init__(self, username='Unknown'):
        self.start_time = None
        self.previous_exit = None
        self.has_warped = False
        self.running = True
        pygame.init()
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.interact_font = pygame.font.Font(Config.get('font'), 24)
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        
        # Store username
        self.username = username
        
        # Load saved game or initialize new game
        self.reset_game(load_save=True)  # Modified to load save by default
        
        self.bunny = Bunny(10, 10, mode='farm', username=username)  # Pass username to Bunny
        self.dungeon = Dungeon(30, 30, self.bunny)
        
        self.last_log_time = pygame.time.get_ticks()

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

    def reset_game(self, load_save=False):
        self.farm = Farm(50, 30)
        self.bunny = Bunny(1, 1, mode='farm', username=self.username)
        self.init_portals()
        self.camera_x, self.camera_y = 0, 0
        self.game_over = False
        self.portal_cooldown = 0
        self.dungeon = Dungeon(30, 30, self.bunny)
    
        if load_save:
            loaded = self.load_game()
            if not loaded:
                self.save_game()  # Auto-save for new users


    def handle_interactions(self):
        front_x, front_y = self.bunny.get_front_position()
        world = self.maze if self.bunny.mode == 'maze' else self.farm
        
        if self.bunny.mode == 'farm' and 0 <= front_x < self.farm.width and 0 <= front_y < self.farm.height:
            tile = self.farm.tiles[front_y][front_x]
            
            if tile.type == 'tree':
                self.bunny.start_action('cut', tile)
            elif tile.type == 'stone':
                self.bunny.start_action('mine', tile)
            elif tile.type == 'dirt':
                if not tile.dug:
                    self.bunny.start_action('dig', tile)
                elif tile.dug and tile.plant is None and self.bunny.held_item and self.bunny.held_item.endswith("_seed"):
                    crop_type = self.bunny.held_item.replace("_seed", "")
                    if crop_type in Config.PLANT_CONFIG and self.bunny.inventory.items.get(self.bunny.held_item, 0) > 0:
                        # Get all stages for this crop
                        stages = []
                        for i in range(1, Config.PLANT_CONFIG[crop_type]["stages"] + 1):
                            stage_img = Config.get('environ')[f'{crop_type}_stage{i}']
                            if stage_img:
                                stages.append(stage_img)
                        
                        if stages:  # Only plant if we have all required stages
                            tile.plant = Plant(crop_type, stages)
                            self.bunny.inventory.items[self.bunny.held_item] -= 1
                            self.bunny.inventory.show_notification(f"Planted {crop_type}!", (0, 255, 0))
                elif tile.dug and tile.plant and tile.plant.harvestable:
                    self.bunny.harvest_crop(self.farm)
                elif tile.dug and (not self.bunny.held_item or not self.bunny.held_item.endswith("_seed")):
                    tile.water()
                    self.bunny.inventory.show_notification("Watered!", (100, 200, 255))


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
        
        # Draw Health
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))
        
        # Draw day
        pygame.draw.rect(self.screen, Config.get('brown'), (490, 10, 500, 30), 0,border_radius=10)
        date_text = self.farm.calendar.get_date_string()
        self.draw_text(date_text, 25, Config.get('sky'), (500, 10))

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

        # Draw money
        moneytxt = f"Money: {self.bunny.money}"
        self.draw_text(moneytxt, 25, Config.get('white'), (10, 50))
        

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
        with open('Data/maze_log.csv', mode='a', newline='') as file:
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

    def update(self):
        """Update the game state based on current mode"""
        keys = pygame.key.get_pressed()
                # Check if 10 seconds have passed since the last log
        current_time = pygame.time.get_ticks()
        if current_time - self.last_log_time >= 5000:  # 5 seconds = 5000 ms
            self.log_bunny_position()
            self.last_log_time = current_time  # Update the time of the last log

        
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
        self.check_sleep_trigger()


        # Update world state
        if hasattr(world, 'update'):
            if self.bunny.mode == 'dungeon':
                world.update(self.bunny)
            else:
                world.update()

        # Handle interactions
        if keys[pygame.K_SPACE]:
            self.handle_interactions()

        if keys[pygame.K_SPACE] and self.bunny.mode == 'dungeon':
            self.bunny.throw_carrot()
        
        # Update projectiles
        if self.bunny.mode == 'dungeon':
            self.bunny.update_projectiles(self.dungeon.enemies, self.dungeon)

        # Update camera
        self.update_camera()

        # Update cooldowns
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
        
        # Fainting check
        if self.bunny.health <= 0:
            self.handle_bunny_faint()
            return  # Skip rest of update loop this frame


        

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
    
    def check_sleep_trigger(self):
        bx, by = int(self.bunny.x), int(self.bunny.y)
        # Door at (12, 15) which is center bottom tile of 4x6 house
        if (bx, by) == (13, 14):
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self.sleep()

    def sleep(self):
        # Show sleep screen
        sleep_overlay = pygame.Surface(Config.get('window'))
        sleep_overlay.fill((0, 0, 0))
        font = pygame.font.Font(None, 100)
        text = font.render("Sleeping...", True, (255, 255, 255))
        rect = text.get_rect(center=(Config.get('window')[0]//2, Config.get('window')[1]//2))
        sleep_overlay.blit(text, rect)
        self.screen.blit(sleep_overlay, (0, 0))
        pygame.display.flip()
        pygame.time.wait(2000)  # sleep effect 2 sec
        self.farm.calendar.advance_day()

        self.save_game()


    def save_game(self):
        """Save current user's game state into a shared JSON file for all users."""
        try:
            with open('Data/save_game.json', 'r') as f:
                all_saves = json.load(f)
        except FileNotFoundError:
            all_saves = {}


        username = self.bunny.name

        user_save = {
            "Day": self.farm.calendar.current_date,
            "Date": self.farm.calendar.current_day_name,  # e.g., "Mon", "Tue"
            "Week": self.farm.calendar.current_week,
            "Season": self.farm.calendar.current_season,
            "Year":self.farm.calendar.current_year,
            "Time": "7:00",  # Reset daily
            "Health": self.bunny.health,
            "CropStatus": [
                {
                    "x": x,
                    "y": y,
                    "type": tile.plant.type if tile.plant else None,
                    "stage": tile.plant.stage if tile.plant else None,
                    "watered": tile.watered
                }
                for y, row in enumerate(self.farm.tiles)
                for x, tile in enumerate(row)
                if tile.type == 'dirt' and (tile.dug or tile.plant)
            ],
            "Inventory": self.bunny.inventory.items,
            "Money": getattr(self.bunny, "money", 0),
            "Relationship": getattr(self.bunny, "relationships", {})
        }

        all_saves[username] = user_save

        with open('Data/save_game.json', 'w') as f:
            json.dump(all_saves, f, indent=4)

        print(f"Game saved for {username}")
    
    def load_game(self):
        """Load the user's saved game state."""
        try:
            with open('Data/save_game.json', 'r') as f:
                all_saves = json.load(f)
                
                if self.username in all_saves:
                    save_data = all_saves[self.username]
                    
                    # Load calendar data
                    self.farm.calendar.current_date = save_data.get("Day", 1)
                    self.farm.calendar.current_day_name = save_data.get("Date", "Mon")
                    self.farm.calendar.current_week = save_data.get("Week", 1)
                    self.farm.calendar.current_season = save_data.get("Season", "Spring")
                    self.farm.calendar.current_year = save_data.get("Year", 1)
                    
                    # Load bunny stats
                    self.bunny.health = 100
    
                    # Load inventory
                    self.bunny.inventory.items = defaultdict(int, save_data.get("Inventory", {}))
                    
                    # Load crops
                    for crop_data in save_data.get("CropStatus", []):
                        x, y = crop_data["x"], crop_data["y"]
                        if 0 <= x < self.farm.width and 0 <= y < self.farm.height:
                            tile = self.farm.tiles[y][x]
                            if crop_data["type"]:
                                stages = []
                                for i in range(1, Config.PLANT_CONFIG[crop_data["type"]]["stages"] + 1):
                                    stage_img = Config.get('environ')[f'{crop_data["type"]}_stage{i}']
                                    if stage_img:
                                        stages.append(stage_img)
                                
                                if stages:
                                    tile.plant = Plant(crop_data["type"], stages)
                                    tile.plant.stage = crop_data.get("stage", 0)
                                    tile.watered = crop_data.get("watered", False)
                            tile.dug = True
                    
                    print(f"Game loaded for {self.username}")
                else:
                    print(f"No save found for {self.username}, starting new game")
                    
        except FileNotFoundError:
            print("No save file found, starting new game")
        except Exception as e:
            print(f"Error loading game: {e}")

    def log_bunny_position(self):
        """Log bunny's (x, y) position to a CSV file."""
        with open('Data/bunny_positions.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([round(self.bunny.x), round(self.bunny.y)])

    def end_game(self):
        """End the game and show statistics"""
        print("Game ended. Opening StatsApp...")
        pygame.quit()
        
        # Launch stats app as separate process
        stats_script = os.path.join(os.path.dirname(__file__), 'stattk.py')
        subprocess.Popen([sys.executable, stats_script])
        sys.exit(0)

    def start_stats_app(self):
        """Start the statistics application"""
        root = tk.Tk()
        app = StatsApp(root)
        root.mainloop()

    def run(self):
        """Main game loop"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        self.end_game()
    
    def handle_bunny_faint(self):
        """Handle the bunny fainting and transition to next day at farmhouse."""
        faint_overlay = pygame.Surface(Config.get('window'))
        faint_overlay.fill((0, 0, 0))
        font = pygame.font.Font(None, 60)
        text = font.render("You passed out and were rescued...", True, (255, 255, 255))
        rect = text.get_rect(center=(Config.get('window')[0]//2, Config.get('window')[1]//2))
        faint_overlay.blit(text, rect)
        self.screen.blit(faint_overlay, (0, 0))
        pygame.display.flip()
        pygame.time.wait(2500)  # Wait 2.5 seconds

        # Set bunny position to farm house center
        self.bunny.mode = 'farm'
        self.bunny.x, self.bunny.y = 13, 14
        self.bunny.target_x, self.bunny.target_y = 13, 14
        self.bunny.health = 100

        # Advance to next day
        self.farm.calendar.advance_day()

        self.update_camera(instant=True)
        self.save_game()
    
    def log_harvest(self, crop_type, amount, file='Data/Crop.csv'):
        with open(file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self.farm.calendar.current_week, crop_type, amount])
    
    def log_attack(self, success, file='Data/accuracy_log.csv'):
        with open(file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([pygame.time.get_ticks(), int(success)])




if __name__ == "__main__":
    Game().run()
