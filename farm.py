import pygame
import random
from config import Config
from bunny import *


class Tile:
    def __init__(self, tile_type='dirt', x=0, y=0):
        self.type = tile_type
        self.dug = False
        self.tile_x = x
        self.tile_y = y
        self.health = 10 if tile_type in ('tree', 'stone') else 0
        self.max_health = 10 if tile_type in ('tree', 'stone') else 0
        self.interactables = []
        self.plant = None
        self.watered = False
        self.last_watered = 0
        self.tree_scale = 1.0
        self.stone_scale = random.uniform(0.3, 0.5) if self.type == 'stone' else 1.0
        self.image_rotation = random.choice([0, 0, 0, 5, -5]) if self.type in ('tree', 'stone') else 0
        self.image_offset_x = random.randint(-4, 4) if self.type in ('tree', 'stone') else 0

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y

    def water(self):
        self.watered = True
        self.last_watered = pygame.time.get_ticks()

    def dig(self):
        if self.type == 'dirt':
            self.dug = True
            return True
        return False

    def take_damage(self, amount):
        if self.type in ('tree', 'stone'):
            self.health = max(0, self.health - amount)
            return self.health <= 0
        return False

    def draw(self, screen, camera_x, camera_y):
        size = Config.get('bun_size')
        x = self.tile_x * size - camera_x
        y = self.tile_y * size - camera_y

        env_images = Config.get('environ')

        if self.type == 'house':
            pygame.draw.rect(screen, (150, 75, 0), (x, y, size, size))
        elif self.type == 'wall':
            wall_img = env_images.get('wall')
            if wall_img:
                screen.blit(pygame.transform.scale(wall_img, (size, size)), (x, y))
        else:
            # Get the base image (dirt by default)
            base_image = env_images.get('dirt')
            # Draw the base tile (dirt)
            screen.blit(pygame.transform.scale(base_image, (size, size)), (x, y))
            
            # Draw tree/stone if present (with proper transparency)
            if self.type in ('tree', 'stone'):
                overlay_img = env_images.get(self.type)
                if overlay_img:
                    # Create a temporary surface for proper alpha blending
                    temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                    scaled_img = pygame.transform.scale(
                        overlay_img, 
                        (int(size * self.tree_scale if self.type == 'tree' else size * self.stone_scale), 
                         int(size * self.tree_scale if self.type == 'tree' else size * self.stone_scale))
                    )
                    # Position the scaled image with offset
                    img_x = (size - scaled_img.get_width()) // 2 + self.image_offset_x
                    img_y = size - scaled_img.get_height()  # Align to bottom
                    temp_surface.blit(scaled_img, (img_x, img_y))
                    screen.blit(temp_surface, (x, y))

        # Draw soil overlay if dug
        if self.dug and self.type == 'dirt':
            soil_overlay = env_images.get('soil_overlay')
            if soil_overlay:
                soil_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                scaled_soil = pygame.transform.scale(soil_overlay, (size, size))
                soil_surface.blit(scaled_soil, (0, 0))
                screen.blit(soil_surface, (x, y))

        # Draw plant if exists
        if self.plant:
            self.plant.draw(screen, x, y, size)

        # Draw water overlay
        if self.watered:
            water_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            water_overlay.fill((0, 100, 255, 60))
            screen.blit(water_overlay, (x, y))


    # In farm.py, modify the Tile class's update method:
    def update(self):
        if self.watered and pygame.time.get_ticks() - self.last_watered > 10000:  # 10 seconds
            self.watered = False
            if self.plant and not self.plant.harvestable:  # Only affect growing plants
                # Return seed to inventory (you'll need access to bunny)
                seed_name = f"{self.plant.crop_type}_seed"
                if hasattr(self, 'bunny'):  # Make sure tile has bunny reference
                    self.bunny.add_to_inventory(seed_name)
                self.plant = None
                self.dug = False  # Undig the tile
 
    def harvest(self, bunny):
        if self.plant and self.plant.harvestable:
            result = self.plant.harvest()
            if result:
                item, amount = result
                bunny.add_to_inventory(item, amount)
                self.plant = None
                return True
        return False


class Farm:
    def __init__(self, width=50, height=30):
        self.width = width
        self.height = height
        self.tiles = [[Tile('dirt', x, y) for x in range(width)] for y in range(height)]
        self.interactables = []
        self.calendar = Calendar()  # Add calendar
        # In the Tile class's __init__ method, modify these lines:

        self._generate_terrain()


    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Update calendar
        prev_season = self.calendar.current_season
        self.calendar.update()
        
        if prev_season != self.calendar.current_season:
            print(f"Season changed to {self.calendar.current_season}")
        
        # Only update plants every 100ms to reduce lag
        if current_time % 100 < 16:  # About 10 times per second
            for row in self.tiles:
                for tile in row:
                    if tile.plant:
                        tile.plant.update(self.calendar.current_season)
                    tile.update()  # Update tile state (like watering)
        
    def _generate_terrain(self):
        """Generate trees, stones, and other terrain features"""

        # Add some trees 
        for _ in range(40):
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            # Create a NEW Tile instance with type 'tree' - this will apply the scaling factors
            self.tiles[y][x] = Tile('tree', x, y)
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10
        
        # Add some stones 
        for _ in range(25): 
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            # Create a NEW Tile instance with type 'stone' - this will apply the scaling factors
            self.tiles[y][x] = Tile('stone', x, y)
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10

        # Example manually placed house from (10, 16) to (10, 14)
        for x in range(10, 16):  # 6 tiles wide
            for y in range(10, 14):  # 4 tiles tall
                self.tiles[y][x] = Tile('house', x, y)

        # Place mailbox at a clear position near house
        mailbox_x, mailbox_y = 15, 14
        self.tiles[mailbox_y][mailbox_x] = Tile('dirt', mailbox_x, mailbox_y)  # Ensure it's on dirt
        self.mailbox = Mailbox(mailbox_x, mailbox_y)
        self.interactables.append(self.mailbox)

        wall_x, wall_y = 48, 28
        self.tiles[wall_y][wall_x] = Tile('wall', wall_x, wall_y)  # Note y comes first in the indexing


    def handle_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.game.bunny.check_for_interaction(self.interactables, self.game)


    def draw(self, screen, camera_x, camera_y):
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x].draw(screen, camera_x, camera_y)
        
        # Draw interactables
        for obj in self.interactables:
            if hasattr(obj, 'draw'):
                obj.draw(screen, camera_x, camera_y)
        
        # Draw house image just once at (10,10)
        house_img = Config.get('environ').get('house')
        if house_img:
            tile_size = Config.get('bun_size')
            house_img = pygame.transform.scale(house_img, (tile_size * 10, tile_size * 8))
            screen.blit(house_img, (8 * tile_size - camera_x, 8 * tile_size - camera_y))


    def regenerate_resources(self):
        for row in self.tiles:
            for tile in row:
                if tile.type == 'dirt':  # only regenerate on dirt
                    chance = random.random()
                    if chance < 0.01:
                        tile.type = 'tree'
                        tile.health = 10
                        tile.max_health = 10
                    elif chance < 0.02:
                        tile.type = 'stone'
                        tile.health = 10
                        tile.max_health = 10
    
    def is_tile_walkable(self, x, y):
        """Check if a tile can be walked on"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        # Check tile type
        if self.tiles[y][x].type in ('tree', 'stone', 'house', 'wall'):
            return False
            
        # Check interactables
        for obj in self.interactables:
            if int(x) == getattr(obj, 'tile_x', -1) and int(y) == getattr(obj, 'tile_y', -1):
                return False
                
        return True


class Plant:
    def __init__(self, crop_type, growth_images):
        self.crop_type = crop_type
        self.config = Config.PLANT_CONFIG[crop_type]
        self.growth_images = growth_images
        self.stage = 0
        self.max_stage = self.config["stages"] - 1
        self.planted_time = pygame.time.get_ticks()
        self.harvestable = False
        
    def update(self, current_season):
        now = pygame.time.get_ticks()
        
        # Growth stops in wrong season
        if current_season not in self.config["seasons"]:
            return
            
        if self.stage < self.max_stage:
            if now - self.planted_time > self.config["grow_time"]:
                self.stage += 1
                self.planted_time = now
                if self.stage == self.max_stage:
                    self.harvestable = True
            
            if self.stage == self.max_stage:
                self.harvestable = True

    def draw(self, screen, x, y, tile_size):
        if 0 <= self.stage < len(self.growth_images):
            stage_img = self.growth_images[self.stage]
            if stage_img:  # Check if image exists
                scaled_img = pygame.transform.scale(stage_img, (tile_size, tile_size))
                screen.blit(scaled_img, (x, y))
        
    def harvest(self):
        if self.harvestable:
            self.harvestable = False
            return (self.config["harvest_item"], self.config["harvest_amount"])
        return None
    

class Calendar:
    def __init__(self):
        self.seasons = ["Spring", "Summer", "Fall", "Winter"]
        self.days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.current_season_index = 0
        self.current_day = 0
        self.current_date = 1
        self.current_year = 1
        self.day_timer = 0
        self.day_duration = 60000  # 60 seconds per day
        self.last_update_time = pygame.time.get_ticks()
        
    def update(self):
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        self.day_timer += delta_time
        if self.day_timer >= self.day_duration:
            self.day_timer = 0
            self.advance_day()
            
    def advance_day(self):
        self.current_day = (self.current_day + 1) % 7
        self.current_date += 1
        if self.current_date > 28:
            self.current_date = 1
            self.current_season_index = (self.current_season_index + 1) % 4
            if self.current_season_index == 0:  # End of a season
                self.current_year += 1
            
    @property
    def current_season(self):
        return self.seasons[self.current_season_index]
        
    @property
    def current_day_name(self):
        return self.days_of_week[self.current_day]
    
    @property
    def current_week(self):
        # Calculate the current week (1-4)
        return (self.current_date - 1) // 7 + 1
        
    def get_date_string(self):
        # Return formatted string with the current day, date, season, week, and year
        return f"{self.current_day_name} {self.current_date}, {self.current_season}, Year {self.current_year}"


class Mailbox:
    def __init__(self, x, y):
        self.tile_x = x
        self.tile_y = y
        self.size = Config.get('bun_size')
        self.has_mail = False
        self.mail_items = []
        self.notification_timer = 0
        self.image = Config.get('environ').get('mailbox', pygame.Surface((32,32)))
        self.noti_img = pygame.image.load('assets/picture/noti.png').convert_alpha()
        
        # Selling properties
        self.show_sell_menu = False
        self.selected_crop = None
        self.crop_prices = {
            "carrot": 15,
            "potato": 20,
            "radish": 25,
            "spinach": 30,
            "turnip": 35
        }

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y
    
    @property
    def rect(self):
        """Return collision rectangle for the mailbox"""
        return pygame.Rect(
            self.tile_x * self.size,
            self.tile_y * self.size,
            self.size * 1.5,  # Account for larger size
            self.size * 1.5
        )

    def draw(self, screen, camera_x, camera_y):
        """Draw mailbox and notification icon"""
        x = self.tile_x * self.size - camera_x
        y = self.tile_y * self.size - camera_y
        
        # Draw larger mailbox (1.5x size)
        scaled_size = int(self.size * 1.5)
        screen.blit(pygame.transform.scale(self.image, (scaled_size, scaled_size)), 
                (x - scaled_size//4, y - scaled_size//2))
        
        # Draw notification if has mail
        if self.has_mail or self.notification_timer:
            noti_size = self.size // 2
            scaled_noti = pygame.transform.scale(self.noti_img, (noti_size, noti_size))
            screen.blit(scaled_noti, (x + scaled_size//2 - noti_size//2, y - noti_size))
            
        # Draw sell menu if open
        if self.show_sell_menu:
            self.draw_sell_menu(screen)

    def update(self):
        """Update notification timer"""
        if self.notification_timer and pygame.time.get_ticks() - self.notification_timer > 5000:
            self.notification_timer = 0

    def add_mail(self, items):
        """Add reward items to mailbox"""
        self.mail_items.extend(items)
        self.has_mail = True
        self.notification_timer = pygame.time.get_ticks()

    def check_mail(self, bunny):
        """Player collects mail items"""
        if self.has_mail:
            for item, amount in self.mail_items:
                bunny.add_to_inventory(item, amount)
            self.mail_items = []
            self.has_mail = False
            return True
        return False

    def interact(self, game):
        """Handle mailbox interaction"""
        if self.has_mail:
            if self.check_mail(game.bunny):
                game.bunny.inventory.show_notification("Collected rewards!", (0, 255, 0))
        else:
            self.show_sell_menu = True
            game.bunny.current_interactable = self

    def draw_sell_menu(self, screen):
        """Draw the crop selling interface"""
        menu_width = 300
        menu_height = 400
        menu_x = (screen.get_width() - menu_width) // 2
        menu_y = (screen.get_height() - menu_height) // 2
        
        # Main menu background
        pygame.draw.rect(screen, (50, 50, 50), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height), 2)
        
        font = pygame.font.Font(None, 30)
        title = font.render("Sell Crops", True, (255, 255, 255))
        screen.blit(title, (menu_x + 20, menu_y + 20))
        
        # Draw crop list
        y_offset = 70
        for crop, price in self.crop_prices.items():
            rect = pygame.Rect(menu_x + 20, menu_y + y_offset, menu_width - 40, 40)
            color = (100, 100, 100) if self.selected_crop == crop else (70, 70, 70)
            pygame.draw.rect(screen, color, rect)
            
            crop_text = font.render(f"{crop.capitalize()} - ${price}", True, (255, 255, 255))
            screen.blit(crop_text, (rect.x + 10, rect.y + 10))
            
            if rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, (150, 150, 150), rect, 2)
            
            y_offset += 50
        
        # Draw sell button if crop selected
        if self.selected_crop:
            sell_rect = pygame.Rect(menu_x + 20, menu_y + menu_height - 60, menu_width - 40, 40)
            pygame.draw.rect(screen, (0, 150, 0), sell_rect)
            sell_text = font.render(f"Sell {self.selected_crop}", True, (255, 255, 255))
            screen.blit(sell_text, (sell_rect.x + 10, sell_rect.y + 10))
        
        # Close button
        close_rect = pygame.Rect(menu_x + menu_width - 40, menu_y + 10, 30, 30)
        pygame.draw.rect(screen, (200, 0, 0), close_rect)
        close_text = font.render("X", True, (255, 255, 255))
        screen.blit(close_text, (close_rect.x + 10, close_rect.y + 5))

    def handle_click(self, pos, game):
        """Handle clicks in sell menu"""
        if not self.show_sell_menu:
            return False
        
        menu_width = 300
        menu_height = 400
        menu_x = (game.screen.get_width() - menu_width) // 2
        menu_y = (game.screen.get_height() - menu_height) // 2
        
        # Create a rect for the entire menu
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # If click is outside menu, close it
        if not menu_rect.collidepoint(pos):
            self.show_sell_menu = False
            self.selected_crop = None
            game.bunny.current_interactable = None
            return True
        
        # Check close button
        close_rect = pygame.Rect(menu_x + menu_width - 40, menu_y + 10, 30, 30)
        if close_rect.collidepoint(pos):
            self.show_sell_menu = False
            self.selected_crop = None
            game.bunny.current_interactable = None
            return True
        
        # Check crop selection
        y_offset = 70
        for crop in self.crop_prices:
            rect = pygame.Rect(menu_x + 20, menu_y + y_offset, menu_width - 40, 40)
            if rect.collidepoint(pos):
                self.selected_crop = crop
                return True
            y_offset += 50
        
        # Check sell button
        if self.selected_crop:
            sell_rect = pygame.Rect(menu_x + 20, menu_y + menu_height - 60, menu_width - 40, 40)
            if sell_rect.collidepoint(pos):
                self.sell_crop(game.bunny)
                return True
        
        return False

    def sell_crop(self, bunny):
        """Sell all of a specific crop"""
        if self.selected_crop in bunny.inventory.items and bunny.inventory.items[self.selected_crop] > 0:
            quantity = bunny.inventory.items[self.selected_crop]
            total = quantity * self.crop_prices[self.selected_crop]
            bunny.money += total
            bunny.inventory.items[self.selected_crop] = 0
            bunny.inventory.show_notification(f"Sold {quantity} {self.selected_crop} for ${total}!", (0, 255, 0))
        else:
            bunny.inventory.show_notification(f"No {self.selected_crop} to sell!", (255, 0, 0))
        
        self.show_sell_menu = False
        self.selected_crop = None
    # In farm.py, add to Mailbox class:
    def draw_interaction(self, screen):
        """Draw interaction prompt"""
        if self.has_mail:
            text = "Check Mail (SPACE)"
        else:
            text = "Open Shop (SPACE)"
        
        font = pygame.font.Font(Config.get('font'), 24)
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10))
        