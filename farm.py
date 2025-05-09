import pygame
import random
from config import Config
from object import *


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
        base_image = env_images.get(self.type, env_images['dirt'])

        # Default draw settings
        draw_width, draw_height = size, size
        offset_y = 0
        scale = 1.0

        # Custom scaling
        if self.type == 'tree':
            scale = self.tree_scale
        elif self.type == 'stone':
            scale = self.stone_scale

        draw_width = int(size * scale)
        draw_height = int(size * scale)
        offset_y = size - draw_height  # tree/stone lifted from tile base

        # Apply scaling and rotation
        image = pygame.transform.scale(base_image, (draw_width, draw_height))
        image = pygame.transform.rotate(image, self.image_rotation)

        # Draw soft shadow
        shadow = pygame.Surface((draw_width, draw_height // 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 60), shadow.get_rect())
        screen.blit(shadow, (x + (size - draw_width) // 2 + self.image_offset_x, y + size - draw_height // 4))

        # Draw the object
        screen.blit(image, (x + (size - draw_width) // 2 + self.image_offset_x, y + offset_y))

        # Soil overlay if dug
        if self.dug and self.type == 'dirt':
            soil_overlay = env_images.get('soil_overlay')
            if soil_overlay:
                soil_overlay = pygame.transform.scale(soil_overlay, (size, size))
                screen.blit(soil_overlay, (x, y))

        # Health bar
        if self.type in ('tree', 'stone') and self.health < self.max_health:
            bar_width = size - 10
            bar_height = 5
            health_percent = self.health / self.max_health
            pygame.draw.rect(screen, (255, 0, 0), (x + 5, y + 5, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (x + 5, y + 5, int(bar_width * health_percent), bar_height))

        # Water overlay
        if self.watered:
            water_overlay = pygame.Surface((size, size), pygame.SRCALPHA)
            water_overlay.fill((0, 100, 255, 60))
            screen.blit(water_overlay, (x, y))
    
    def draw(self, screen, camera_x, camera_y):
        size = Config.get('bun_size')
        x = self.tile_x * size - camera_x
        y = self.tile_y * size - camera_y

        # Draw base tile
        env_images = Config.get('environ')
        base_image = env_images.get(self.type, env_images['dirt'])
        screen.blit(pygame.transform.scale(base_image, (size, size)), (x, y))

        # Draw plant if exists
        if self.plant:
            self.plant.draw(screen, x, y, size)

        # Draw other overlays (water, etc.)
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
        


class Plant:
    def __init__(self, growth_stages, grow_time=300):
        self.growth_stages = growth_stages  # list of images or colors
        self.grow_time = grow_time  # ms per stage
        self.stage = 0
        self.planted_time = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if self.stage < len(self.growth_stages) - 1:
            if now - self.planted_time > self.grow_time:
                self.stage += 1
                self.planted_time = now

    def draw(self, screen, x, y, tile_size):
        color = self.growth_stages[self.stage]
        pygame.draw.rect(screen, color, (x, y, tile_size, tile_size))

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
            
    @property
    def current_season(self):
        return self.seasons[self.current_season_index]
        
    @property
    def current_day_name(self):
        return self.days_of_week[self.current_day]
        
    def get_date_string(self):
        return f"{self.current_day_name}, Day {self.current_date} of {self.current_season}"
    
        i