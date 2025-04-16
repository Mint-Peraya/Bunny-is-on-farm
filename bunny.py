import pygame
import math
from config import *
from collections import defaultdict


class Inventory:
    def __init__(self, capacity=5):
        self.capacity = capacity
        self.items = defaultdict(int)  # {item_name: count}
        self.notification = None
        self.notification_time = 0
        self.full_view = False  # For toggling full inventory screen

    def is_full(self):
        return sum(self.items.values()) >= self.capacity

    def add_item(self, item):
        if not self.is_full() or item.name in self.items:
            self.items[item.name] += 1
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
        padding = 10
        start_x = (screen.get_width() - (slot_size + padding) * self.capacity) // 2
        y = screen.get_height() - slot_size - 10

        item_list = list(self.items.items())
        for i in range(self.capacity):
            rect = pygame.Rect(start_x + i * (slot_size + padding), y, slot_size, slot_size)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)
            if i < len(item_list):
                name, count = item_list[i]
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
            screen.blit(count_surf, (x + slot_size - 20, y + slot_size - 20))

    def show_notification(self, text, color):
        font = pygame.font.SysFont(None, 30)
        self.notification = (font.render(text, True, color), pygame.time.get_ticks())
        self.notification_time = pygame.time.get_ticks()

    def toggle_inventory_view(self):
        self.full_view = not self.full_view


class Bunny:
    def __init__(self, x, y, mode='farm'):
        self.x, self.y = x, y
        self.health = 100
        self.speed = 0.1
        self.target_x, self.target_y = x, y

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

    def start_action(self, action_type):
        if self.action_time == 0:
            self.current_action = action_type
            self.action_time = 60  # Takes 1 second if your FPS is 60



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
                    world.tiles[y][x].type not in ('tree', 'stone'))

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
        self.draw_health_bar(screen, camera_x, camera_y)
        self.inventory.draw(screen)

    def draw_health_bar(self, screen, camera_x, camera_y):
        bar_width = 50
        bar_height = 5
        x = self.x * Config.get('bun_size') - camera_x + (Config.get('bun_size') - bar_width) // 2
        y = self.y * Config.get('bun_size') - camera_y - 10

        pygame.draw.rect(screen, (255, 0, 0), (x, y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (x, y, bar_width * (self.health / 100), bar_height))

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

    def can_interact_with(self, obj):
        if hasattr(obj, 'tile_x') and hasattr(obj, 'tile_y'):
            distance = math.sqrt((self.x - obj.tile_x)**2 + (self.y - obj.tile_y)**2)
            return distance <= self.interact_range
        return False

    def add_to_inventory(self, item_name, amount=1):
        for _ in range(amount):
            if item_name in Config.RESOURCE_ITEMS:
                self.inventory.add_item(Config.RESOURCE_ITEMS[item_name])
