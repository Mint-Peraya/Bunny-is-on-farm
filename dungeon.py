import pygame
import math, csv
import random
from config import *
from farm import Tile

class Dungeon:
    def __init__(self, width, height, bunny):
        self.width = width
        self.height = height
        self.bunny = bunny
        self.exit_x = width - 2
        self.exit_y = height - 2
        self.layout = self.generate_dungeon_layout()
        self.tiles = self.create_tiles()
        self.enemies = []
        self.create_rooms_and_enemies()
        self.loot_boxes = []
        self.interactables = []

    def is_tile_walkable(self, x, y):
        """Check if the tile at (x, y) is walkable (i.e., not a wall)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            # Check if the tile is empty (walkable)
            return self.layout[y][x] == '.'
        return False  # Out of bounds or a wall tile
    
    def is_valid_position(self, x, y):
        """Check if position is walkable (not a wall)"""
        grid_x, grid_y = int(x), int(y)
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            # Check all adjacent tiles to prevent getting stuck
            for dx, dy in [(0,0), (-1,0), (1,0), (0,-1), (0,1)]:
                check_x, check_y = grid_x + dx, grid_y + dy
                if 0 <= check_x < self.width and 0 <= check_y < self.height:
                    if self.layout[check_y][check_x] != '.':
                        return False
            return True
        return False


    def generate_dungeon_layout(self):
        """Generate a dungeon layout with rooms and corridors"""
        layout = [['#' for _ in range(self.width)] for _ in range(self.height)]
        
        # Create main rooms
        main_room = (10, 5, 10, 10)  # Central room
        room_1 = (3, 3, 6, 6)        # Top-left room
        room_2 = (21, 3, 6, 6)       # Top-right room
        room_3 = (3, 15, 6, 6)       # Bottom-left room
        room_4 = (21, 15, 6, 6)      # Bottom-right room
        
        self.create_room(layout, main_room)
        self.create_room(layout, room_1)
        self.create_room(layout, room_2)
        self.create_room(layout, room_3)
        self.create_room(layout, room_4)
        
        # Create corridors connecting rooms
        self.create_corridor(layout, (9, 5), (9, 3))    # Vertical to top
        self.create_corridor(layout, (9, 15), (9, 20))  # Vertical to bottom
        self.create_corridor(layout, (5, 10), (3, 10))  # Horizontal to left
        self.create_corridor(layout, (15, 10), (21, 10)) # Horizontal to right
        
        # Ensure exit is accessible
        layout[self.exit_y][self.exit_x] = '.'
        
        return layout

    def create_tiles(self):
        """Create a grid of tiles with types based on dungeon layout"""
        tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if self.layout[y][x] == '#':
                    row.append(Tile(x, y, 'stone'))  # Wall
                else:
                    row.append(Tile(x, y, 'empty'))  # Floor
            tiles.append(row)
        return tiles

    def update(self, bunny):
        """Update dungeon state including enemies"""
        for enemy in self.enemies[:]:  # Use [:] to make a copy for safe removal
            enemy.update(bunny, self)
            if enemy.health <= 0:
                if not enemy.has_dropped_loot:
                    self.handle_enemy_death(enemy)
                self.enemies.remove(enemy)
                
        for loot_box in self.loot_boxes:
            loot_box.update(bunny)

    def handle_enemy_death(self, enemy):
        """Handle loot dropping when enemy dies"""
        enemy.has_dropped_loot = True
        if isinstance(enemy, Boss):
            self.loot_boxes.append(LootBox(enemy.x, enemy.y, "boss", self.bunny))
        else:
            loot_type = "health_potion" if random.random() > 0.5 else "coins"
            self.loot_boxes.append(LootBox(enemy.x, enemy.y, loot_type, self.bunny))

    def render(self, screen, camera_x, camera_y):
        """Render the dungeon with optimized drawing"""
        wall_color = (0, 0, 0)  # Black walls
        floor_color = (50, 50, 50)  # Dark gray floors
        tile_size = Config.get('bun_size')
        
        for y in range(self.height):
            for x in range(self.width):
                pos_x = x * tile_size - camera_x
                pos_y = y * tile_size - camera_y
                
                if self.layout[y][x] == '#':
                    pygame.draw.rect(screen, wall_color, 
                                (pos_x, pos_y, tile_size, tile_size))
                else:
                    pygame.draw.rect(screen, floor_color,
                                (pos_x, pos_y, tile_size, tile_size))
        
        # Render enemies and loot boxes
        for enemy in self.enemies:
            enemy.render(screen, camera_x, camera_y)
            
        for loot_box in self.loot_boxes:
            loot_box.render(screen, camera_x, camera_y)
        
        # Render interactables (like portals)
        for obj in self.interactables:
            if hasattr(obj, 'draw'):
                obj.draw(screen, camera_x, camera_y)

    def create_room(self, layout, room):
        """Mark room area in the dungeon layout"""
        x, y, w, h = room
        for i in range(y, y + h):
            for j in range(x, x + w):
                if 0 <= i < self.height and 0 <= j < self.width:
                    layout[i][j] = '.'

    def create_corridor(self, layout, start, end):
        """Create a corridor between two points"""
        x1, y1 = start
        x2, y2 = end
        
        # Horizontal first
        step_x = 1 if x2 > x1 else -1
        for x in range(x1, x2 + step_x, step_x):
            if 0 <= x < self.width:
                layout[y1][x] = '.'
        
        # Then vertical
        step_y = 1 if y2 > y1 else -1
        for y in range(y1, y2 + step_y, step_y):
            if 0 <= y < self.height:
                layout[y][x2] = '.'

    def create_rooms_and_enemies(self):
        """Place enemies in rooms"""
        # Boss in center
        self.enemies.append(Boss(15, 10))

        # Normal enemies
        enemy_positions = [
            (5, 5), (7, 7), (24, 5), (22, 7),
            (5, 18), (7, 16), (24, 18), (22, 16)
        ]
        for x, y in enemy_positions:
            if self.layout[y][x] == '.':  # Only place in walkable areas
                self.enemies.append(Enemy(x, y, "normal"))

        # Rare enemies
        rare_positions = [(5, 7), (24, 16)]
        for x, y in rare_positions:
            if self.layout[y][x] == '.':
                self.enemies.append(Enemy(x, y, "rare"))


class Enemy:
    def __init__(self, x, y, enemy_type="normal"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.rect = pygame.Rect(
            self.x * Config.get('bun_size'), 
            self.y * Config.get('bun_size'), 
            Config.get('bun_size'), 
            Config.get('bun_size'))
        self.is_awake = False
        self.has_dropped_loot = False
        
        # Movement properties
        self.direction = random.choice(["left", "right", "up", "down"])
        self.direction_timer = random.randint(30, 120)
        self.speed = 0.05 if enemy_type == "normal" else 0.03
        
        # Combat properties
        self.health = 100 if enemy_type == "normal" else 200
        self.max_health = self.health
        self.attack_power = 15 if enemy_type == "normal" else 25
        self.color = (150, 150, 150) if enemy_type == "normal" else (0, 0, 200)
        self.size = Config.get('bun_size')
        
        # Special properties
        if enemy_type == "rare":
            self.shield_active = True
            self.shield_health = 50

    def update(self, bunny, dungeon):
        """Update enemy state and movement"""
        if not self.is_awake:
            # Wake up if player is nearby
            dist = math.sqrt((self.x - bunny.x)**2 + (self.y - bunny.y)**2)
            if dist < 5:
                self.is_awake = True
                return
        
        # Handle movement
        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.choice(["left", "right", "up", "down"])
            self.direction_timer = random.randint(30, 120)
        
        # Calculate new position
        new_x, new_y = self.x, self.y
        if self.direction == "left":
            new_x -= self.speed
        elif self.direction == "right":
            new_x += self.speed
        elif self.direction == "up":
            new_y -= self.speed
        elif self.direction == "down":
            new_y += self.speed
        
        # Check if new position is valid
        if self.is_valid_position(new_x, new_y, dungeon):
            self.x, self.y = new_x, new_y
        else:
            self.direction_timer = 0  # Change direction next frame
        
        # Update collision rect
        self.rect.x = self.x * Config.get('bun_size')
        self.rect.y = self.y * Config.get('bun_size')
        
        # Check for attack
        if self.rect.colliderect(bunny.rect):
            bunny.take_damage(self.attack_power)

    def is_valid_position(self, x, y, dungeon):
        """Check if position is valid (not a wall)"""
        # Check all four corners of enemy's hitbox
        size = self.size / Config.get('bun_size')
        corners = [
            (x, y),
            (x + size, y),
            (x, y + size),
            (x + size, y + size)
        ]
        
        for cx, cy in corners:
            grid_x, grid_y = int(cx), int(cy)
            if not (0 <= grid_x < dungeon.width and 0 <= grid_y < dungeon.height):
                return False
            if dungeon.layout[grid_y][grid_x] != '.':
                return False
        return True

    def take_damage(self, amount):
        """Handle taking damage"""
        if hasattr(self, 'shield_active') and self.shield_active:
            self.shield_health -= amount
            if self.shield_health <= 0:
                self.shield_active = False
        else:
            self.health -= amount

    def render(self, screen, camera_x, camera_y):
        """Draw the enemy"""
        # Main body
        pygame.draw.rect(screen, self.color,
                        (self.rect.x - camera_x,
                         self.rect.y - camera_y,
                         self.size, self.size))
        
        # Shield for rare enemies
        if hasattr(self, 'shield_active') and self.shield_active:
            shield_rect = pygame.Rect(
                self.rect.x - camera_x - 5,
                self.rect.y - camera_y - 5,
                self.size + 10,
                self.size + 10)
            pygame.draw.rect(screen, (0, 100, 255), shield_rect, 2)
        
        # Health bar
        health_width = self.size * (self.health / self.max_health)
        pygame.draw.rect(screen, (255, 0, 0),
                        (self.rect.x - camera_x,
                         self.rect.y - camera_y - 10,
                         self.size, 5))
        pygame.draw.rect(screen, (0, 255, 0),
                        (self.rect.x - camera_x,
                         self.rect.y - camera_y - 10,
                         health_width, 5))


class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "boss")
        self.health = 500
        self.max_health = 500
        self.attack_power = 40
        self.color = (200, 0, 0)
        self.size = Config.get('bun_size') * 1.5
        self.speed = 0.02  # Boss moves slower
        self.special_attack_timer = 180

    def update(self, bunny, dungeon):
        """Boss-specific update with special attacks"""
        super().update(bunny, dungeon)
        
        if self.is_awake:
            self.special_attack_timer -= 1
            if self.special_attack_timer <= 0:
                self.special_attack(bunny)
                self.special_attack_timer = 180

    def special_attack(self, bunny):
        """Shockwave attack that damages player"""
        dist = math.sqrt((self.x - bunny.x)**2 + (self.y - bunny.y)**2)
        if dist < 3:  # Attack range
            bunny.take_damage(self.attack_power * 1.5)


class LootBox:
    def __init__(self, x, y, loot_type, bunny=None):
        self.x = x
        self.y = y
        self.loot_type = loot_type
        self.rect = pygame.Rect(
            x * Config.get('bun_size'),
            y * Config.get('bun_size'),
            Config.get('bun_size'),
            Config.get('bun_size'))
        self.opened = False
        self.bunny = bunny

    def update(self, bunny):
        """Check for interaction with bunny"""
        if not self.opened and self.rect.colliderect(bunny.rect):
            self.open(bunny)

    def open(self, bunny):
        """Give loot to bunny"""
        self.opened = True
        if self.loot_type == "health_potion":
            bunny.heal(50)
            bunny.inventory.show_notification("Health +50!", (0, 255, 0))
        elif self.loot_type == "coins":
            coins = random.randint(10, 50)
            bunny.money += coins
            bunny.inventory.show_notification(f"Found {coins} coins!", (255, 255, 0))
        elif self.loot_type == "boss":
            bunny.inventory.items["boss_key"] = 1
            bunny.inventory.items["diamond"] = random.randint(1, 3)
            bunny.money += 100
            bunny.inventory.show_notification("You got the BOSS KEY!", (255, 215, 0))

    def render(self, screen, camera_x, camera_y):
        """Draw the loot box"""
        if not self.opened:
            color = (200, 150, 0) if self.loot_type == "boss" else (150, 100, 0)
            pygame.draw.rect(screen, color,
                           (self.rect.x - camera_x,
                            self.rect.y - camera_y,
                            self.rect.width,
                            self.rect.height))
            pygame.draw.rect(screen, (255, 215, 0),
                           (self.rect.x - camera_x + 5,
                            self.rect.y - camera_y + 5,
                            self.rect.width - 10,
                            self.rect.height - 10), 2)