import pygame
import csv,json,os,sys,subprocess,time
from config import *
from maze import Maze
from bunny import *
from farm import *
from dungeon import Dungeon 
from stattk import *
import tkinter as tk
from collections import defaultdict

class Game:
    def __init__(self, username='Unknown'):
        # Ensure the 'Data' directory exists
        os.makedirs('Data', exist_ok=True)
        self.ensure_data_files()

        self.start_time = None
        self.previous_exit = None
        self.has_warped = False
        self.running = True
        pygame.init()
        pygame.display.set_caption('Bunny is on farm')
        self.screen = pygame.display.set_mode(Config.get('window'))
        self.clock = pygame.time.Clock()
        self.interact_font = pygame.font.Font(Config.get('font'), 24)
        self.farm = Farm(50, 30)
        self.maze = Maze(Config.get('grid'), Config.get('grid'))
        self.mailbox = Mailbox(15, 14)  # Position near house
        self.warp_portal = Portal(self.farm.width - 3, self.farm.height - 2, 'random')
        self.farm.interactables.append(self.warp_portal)
        # Position it in a walkable area
        self.farm.tiles[self.farm.height - 2][self.farm.width - 3] = Tile('dirt', self.farm.width - 3, self.farm.height - 2)
        self.farm.interactables.append(self.mailbox)
        
        # Store username
        self.username = username
        
        self.bunny = Bunny(15, 15, mode='farm', username=username)  # Pass username to Bunny
        self.dungeon = Dungeon(30, 30,self.bunny)
        
        self.last_log_time = pygame.time.get_ticks()
        if not self.is_player_exists():
            self.handle_new_player()

        self.reset_game(load_save=True)  # Modified to load save by default
    
    def give_starter_kit(self):
        """Give new players essential starting items"""
        self.bunny.add_to_inventory("carrot_weapon")
        self.bunny.add_to_inventory("carrot_seed",5)
        self.bunny.add_to_inventory("potato_seed",5)
        # Give money separately
        self.bunny.money += 200  # Starting money

        self.bunny.inventory.show_notification("Received starter kit!", (0, 255, 0))

    def init_portals(self):
        # Farm portal (goes to random location)
        self.farm_portal = Portal(self.farm.width - 2, self.farm.height - 2)
        self.farm.interactables.append(self.farm_portal)
        
        # Only create maze exit portal (no entrance portal)
        self.exit = self.maze.get_random_exit()
        self.maze_exitportal = Portal(self.exit[0], self.exit[1], 'farm', (13, 14))  # Goes back to farm at position (13,14)
        self.maze.interactables.append(self.maze_exitportal)
        
        # Dungeon portals (unchanged)
        self.dungeon_enterportal = Portal(1, 1, 'farm', (self.farm.width - 3, self.farm.height - 2))
        self.dungeon_exitportal = Portal(self.dungeon.exit_x, self.dungeon.exit_y, 'farm', (1, 1))
        self.dungeon.interactables.append(self.dungeon_enterportal)
        self.dungeon.interactables.append(self.dungeon_exitportal)

    def warp_to_random(self):
        """Randomly warp to either maze or dungeon"""
        if random.random() < 0.5:
            self.warp_to_maze()
        else:
            self.warp_to_dungeon()

    def warp_to_dungeon(self):
        self.fade_transition()
        self.bunny.mode = 'dungeon'
        
        # Reinitialize dungeon to ensure it's properly generated
        self.dungeon = Dungeon(30, 30,self.bunny)
        
        # Set position to a known walkable spot (near entrance portal)
        self.bunny.x, self.bunny.y = 1, 1
        self.bunny.target_x, self.bunny.target_y = self.bunny.x, self.bunny.y
        
        # Force camera update
        self.update_camera(instant=True)
        self.dungeon_start_time = pygame.time.get_ticks()
        
        # Debug output
        print(f"Dungeon spawned at ({self.bunny.x}, {self.bunny.y})")
        print(f"Camera position: ({self.camera_x}, {self.camera_y})")

    def warp_to_maze(self):
        self.fade_transition()
        self.bunny.mode = 'maze'
        self.bunny.x, self.bunny.y = 1, 1  # Maze entrance position
        self.bunny.target_x, self.bunny.target_y = self.bunny.x, self.bunny.y
        self.update_camera(instant=True)
        self.start_time = pygame.time.get_ticks()  # Reset timer when entering maze
        self.game_over = False  # Reset game over state
        print("Warped to maze! Timer started.")  # Debug message

    def is_player_exists(self):
        """Check if the player's save exists"""
        try:
            with open('Data/save_game.json', 'r') as f:
                all_saves = json.load(f)
            return self.username in all_saves
        except FileNotFoundError:
            return False   

    def handle_new_player(self):
        """Handle new player setup - shown once before starting the game"""
        print(f"Welcome {self.username}! First time playing!")

        # You can display a message, intro scene, or a tutorial here
        txt1 = "Welcome, little one. I know I am not part of the family you once had, but the forest has brought you to me, and now you will rest here, where the shadows of the trees cannot reach you. "
        txt2 = "This tiny space has been a refuge for many, and it will be yours for a time. But I must leave."
        txt3 = " I have places to go. Dear bunny, you will be left in peace. I hope this new life brings you peace, though I won't be here to see your journey. "
        txt5 = "Goodbye, little one. Good luck!"

        BigScene(self.screen,self.clock,txt1,Config.get('font'),40).run()
        BigScene(self.screen,self.clock,txt2,Config.get('font'),40).run()
        BigScene(self.screen,self.clock,txt3,Config.get('font'),40).run()
        BigScene(self.screen,self.clock,txt5,Config.get('font'),40).run()
        self.give_starter_kit()
        self.save_game()    

    def warp_to_farm(self):
        """Warp the bunny back to the farm."""
        self.fade_transition()
        self.bunny.mode = 'farm'
        self.bunny.x, self.bunny.y = 13, 14
        self.bunny.target_x, self.bunny.target_y = self.bunny.x, self.bunny.y
        self.update_camera(instant=True)
        self.has_warped = True
        self.game_over = False
        self.portal_cooldown = 0  # Reset cooldown when returning to farm

    def render_maze(self):
        """Render maze mode"""
        self.maze.draw(self.screen, self.camera_x, self.camera_y)
        self.maze_exitportal.draw(self.screen, self.camera_x, self.camera_y)

        # Check time limit (600 seconds = 10 minutes)
        current_time = (pygame.time.get_ticks() - self.start_time) / 1000
        if current_time > 600:
            print("Time limit exceeded!")
            self.game_over = True
            self.success = False
            self.log_to_csv(current_time, False)
            self.warp_to_farm()
            return

        # Check for exit if not just warped
        if not self.has_warped and int(self.bunny.x) == self.exit[0] and int(self.bunny.y) == self.exit[1]:
            print(f"Bunny reached the exit!")
            self.game_over = True
            self.success = True
            end_time = pygame.time.get_ticks()
            time_taken = (end_time - self.start_time) / 1000  # Convert to seconds
            self.log_to_csv(time_taken, self.success)
            self.previous_exit = (self.exit[0], self.exit[1])
            self.exit = self.maze.get_random_exit()
            self.handle_bunny_faint()
    
    def reset_game(self, load_save=False):
        self.farm = Farm(50, 30)
        self.bunny = Bunny(15, 15, mode='farm', username=self.username)
        self.init_portals()
        self.camera_x, self.camera_y = 0, 0
        self.game_over = False
        self.portal_cooldown = 0
        self.dungeon = Dungeon(30, 30,self.bunny)
    
        if load_save:
            loaded = self.load_game()
            if not loaded:
                self.save_game()  # Auto-save for new users

    def handle_interactions(self):
        # First check mailbox interaction
        front_x, front_y = self.bunny.get_front_position()
        if (int(front_x), int(front_y)) == (self.mailbox.x, self.mailbox.y):
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                self.mailbox.interact(self)
                return
        
        # Then check portal interaction
        for obj in self.farm.interactables:
            if isinstance(obj, Portal):
                bunny_tile_x, bunny_tile_y = int(self.bunny.x), int(self.bunny.y)
                if bunny_tile_x == obj.x and bunny_tile_y == obj.y:
                    if pygame.key.get_pressed()[pygame.K_SPACE]:
                        self.handle_teleport(obj)
                        return

        # Handle other interactions based on bunny's mode
        if self.bunny.mode == 'farm' and 0 <= front_x < self.farm.width and 0 <= front_y < self.farm.height:
            tile = self.farm.tiles[front_y][front_x]      
            # Interactions for different types of tiles (tree, stone, dirt)
            if tile.type == 'tree':
                self.bunny.start_action('cut', tile)  # Start cutting the tree
            elif tile.type == 'stone':
                self.bunny.start_action('mine', tile)  # Start mining the stone
            elif tile.type == 'dirt':
                if not tile.dug:
                    self.bunny.start_action('dig', tile)  # Start digging if not dug
                elif tile.dug and tile.plant is None and self.bunny.held_item and self.bunny.held_item.endswith("_seed"):
                    # Planting a seed if the tile is dug and the bunny has a seed
                    crop_type = self.bunny.held_item.replace("_seed", "")
                    if crop_type in Config.PLANT_CONFIG and self.bunny.inventory.use_item(self.bunny.held_item):  # Check if seed can be used
                        stages = []
                        for i in range(1, Config.PLANT_CONFIG[crop_type]["stages"] + 1):
                            stage_img = Config.get('environ')[f'{crop_type}_stage{i}']
                            if stage_img:
                                stages.append(stage_img)

                        if stages:
                            tile.plant = Plant(crop_type, stages)  # Plant the seed in the tile
                            self.bunny.inventory.show_notification(f"Planted {crop_type}!", (0, 255, 0))
                elif tile.dug and tile.plant and tile.plant.harvestable:
                        # Harvest crop if the plant is ready
                        result = tile.harvest()
                        if result:
                            item, amount = result
                            self.bunny.add_to_inventory(item, amount)
                            self.bunny.inventory.show_notification(f"Harvested {amount} {item}!", (0, 255, 0))
                            tile.plant = None
                            self.log_harvest(tile.plant.crop_type, amount)
                        else:
                            print("Harvest failed")

                elif tile.dug and (not self.bunny.held_item or not self.bunny.held_item.endswith("_seed")):
                    # Water the tile if there's no seed in hand
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
        self.bunny.draw(self.screen, self.camera_x, self.camera_y)
        front_x, front_y = self.bunny.get_front_position()
        if (int(front_x), int(front_y)) == (self.mailbox.x, self.mailbox.y):
            text = "Check Mail (SPACE)" if self.mailbox.has_mail else "Open Shop (SPACE)"
            font = pygame.font.Font(Config.get('font'), 24)
            text_surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, 10))
        
        self.draw_text(f"Health: {self.bunny.health}", 35, Config.get('white'), (10, 10))
        pygame.draw.rect(self.screen, Config.get('brown'), (490, 10, 500, 30), 0, border_radius=10)
        date_text = self.farm.calendar.get_date_string()
        self.draw_text(date_text, 25, Config.get('sky'), (500, 10))

        if self.bunny.current_interactable:
            if isinstance(self.bunny.current_interactable, Tile):
                if self.bunny.current_interactable.type == 'tree':
                    text = "Chop tree (SPACE)"
                elif self.bunny.current_interactable.type == 'stone':
                    text = "Mine stone (SPACE)"
            else:
                text = "Interact (SPACE)"
            self.draw_text(text, 24, Config.get('white'), (10, 80))
        
        for portal in self.farm.interactables:
            if isinstance(portal, Portal) and portal.check_collision(self.bunny):
                text = "Enter Portal (SPACE)"
                font = pygame.font.Font(Config.get('font'), 24)
                text_surface = font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surface, (10, 10))
                break
            
        self.draw_text((f"Holding:{self.bunny.held_item}"), 25 ,Config.get('white'), (10, 80))
        self.bunny.inventory.draw(self.screen)
        moneytxt = f"Money: {self.bunny.money}"
        self.draw_text(moneytxt, 25, Config.get('white'), (10, 50))

        if self.bunny.mode == 'maze' and not self.game_over:
            # Draw timer
            current_time = (pygame.time.get_ticks() - self.start_time) / 1000
            time_left = max(0, 600 - current_time)  # Countdown from 600 seconds
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            timer_text = f"Time left: {minutes}:{seconds:02d}"
            self.draw_text(timer_text, 25, Config.get('white'), (10, 110))
            
            # Draw compass
            self.maze.draw_compass(self.screen, self.bunny, self.exit)
        
        # Draw mailbox menu if open
        self.draw_mailbox_menu()
        
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    self.warp_to_dungeon()
                elif event.key == pygame.K_m:
                    self.bunny.switch_mode()
                elif event.key == pygame.K_i:
                    self.bunny.inventory.toggle_inventory_view()
                elif event.key == pygame.K_SPACE:
                    if self.mailbox.show_sell_menu:
                        self.mailbox.show_sell_menu = True
                        self.bunny.current_interactable = None
                    else:
                        self.handle_space_press()
                elif event.key == pygame.K_p:  # Add dedicated portal key
                    self.handle_portal_interaction()
                elif event.key == pygame.K_ESCAPE:
                    if self.mailbox.show_sell_menu:
                        self.mailbox.show_sell_menu = False
                        self.bunny.current_interactable = None
                # Handle number keys 1-6 for item selection
                elif pygame.K_1 <= event.key <= pygame.K_6:
                    slot_index = event.key - pygame.K_1
                    self.bunny.select_hotbar_item(slot_index)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mailbox.show_sell_menu:
                    self.handle_mailbox_click(event.pos)
                    
            # Handle inventory management when in full view
            if self.bunny.inventory.full_view and event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_6:
                    num = event.key - pygame.K_1  # hotbar slot index
                    selected = self.bunny.inventory.swap_selected_index
                    if selected is not None:
                        if num < len(self.bunny.inventory.hotbar_indices):
                            self.bunny.inventory.hotbar_indices[num] = selected
                            self.bunny.held_item = self.bunny.inventory[num]
                            self.bunny.inventory.swap_selected_index = None

                if self.bunny.inventory.show_swap_box:
                    if event.key == pygame.K_BACKSPACE:
                        self.bunny.inventory.swap_input_text = self.bunny.inventory.swap_input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        try:
                            slot_index = int(self.bunny.inventory.swap_input_text) - 1
                            if 0 <= slot_index < 6 and self.bunny.inventory.swap_selected_index is not None:
                                self.bunny.inventory.hotbar_indices[slot_index] = self.bunny.inventory.swap_selected_index
                        except:
                            pass
                        self.bunny.inventory.swap_input_text = ""
                        self.bunny.inventory.show_swap_box = False
                        self.bunny.inventory.swap_selected_index = None
                    elif event.unicode.isdigit():
                        self.bunny.inventory.swap_input_text += event.unicode

    def handle_space_press(self):
        if self.bunny.mode == 'farm':
            front_x, front_y = self.bunny.get_front_position()
            
            # Check mailbox interaction first
            if (int(front_x), int(front_y)) == (self.mailbox.x, self.mailbox.y):
                self.handle_mailbox_interaction()
                return
                
            # Check if standing on a portal (but don't interact automatically)
            on_portal = False
            for obj in self.farm.interactables:
                if isinstance(obj, Portal) and (int(front_x), int(front_y)) == (obj.x, obj.y):
                    on_portal = True
                    break
                    
            # Only interact with non-portal objects
            if not on_portal:
                # Get tile in front of bunny
                if 0 <= front_x < self.farm.width and 0 <= front_y < self.farm.height:
                    tile = self.farm.tiles[front_y][front_x]
                    
                    # Handle tile-specific interactions
                    if tile.type == 'tree':
                        self.bunny.start_action('cut', tile)
                    elif tile.type == 'stone':
                        self.bunny.start_action('mine', tile)
                    elif tile.type == 'dirt':
                        if not tile.dug:
                            self.bunny.start_action('dig', tile)
                        elif tile.plant and tile.plant.harvestable:
                            tile.harvest()
                        elif tile.dug and not tile.plant:
                            # Water the tile if empty and dug
                            tile.water()
                            
        elif self.bunny.mode == 'maze':
            # Only interact with non-portal objects in maze
            front_x, front_y = self.bunny.get_front_position()
            for obj in self.maze.interactables:
                if not isinstance(obj, Portal) and (int(front_x), int(front_y)) == (obj.x, obj.y):
                    obj.interact(self)
                    
        elif self.bunny.mode == 'dungeon':
            self.bunny.throw_carrot()

    def handle_portal_interaction(self):
        """Explicitly handle portal interaction when a specific key is pressed (like 'P')"""
        if self.bunny.mode == 'farm':
            front_x, front_y = self.bunny.get_front_position()
            for obj in self.farm.interactables:
                if isinstance(obj, Portal) and (int(front_x), int(front_y)) == (obj.x, obj.y):
                    self.handle_teleport(obj)
                    return
        
    def ensure_data_files(self):
        """Ensure all data files exist with proper headers"""
        data_files = [
            ('Data/maze_log.csv', ["time_taken(s)", "Success_status"]),
            ('Data/bunny_positions.csv', ["x", "y"]),
            ('Data/combat_accuracy.csv', ["Hit"]),
            ('Data/inventory_usage.csv', ["item_name"]),
            ('Data/Crop.csv', ["Week", "Season", "Crop", "Amount"])
        ]
        
        for file_path, headers in data_files:
            try:
                os.makedirs('Data', exist_ok=True)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
            except Exception as e:
                print(f"Error creating data file {file_path}: {e}")

    def draw_text(self, text, font_size, color, position):
        """Helper method to draw text"""
        font = pygame.font.Font(Config.get('font'), font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def render_farm(self):
        """Render farm mode"""
        self.farm.draw(self.screen, self.camera_x, self.camera_y)
        self.farm_portal.draw(self.screen, self.camera_x, self.camera_y)
        self.mailbox.draw(self.screen, self.camera_x, self.camera_y)

    def log_to_csv(self, time_taken, success):
        """Log game results to maze_log.csv"""
        try:
            os.makedirs('Data', exist_ok=True)
            file_path = 'Data/maze_log.csv'

            write_header = not os.path.exists(file_path)

            with open(file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                if write_header:
                    writer.writerow(["timestamp", "username", "time_taken", "result"])

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                result = "win" if success else "lose"
                if result == 'win':
                    result == True
                elif result == 'lose':
                    result == False
                writer.writerow([ time_taken, result])

            print(f"Logged {result} for {self.username}.")
        except Exception as e:
            print(f"Error logging maze data: {e}")

            if success:
                # Add rewards to mailbox
                rewards = []
                if self.bunny.mode == 'maze':
                    rewards.append(('diamond', 5))
                    rewards.append(('carrot', 3))
                    rewards.append(('stone', 5))
    
                self.mailbox.add_mail(rewards)
                self.bunny.inventory.show_notification("Rewards waiting at mailbox!", (200, 200, 0))

    def send_seeds(self):
        """Send seeds every Saturday"""
        self.bunny.add_to_inventory("carrot_seed", 5)
        self.bunny.add_to_inventory("potato_seed", 5)
        self.bunny.add_to_inventory("radish_seed", 5)
        self.bunny.add_to_inventory("spinach_seed", 5)
        self.bunny.add_to_inventory("turnip_seed", 5)
        self.bunny.inventory.show_notification("Seeds sent!", (0, 255, 0))
        
    def teleport_bunny(self, world, target_pos):
        tx, ty = target_pos
        print(f"Attempting to teleport to ({tx}, {ty})")  # Debugging line
        if self.bunny.can_move_to(tx, ty, world):
            self.bunny.x = self.bunny.target_x = tx
            self.bunny.y = self.bunny.target_y = ty
            self.update_camera(instant=True)
            return True
        return False

    def handle_mailbox_interaction(self):
        if not self.mailbox.show_sell_menu:
            if self.mailbox.check_mail(self.bunny):
                self.bunny.inventory.show_notification("Collected rewards!", (0, 255, 0))
            else:
                self.mailbox.show_sell_menu = True
                self.bunny.current_interactable = self.mailbox

    def handle_mailbox_click(self, pos):
        if not self.mailbox.show_sell_menu:
            return False
        
        menu_width = 300
        menu_height = 400
        menu_x = (self.screen.get_width() - menu_width) // 2
        menu_y = (self.screen.get_height() - menu_height) // 2
        
        # Create a rect for the entire menu
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # If click is outside menu, close it
        if not menu_rect.collidepoint(pos):
            self.mailbox.show_sell_menu = False
            self.bunny.current_interactable = None
            return True
        
        # Check close button
        close_rect = pygame.Rect(menu_x + menu_width - 40, menu_y + 10, 30, 30)
        if close_rect.collidepoint(pos):
            self.mailbox.show_sell_menu = False
            self.bunny.current_interactable = None
            return True
        
        # Check crop selection
        y_offset = 70
        for crop in self.mailbox.crop_prices:
            rect = pygame.Rect(menu_x + 20, menu_y + y_offset, menu_width - 40, 40)
            if rect.collidepoint(pos):
                self.mailbox.selected_crop = crop
                return True
            y_offset += 50
        
        # Check sell button
        if self.mailbox.selected_crop:
            sell_rect = pygame.Rect(menu_x + 20, menu_y + menu_height - 60, menu_width - 40, 40)
            if sell_rect.collidepoint(pos):
                self.sell_crop()
                return True
        
        return False

    def sell_crop(self):
        if self.mailbox.selected_crop in self.bunny.inventory.items and self.bunny.inventory.items[self.mailbox.selected_crop] > 0:
            quantity = self.bunny.inventory.items[self.mailbox.selected_crop]
            total = quantity * self.mailbox.crop_prices[self.mailbox.selected_crop]
            self.bunny.money += total
            self.bunny.inventory.items[self.mailbox.selected_crop] = 0
            self.bunny.inventory.show_notification(f"Sold {quantity} {self.mailbox.selected_crop} for ${total}!", (0, 255, 0))
            
            # Log the sale
            self.log_sale(self.mailbox.selected_crop, quantity, total)
        else:
            self.bunny.inventory.show_notification(f"No {self.mailbox.selected_crop} to sell!", (255, 0, 0))
        
        self.mailbox.show_sell_menu = False
        self.mailbox.selected_crop = None

    def draw_mailbox_menu(self):
        if not self.mailbox.show_sell_menu:
            return
        
        menu_width = 300
        menu_height = 400
        menu_x = (self.screen.get_width() - menu_width) // 2
        menu_y = (self.screen.get_height() - menu_height) // 2
        
        # Main menu background
        pygame.draw.rect(self.screen, (50, 50, 50), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height), 2)
        
        font = pygame.font.Font(None, 30)
        title = font.render("Sell Crops", True, (255, 255, 255))
        self.screen.blit(title, (menu_x + 20, menu_y + 20))
        
        # Draw crop list
        y_offset = 70
        for crop, price in self.mailbox.crop_prices.items():
            rect = pygame.Rect(menu_x + 20, menu_y + y_offset, menu_width - 40, 40)
            color = (100, 100, 100) if self.mailbox.selected_crop == crop else (70, 70, 70)
            pygame.draw.rect(self.screen, color, rect)
            
            crop_text = font.render(f"{crop.capitalize()} - ${price}", True, (255, 255, 255))
            self.screen.blit(crop_text, (rect.x + 10, rect.y + 10))
            
            if rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (150, 150, 150), rect, 2)
            
            y_offset += 50
        
        # Draw sell button if crop selected
        if self.mailbox.selected_crop:
            sell_rect = pygame.Rect(menu_x + 20, menu_y + menu_height - 60, menu_width - 40, 40)
            pygame.draw.rect(self.screen, (0, 150, 0), sell_rect)
            sell_text = font.render(f"Sell {self.mailbox.selected_crop}", True, (255, 255, 255))
            self.screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 10))
        
        # Close button
        close_rect = pygame.Rect(menu_x + menu_width - 40, menu_y + 10, 30, 30)
        pygame.draw.rect(self.screen, (200, 0, 0), close_rect)
        close_text = font.render("X", True, (255, 255, 255))
        self.screen.blit(close_text, (close_rect.x + 10, close_rect.y + 5))

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

    def check_collision(self, proj, enemy):
        """Check if a projectile collides with an enemy."""
        proj_rect = pygame.Rect(proj['x'] * Config.get('bun_size'), proj['y'] * Config.get('bun_size'),
                                Config.get('bun_size') // 2, Config.get('bun_size') // 2)
        return proj_rect.colliderect(enemy.rect)
    
    def update(self):
        """Update the game state based on current mode"""
        keys = pygame.key.get_pressed()
                # Check if 10 seconds have passed since the last log
            # Check if it's Saturday
        if self.farm.calendar.current_day_name == "Sat":
            self.send_seeds()

        current_time = pygame.time.get_ticks()
        if current_time - self.last_log_time >= 5000:  # 1 seconds = 5000 ms
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
        
        # Update portals
        for portal in self.farm.interactables:
            if isinstance(portal, Portal):
                portal.update()
    
        # Handle interactions
        if keys[pygame.K_SPACE]:
            self.handle_interactions()

        if keys[pygame.K_SPACE] and self.bunny.mode == 'dungeon':
            self.bunny.throw_carrot()
        
        if self.bunny.mode == 'dungeon':
            # Update projectiles
            self.bunny.update_projectiles(self.dungeon.enemies, self.dungeon)
            
            # Check for collisions between projectiles and enemies
            for proj in self.bunny.carrot_weapon['projectiles'][:]:
                proj_rect = pygame.Rect(
                    proj['x'] * Config.get('bun_size'),
                    proj['y'] * Config.get('bun_size'),
                    Config.get('bun_size') // 2,
                    Config.get('bun_size') // 2
                )
                
                for enemy in self.dungeon.enemies[:]:
                    if proj_rect.colliderect(enemy.rect):
                        enemy.take_damage(self.bunny.carrot_weapon['damage'])
                        if proj in self.bunny.carrot_weapon['projectiles']:
                            self.bunny.carrot_weapon['projectiles'].remove(proj)
                        break
        # Update camera
        self.update_camera()

        # Update cooldowns
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
        
        # Fainting check
        if self.bunny.health <= 0:
            self.handle_bunny_faint()
            return  # Skip rest of update loop this frame
        
        if (self.farm.calendar.current_date and self.farm.calendar.current_year) == 1 and self.farm.calendar.current_season == 'Spring':
            txt = 'Dear Little Bunny,I hope this letter finds you well and safe.'
            txt1 = 'To help you on your journey,I send you some seeds.'
            txtf = 'Take good care of yourself, and always remember that you are never alone.'
            BigScene(self.screen,self.clock,txt,Config.get('font'),40)
            BigScene(self.screen,self.clock,txt1,Config.get('font'),40)
            BigScene(self.screen,self.clock,txtf,Config.get('font'),40)
            pass

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
        font = pygame.font.Font(Config.get('font'), 40)
        text = font.render("Home is the best place to sleep", True, (255, 255, 255))
        rect = text.get_rect(center=(Config.get('window')[0]//2, Config.get('window')[1]//2))
        sleep_overlay.blit(text, rect)
        self.screen.blit(sleep_overlay, (0, 0))
        pygame.display.flip()
        pygame.time.wait(2000)  # sleep effect 2 sec
        self.farm.calendar.advance_day()

        self.save_game()
        self.farm.regenerate_resources()

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
            "type": tile.plant.crop_type if tile.plant else None,
            "stage": tile.plant.stage if tile.plant else None,
            "harvestable": tile.plant.harvestable if tile.plant else False,
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
                    
                    self.farm.calendar.current_date = save_data.get("Day", 1)

                    # Restore current_day from name
                    day_name = save_data.get("Date", "Mon")
                    if day_name in self.farm.calendar.days_of_week:
                        self.farm.calendar.current_day = self.farm.calendar.days_of_week.index(day_name)

                    #  Restore current_season_index using saved name
                    season_name = save_data.get("Season", "Spring")
                    if season_name in self.farm.calendar.seasons:
                        self.farm.calendar.current_season_index = self.farm.calendar.seasons.index(season_name)

                    # ✅ This one is safe
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
                                    tile.plant.harvestable = crop_data.get("harvestable", False)
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
        """Handle the bunny fainting in any game mode"""
        # Log failure if in maze/dungeon
        if self.bunny.mode == 'maze':
            end_time = pygame.time.get_ticks()
            time_taken = (end_time - self.start_time) / 1000
            self.log_to_csv(time_taken, False)  # Log as failure
        
        # Create faint overlay
        faint_overlay = pygame.Surface(Config.get('window'), pygame.SRCALPHA)
        faint_overlay.fill((0, 0, 0, 200))  # Semi-transparent black
        
        # Set up text
        font = pygame.font.Font(None, 60)
        if self.bunny.mode == 'maze':
            text = "You failed the maze and were rescued..."
        else:
            text = "You passed out and were rescued..."
        
        # Render text
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(Config.get('window')[0]//2, Config.get('window')[1]//2))
        
        # Draw everything
        self.screen.blit(faint_overlay, (0, 0))
        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        
        # Wait before continuing
        pygame.time.wait(2500)  # Wait 2.5 seconds

        # Reset bunny position
        self.bunny.mode = 'farm'
        self.bunny.x, self.bunny.y = 13, 14
        self.bunny.target_x, self.bunny.target_y = 13, 14
        self.bunny.health = 100

        # Advance to next day
        self.farm.calendar.advance_day()
        self.update_camera(instant=True)
        self.save_game()

    def log_harvest(self, crop_type, amount):
        """Log harvested crops with week and season info"""
        try:
            file_path = 'Data/Crop.csv'
            with open(file_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # Write header if file is empty
                    writer.writerow(["timestamp", "week", "season", "crop_type", "amount"])
            
                writer.writerow([
                    self.farm.calendar.current_week,
                    self.farm.calendar.current_season,
                    crop_type, 
                    amount
                ])
        except Exception as e:
            print(f"Error logging harvest: {e}")

    def log_attack(self, success):
        """Log combat accuracy"""
        try:
            file_path = 'Data/combat_accuracy.csv'
            with open(file_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # Write header if file is empty
                    writer.writerow(["timestamp", "success"])
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([int(success)])
        except Exception as e:
            print(f"Error logging attack: {e}")

    def handle_teleport(self, portal):
        """Handle portal teleportation based on portal type"""
        if portal.cooldown > 0:
            return
            
        if portal.target_world == 'random':
            self.warp_to_random()
        elif portal.target_world == 'dungeon':
            self.warp_to_dungeon()
        elif portal.target_world == 'maze':
            self.warp_to_maze()
        elif portal.target_world == 'farm':
            self.warp_to_farm()
        
        portal.cooldown = 10  # Set cooldown
        self.fade_transition()

    def harvest(self, bunny):
        if self.plant and self.plant.harvestable:
            result = self.plant.harvest()
            if result:
                item, amount = result
                bunny.add_to_inventory(item, amount)
                self.plant = None
                return True
        return False
    
if __name__ == "__main__":
    Game().run()
