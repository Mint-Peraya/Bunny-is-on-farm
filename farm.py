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

        # Visual modifiers
        self.tree_scale = random.uniform(1.1, 1.6) if self.type == 'tree' else 1.0
        self.stone_scale = random.uniform(0.6, 0.9) if self.type == 'stone' else 1.0
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
        else:
            base_image = env_images.get(self.type, env_images['dirt'])
            screen.blit(pygame.transform.scale(base_image, (size, size)), (x, y))

        # Draw soil overlay if dug
        if self.dug and self.type == 'dirt':
            soil_overlay = env_images.get('soil_overlay')
            if soil_overlay:
                screen.blit(pygame.transform.scale(soil_overlay, (size, size)), (x, y))

        # Draw plant if exists
        if self.plant:
            self.plant.draw(screen, x, y, size)

        # Draw water overlay
        if self.watered:
            water_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            water_overlay.fill((0, 100, 255, 60))
            screen.blit(water_overlay, (x, y))


    def update(self):
        if self.watered and pygame.time.get_ticks() - self.last_watered > 10000:
            self.watered = False
 
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
        for _ in range(10):
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            self.tiles[y][x].type = 'tree'
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10
        
        # Add some stones
        for _ in range(8):
            x, y = random.randint(3, self.width-4), random.randint(3, self.height-4)
            self.tiles[y][x].type = 'stone'
            self.tiles[y][x].health = 10
            self.tiles[y][x].max_health = 10

        # Example manually placed house from (10, 16) to (10, 14)
        for x in range(10, 16):  # 6 tiles wide
            for y in range(10, 14):  # 4 tiles tall
                self.tiles[y][x] = Tile('house', x, y)


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

        import random

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
        return f"{self.current_day_name} {self.current_date}, {self.current_season}, Week {self.current_week}, Year {self.current_year}"


class Mailbox:
    def __init__(self, x, y):
        self.tile_x = x
        self.tile_y = y
        self.size = Config.get('bun_size')
        self.has_mail = False
        self.mail_items = []
        self.notification_timer = 0
        self.image = Config.get('environ').get('mailbox', pygame.Surface((32,32)))

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y

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

    def update(self):
        """Update notification timer"""
        if self.notification_timer and pygame.time.get_ticks() - self.notification_timer > 5000:
            self.notification_timer = 0

    def draw(self, screen, camera_x, camera_y):
        """Draw mailbox with notification if has mail"""
        x = self.tile_x * self.size - camera_x
        y = self.tile_y * self.size - camera_y
        
        # Draw mailbox
        screen.blit(pygame.transform.scale(self.image, (self.size, self.size)), (x, y))
        
        # Draw notification if has mail
        if self.has_mail or self.notification_timer:
            pygame.draw.circle(screen, (255, 0, 0), 
                             (x + self.size - 10, y + 10), 8)
            
            if self.notification_timer:
                font = pygame.font.Font(None, 24)
                text = font.render("New rewards!", True, (255, 255, 255))
                screen.blit(text, (x, y - 30))