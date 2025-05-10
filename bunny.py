import pygame
import math,random
from config import *
from collections import defaultdict


class Bunny:
    def __init__(self, x, y, mode='farm',username = 'Unknown'):
        self.name = username
        self.x, self.y = x, y
        self.health = 100
        self.speed = 0.1
        self.target_x, self.target_y = x, y
        self.held_item = None  # Name of the held item, e.g., 'seed'

        self.current_direction = 'front'
        self.mode = mode
        self.rect = pygame.Rect(
            self.x * Config.get('bun_size'),
            self.y * Config.get('bun_size'),
            Config.get('bun_size'),
            Config.get('bun_size')
        )

        self.attack_cooldown = 0
        self.attacking = False
        self.current_frame = 0
        self.frame_time = 1000 // Config.get('FPS')
        self.last_update_time = pygame.time.get_ticks()

        self.load_bunny()

        self.inventory = Inventory()
        self.interact_range = 1.5
        self.current_interactable = None
        self.action_time = 0  # Countdown timer in frames
        self.current_action = None  # e.g., 'cut', 'mine', 'dig'
        self.tools = {
            'axe': {'level': 1, 'speed': 1.0},  # Base speed multiplier
            'pickaxe': {'level': 1, 'speed': 1.0}
        }
        self.current_tool = None
        self.action_progress = 0  # 0-100%
        self.action_target = None  # Tile being worked on
        self.last_interacted = None


    def start_action(self, action_type, target_tile):
        """Start an action with progress tracking"""
        self.current_action = action_type
        self.action_target = target_tile
        self.action_progress = 0
        
        # Determine action speed based on tool level
        if action_type == 'cut':
            tool_level = self.tools['axe']['level']
            self.action_speed = 1.0 / tool_level  # Higher level = faster
        elif action_type == 'mine':
            tool_level = self.tools['pickaxe']['level']
            self.action_speed = 1.0 / tool_level
        elif action_type == 'dig':
            self.action_speed = 1.0  # Default speed for digging

    def update_action(self):
        """Update action progress if performing one"""
        if self.current_action and self.action_target:
            self.action_progress += self.action_speed
            if self.action_progress >= 100:
                self.complete_action()
                
    def complete_action(self):
        """Finish the current action"""
        if self.current_action == 'cut' and self.action_target.type == 'tree':
            self.add_to_inventory('wood')
            self.action_target.type = 'dirt'
            self.action_target.health = 0


        elif self.current_action == 'mine' and self.action_target.type == 'stone':
            self.add_to_inventory('stone')
            self.action_target.type = 'dirt'
        elif self.current_action == 'dig' and self.action_target.type == 'dirt':
            self.action_target.dig()
            # 🎲 Add chance to drop a seed
            if random.random() < 0.5:  # 30% chance
                self.add_to_inventory('seed')
                self.inventory.show_notification("You got a seed!", (200, 255, 100))

        self.current_action = None
        self.action_target = None
        self.action_progress = 0


    def load_bunny(self):
        self.sheet = Config.get("bun_sheet")
        self.frames = {
            "front": [self.sheet["front_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "back": [self.sheet["back_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "left": [self.sheet["left_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "right": [self.sheet["right_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "front_damage": [self.sheet["front_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "back_damage": [self.sheet["back_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(5)],
            "left_damage": [self.sheet["left_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
            "right_damage": [self.sheet["right_damage_sheet"].get_image(i, Config.get("bun_exact"), Config.get("bun_exact"), 2, (0, 0, 0)) for i in range(8)],
        }

    def move(self, keys, world):
        moving = False
        new_direction = self.current_direction

        if self.x == self.target_x and self.y == self.target_y:
            if keys[pygame.K_LEFT]:
                new_x = self.x - 1
                if self.can_move_to(new_x, self.y, world):
                    self.target_x = new_x
                    new_direction = 'left'
                    moving = True
            elif keys[pygame.K_RIGHT]:
                new_x = self.x + 1
                if self.can_move_to(new_x, self.y, world):
                    self.target_x = new_x
                    new_direction = 'right'
                    moving = True
            elif keys[pygame.K_UP]:
                new_y = self.y - 1
                if self.can_move_to(self.x, new_y, world):
                    self.target_y = new_y
                    new_direction = 'back'
                    moving = True
            elif keys[pygame.K_DOWN]:
                new_y = self.y + 1
                if self.can_move_to(self.x, new_y, world):
                    self.target_y = new_y
                    new_direction = 'front'
                    moving = True

        if self.x < self.target_x:
            self.x = min(self.x + self.speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.speed, self.target_x)
        if self.y < self.target_y:
            self.y = min(self.y + self.speed, self.target_y)
        elif self.y > self.target_y:
            self.y = max(self.y - self.speed, self.target_y)

        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0

        self.rect.topleft = (
            self.x * Config.get('bun_size'),
            self.y * Config.get('bun_size')
        )
        return moving

    def can_move_to(self, x, y, world):
        if self.mode == 'maze':
            return (0 <= x < Config.get('grid') and 
                    0 <= y < Config.get('grid') and 
                    world.grid[y][x] == 0)
        else:
            return (0 <= x < world.width and 
                    0 <= y < world.height and 
                    world.tiles[y][x].type not in ('tree', 'stone','house'))

    def update_animation(self, moving):
        current_time = pygame.time.get_ticks()
        if (moving or self.attacking) and current_time - self.last_update_time > self.frame_time:
            if self.current_direction in self.frames:
                frames = self.frames[self.current_direction]
                if frames:
                    self.current_frame = (self.current_frame + 1) % len(frames)
                    if self.attacking and self.current_frame == 0:
                        self.attacking = False
            self.last_update_time = current_time

    def attack(self, enemies):
        current_time = pygame.time.get_ticks()
        if current_time - self.attack_cooldown > 500:
            self.attacking = True
            self.attack_cooldown = current_time
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy.take_damage(10)

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        self.health = min(100, self.health + amount)

    def draw(self, screen, camera_x, camera_y):
        frames = self.frames.get(self.current_direction, [])
        if frames:
            self.current_frame %= len(frames)
            screen.blit(
                frames[self.current_frame],
                (self.x * Config.get('bun_size') - camera_x,
                 self.y * Config.get('bun_size') - camera_y)
            )
        self.inventory.draw(screen)
        # Draw action progress if performing one
        if self.current_action and self.action_target:
            bar_width = 50
            bar_height = 5
            x = self.x * Config.get('bun_size') - camera_x + (Config.get('bun_size') - bar_width) // 2
            y = self.y * Config.get('bun_size') - camera_y - 20  # Above health bar
            
            pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height))
            pygame.draw.rect(screen, (0, 200, 200), (x, y, int(bar_width * (self.action_progress / 100)), bar_height))

        # Draw status text
        if self.current_action:
            font = pygame.font.Font(None, 24)
            status = f"{self.current_action.capitalize()}..."
            text_surface = font.render(status, True, (255, 255, 255))
            screen.blit(text_surface, (
                self.x * Config.get('bun_size') - camera_x,
                self.y * Config.get('bun_size') - camera_y - 40
            ))

        if self.held_item:
            font = pygame.font.Font(None, 24)
            text = f"Holding: {self.held_item}"
            screen.blit(font.render(text, True, (255, 255, 255)), (10, 120))


    def switch_mode(self):
        self.mode = 'maze' if self.mode == 'farm' else 'farm'
        self.current_frame = 0
        self.last_update_time = pygame.time.get_ticks()

    def pick_up(self, items_group):
        for item in items_group:
            dist = math.hypot(self.x - item.rect.centerx / Config.get('bun_size'),
                              self.y - item.rect.centery / Config.get('bun_size'))
            if dist < self.interact_range:
                self.inventory.add_item(item)
                items_group.remove(item)
                break

    def get_front_position(self):
        """Get the position in front of bunny based on current direction"""
        if self.current_direction == 'front':
            return int(self.x), int(self.y) + 1
        elif self.current_direction == 'back':
            return int(self.x), int(self.y) - 1
        elif self.current_direction == 'left':
            return int(self.x) - 1, int(self.y)
        elif self.current_direction == 'right':
            return int(self.x) + 1, int(self.y)
        return int(self.x), int(self.y)  # Default to current position if no direction
    
    def can_interact_with(self, objects, world):
        for obj in objects:
            if self.is_near(obj):
                obj.interact(world)
                self.last_interacted = obj
                break

    def is_near(self, obj):
        dx = self.x - obj.x
        dy = self.y - obj.y
        return math.hypot(dx, dy) <= self.interact_range

    def add_to_inventory(self, item_name, amount=1):
        for _ in range(amount):
            if item_name in Config.RESOURCE_ITEMS:
                self.inventory.add_item(Config.RESOURCE_ITEMS[item_name])

    def harvest_crop(self, farm):
        front_x, front_y = self.get_front_position()
        if 0 <= front_x < farm.width and 0 <= front_y < farm.height:
            tile = farm.tiles[front_y][front_x]
            if tile.plant and tile.plant.harvestable:
                if tile.harvest(self):
                    self.inventory.show_notification("Harvested crop!", (200, 200, 0))
                else:
                    self.inventory.show_notification("Not ready to harvest!", (255, 100, 0))
            elif tile.plant:
                self.inventory.show_notification("Crop still growing...", (100, 255, 100))
            else:
                self.inventory.show_notification("Nothing to harvest here", (200, 200, 200))


class Inventory:
    def __init__(self, capacity=5):  # Increased capacity
        self.capacity = capacity
        self.items = defaultdict(int)
        # Start with some seeds
        self.items["carrot_seed"] = 5
        self.notification = None
        self.notification_time = 0
        self.full_view = False  # For toggling full inventory screen


    def is_full(self):
        # Return True if the number of unique items exceeds the capacity
        return len(self.items) >= self.capacity

    def add_item(self, item):
        if len(self.items) < self.capacity:  # Check if there's space for new items
            self.items[item.name] += 1
            if self.items[item.name] <= 0:  # If count reaches zero, delete the item
                del self.items[item.name]
            self.show_notification(f"Picked up {item.name}", (0, 255, 0))
            return True
        self.show_notification("Inventory Full!", (255, 0, 0))
        return False

    def draw(self, screen):
        if self.full_view:
            self.draw_full_inventory(screen)
        else:
            self.draw_quick_bar(screen)

    def draw_quick_bar(self, screen):
        slot_size = 64
        padding = 5
        start_x = (screen.get_width() - (slot_size + padding) * self.capacity) // 2
        y = screen.get_height() - slot_size - 10

        item_list = list(self.items.items())
        for i in range(self.capacity):
            rect = pygame.Rect(start_x + i * (slot_size + padding), y, slot_size, slot_size)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            if i < len(item_list):
                name, count = item_list[i]
                if count > 0:  # Only draw the item if count is greater than 0
                    item = Config.RESOURCE_ITEMS[name]
                    img = pygame.transform.scale(item.image, (slot_size - 10, slot_size - 10))
                    screen.blit(img, (rect.x + 5, rect.y + 5))
                    font = pygame.font.SysFont(None, 22)
                    count_surface = font.render(str(count), True, (255, 255, 255))
                    screen.blit(count_surface, (rect.right - 18, rect.bottom - 22))

        if self.notification and pygame.time.get_ticks() - self.notification_time < 2000:
            notif_img, _ = self.notification
            screen.blit(notif_img, (20, 20))


    def draw_full_inventory(self, screen):
        width = 600
        height = 300
        box = pygame.Rect((screen.get_width() - width) // 2, (screen.get_height() - height) // 2, width, height)
        pygame.draw.rect(screen, (50, 50, 50), box)
        pygame.draw.rect(screen, (200, 200, 200), box, 4)

        font = pygame.font.SysFont(None, 28)
        title = font.render("Inventory", True, (255, 255, 255))
        screen.blit(title, (box.x + 20, box.y + 10))

        slot_size = 50
        padding = 10
        cols = 6
        start_x = box.x + 20
        start_y = box.y + 50

        item_list = list(self.items.items())
        for i, (name, count) in enumerate(item_list):
            if count > 0:  # Only draw the item if count is greater than 0
                item = Config.RESOURCE_ITEMS[name]
                row = i // cols
                col = i % cols
                x = start_x + col * (slot_size + padding)
                y = start_y + row * (slot_size + padding)

                rect = pygame.Rect(x, y, slot_size, slot_size)
                pygame.draw.rect(screen, (180, 180, 180), rect, 2)
                img = pygame.transform.scale(item.image, (slot_size - 10, slot_size - 10))
                screen.blit(img, (x + 5, y + 5))

                count_surf = font.render(str(count), True, (255, 255, 255))
                screen.blit(count_surf, (x + slot_size - 35, y + slot_size - 20))

    def show_notification(self, text, color):
        font = pygame.font.SysFont(None, 30)
        self.notification = (font.render(text, True, color), pygame.time.get_ticks())
        self.notification_time = pygame.time.get_ticks()

    def toggle_inventory_view(self):
        self.full_view = not self.full_view


class Stone:
    def __init__(self, tile_x, tile_y, image_path='assets/items/stone.png'):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.health = 2  # Number of hits to destroy
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(tile_x * 32, tile_y * 32))

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y

    def interact(self, game):
        self.health -= 1
        print("You hit the stone! HP:", self.health)
        if self.health <= 0:
            print("Stone is destroyed! You got stone.")
            game.inventory.add_item("stone")
            game.farm.interactables.remove(self)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Tree:
    def __init__(self, tile_x, tile_y, image_path='assets/items/tree.png'):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.health = 3  # Number of hits to destroy
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(topleft=(tile_x * 32, tile_y * 32))

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y
    
    def interact(self, game):
        self.health -= 1
        print("You chopped the tree! HP:", self.health)
        if self.health <= 0:
            print("Tree is gone! You got wood.")
            game.inventory.add_item("wood")
            game.farm.interactables.remove(self)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Portal:
    def __init__(self, tile_x, tile_y, target_world='maze', target_pos=(1, 1)):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.target_world = target_world
        self.target_pos = target_pos
        self.size = Config.get('bun_size')
        self.interact_text = "Enter portal (SPACE)"
        self.cooldown = 0  # Added cooldown timer

    @property
    def x(self):
        return self.tile_x

    @property
    def y(self):
        return self.tile_y
    
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
        if self.cooldown <= 0:
            if self.target_world == 'maze':
                game.warp_to_maze()
            else:
                game.warp_to_farm()
            self.cooldown = 30

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def interact(self, game):
        self.teleport(game)

