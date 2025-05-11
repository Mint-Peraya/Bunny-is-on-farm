import pygame
import math,random,csv
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
        self.money = 0

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

        self.carrot_weapon = {
            'damage': 20,
            'cooldown': 0,
            'max_cooldown': 30,  # frames
            'range': 5,  # tiles
            'speed': 0.3,  # tiles per frame
            'projectiles': []  # Active carrot projectiles
        }

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
            if random.random() < 0.5:
                x = random.choice(["carrot_seed","potato_seed","radish_seed","spinach_seed","turnip_seed"])
                self.add_to_inventory(x)
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
        """Check if the bunny can move to the specified (x, y) position."""
        if self.mode == 'maze':
            return (0 <= x < Config.get('grid') and 
                    0 <= y < Config.get('grid') and 
                    world.grid[y][x] == 0)
        elif self.mode == 'dungeon':
            # Check for walkability in the dungeon
            return world.is_tile_walkable(int(x), int(y))
        elif self.mode == 'farm':
            # For farm, check the type of tile at (x, y)
            if 0 <= x < world.width and 0 <= y < world.height:
                tile = world.tiles[y][x]  # Get the tile at (x, y)
                # Check if the tile is walkable (empty or dirt type)
                return tile.type in ['empty', 'dirt']
            return False
        else:
            return True  # Assume walkable for other modes

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

        self.draw_projectiles(screen, camera_x, camera_y)

    def switch_mode(self):
        self.mode = 'maze' if self.mode == 'farm' else 'farm'
        self.current_frame = 0
        self.last_update_time = pygame.time.get_ticks()

    def pick_up(self, items_group):
        for item in items_group:
            dist = math.hypot(self.x - item.rect.centerx / Config.get('bun_size'),
                              self.y - item.rect.centery / Config.get('bun_size'))
            if dist < self.interact_range:
                if self.inventory.add_item(item.name):  # Add item to inventory if there's space
                    items_group.remove(item)  # Remove item from the world
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

    # In the throw_carrot method in Bunny class (bunny.py)
    def throw_carrot(self):
        if (self.carrot_weapon['cooldown'] <= 0 and 
            'carrot_weapon' in self.inventory.items and 
            self.inventory.items['carrot_weapon'] > 0 and
            self.inventory.use_item('carrot_weapon')):  # Changed to use_item
            self.carrot_weapon['cooldown'] = self.carrot_weapon['max_cooldown']

            # Create projectile based on facing direction
            direction_map = {
                'front': (0, 1),
                'back': (0, -1),
                'left': (-1, 0),
                'right': (1, 0)
            }
            dx, dy = direction_map.get(self.current_direction, (0, 1))
            
            self.carrot_weapon['projectiles'].append({
                'x': self.x,
                'y': self.y,
                'dx': dx * self.carrot_weapon['speed'],
                'dy': dy * self.carrot_weapon['speed'],
                'distance': 0
            })
            self.attacking = True
            self.current_frame = 0

            self.log_accuracy(success=False)
    
    def log_accuracy(self, success):
        with open("Data/combat_accuracy.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([int(success)])  # 1 = hit, 0 = miss

    def update_projectiles(self, enemies, dungeon):
        # Update cooldown
        if self.carrot_weapon['cooldown'] > 0:
            self.carrot_weapon['cooldown'] -= 1
        
        # Create a list of projectiles to remove
        projectiles_to_remove = []
        
        # Update existing projectiles
        for proj in self.carrot_weapon['projectiles']:
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            proj['distance'] += self.carrot_weapon['speed']
            
            # Check for hits
            proj_rect = pygame.Rect(
                proj['x'] * Config.get('bun_size'),
                proj['y'] * Config.get('bun_size'),
                Config.get('bun_size') // 2,
                Config.get('bun_size') // 2
            )
            
            # Check enemy collisions
            for enemy in enemies:
                if proj_rect.colliderect(enemy.rect):
                    enemy.take_damage(self.carrot_weapon['damage'])

                    # ✅ Log hit
                    self.log_accuracy(success=True)

                    projectiles_to_remove.append(proj)
                    break  # Stop checking other enemies for this projectile

                screen_w, screen_h = Config.get('window')
                if (proj['x'] < 0 or proj['x'] * Config.get('bun_size') > screen_w or
                    proj['y'] < 0 or proj['y'] * Config.get('bun_size') > screen_h):
                    self.log_accuracy(success=False)
                    projectiles_to_remove.append(proj)

                    if self.name == "Player":
                        self.log_accuracy(success=False)
                    projectiles_to_remove.append(proj)
                    for proj in projectiles_to_remove:
                        if proj in self.carrot_weapon['projectiles']:
                            self.carrot_weapon['projectiles'].remove(proj)
            
            # Check wall collisions or max range
            if (proj['distance'] >= self.carrot_weapon['range'] or 
                not dungeon.is_valid_position(proj['x'], proj['y'])):
                projectiles_to_remove.append(proj)
        
        # Remove marked projectiles
        for proj in projectiles_to_remove:
            if proj in self.carrot_weapon['projectiles']:
                self.carrot_weapon['projectiles'].remove(proj)

    def draw_projectiles(self, screen, camera_x, camera_y):
        carrot_img = pygame.image.load('assets/items/carrot_weapon.png').convert_alpha()
        for proj in self.carrot_weapon['projectiles'][:]:
            screen.blit(carrot_img, (proj['x'] * Config.get('bun_size') - camera_x, proj['y'] * Config.get('bun_size') - camera_y))
    
    # In the Bunny class, handle the key presses for item selection
    def handle_key_press(self, event):
        if event.key == pygame.K_1:
            self.select_item_for_swap(0)
        elif event.key == pygame.K_2:
            self.select_item_for_swap(1)
        elif event.key == pygame.K_3:
            self.select_item_for_swap(2)
        elif event.key == pygame.K_4:
            self.select_item_for_swap(3)
        elif event.key == pygame.K_5:
            self.select_item_for_swap(4)
        elif event.key == pygame.K_6:
            self.select_item_for_swap(5)

    def select_item_for_swap(self, index):
        if 0 <= index < len(self.inventory):
            self.held_item = self.inventory[index]  # Select the item
            print(f"Item selected: {self.held_item}")  # For debugging purposes

    def select_hotbar_item(self, slot_index):
        """Select an item from the hotbar to hold"""
        if 0 <= slot_index < len(self.inventory.hotbar_indices):
            item_index = self.inventory.hotbar_indices[slot_index]
            if item_index is not None:
                items_list = list(self.inventory.items.items())
                if item_index < len(items_list):
                    self.held_item = items_list[item_index][0]
                    print(f"Now holding: {self.held_item}")  # Debug output


class Inventory:
    def __init__(self, capacity=20):
        self.capacity = capacity
        self.items = defaultdict(int)
        # Initialize hotbar with first 6 items if they exist
        self.hotbar_indices = [i if i < capacity else None for i in range(6)]
        self.swap_selected_index = None
        self.swap_input_text = ""
        self.show_swap_box = False
        self.full_view = False
        self.dragged_item = None
        self.notification = None
        self.notification_time = 0

    def is_full(self):
        return sum(self.items.values()) >= self.capacity

    def update_inventory_ui(self):
        """Ensure hotbar indices are valid after inventory changes"""
        # Create a list of available item indices
        available_indices = list(range(len(self.items)))
        
        # Update hotbar indices, keeping None for empty slots
        self.hotbar_indices = [
            idx if idx is not None and idx < len(self.items) else None
            for idx in self.hotbar_indices
        ]

    def add_item(self, item):
        """Add item to inventory - accepts either ResourceItem object or string name"""
        if hasattr(item, 'name'):
            item_name = item.name
        else:
            item_name = item
            item = Config.RESOURCE_ITEMS.get(item_name, None)
        
        if not self.is_full():
            # If this is a new item type, add it to the inventory
            if item_name not in self.items:
                # Find the first empty hotbar slot if available
                for i in range(len(self.hotbar_indices)):
                    if self.hotbar_indices[i] is None:
                        self.hotbar_indices[i] = len(self.items)
                        break
            
            self.items[item_name] = self.items.get(item_name, 0) + 1
            return True
        return False
    
    def show_notification(self, text, color):
        font = pygame.font.SysFont(None, 30)
        self.notification = (font.render(text, True, color), pygame.time.get_ticks())
        self.notification_time = pygame.time.get_ticks()

    def show_notification(self, text, color):
        font = pygame.font.SysFont(None, 30)
        self.notification = (font.render(text, True, color), pygame.time.get_ticks())
        self.notification_time = pygame.time.get_ticks()

    def draw(self, screen):
        """Draw inventory UI based on current view"""
        if self.full_view:
            self.draw_full_inventory(screen)
        else:
            self.draw_quick_bar(screen)

    def draw_quick_bar(self, screen):
        """Draw only the 6 slots of the hotbar"""
        slot_size = 64
        padding = 5
        start_x = (screen.get_width() - (slot_size + padding) * 6) // 2
        y = screen.get_height() - slot_size - 10

        for i in range(6):
            rect = pygame.Rect(start_x + i * (slot_size + padding), y, slot_size, slot_size)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            item_index = self.hotbar_indices[i]
            if item_index is not None and item_index < len(self.items):
                item_name, count = list(self.items.items())[item_index]
                if count > 0:
                    item = Config.RESOURCE_ITEMS[item_name]
                    img = pygame.transform.scale(item.image, (slot_size - 10, slot_size - 10))
                    screen.blit(img, (rect.x + 5, rect.y + 5))
                    font = pygame.font.SysFont(None, 22)
                    count_surface = font.render(str(count), True, (255, 255, 255))
                    screen.blit(count_surface, (rect.right - 18, rect.bottom - 22))

    def select_item_for_swap(self, index):
        """Select an item to swap into the hotbar."""
        item_list = list(self.items.items())
        if 0 <= index < len(item_list):
            self.swap_selected_index = index
            self.show_swap_box = True  # Show the input box for slot selection
    
    def draw_full_inventory(self, screen):
        width = 600
        height = 300
        box = pygame.Rect((screen.get_width() - width) // 2, (screen.get_height() - height) // 2, width, height)
        pygame.draw.rect(screen, (50, 50, 50), box)
        pygame.draw.rect(screen, (200, 200, 200), box, 4)

        font = pygame.font.Font(Config.get('font'), 24)
        title = font.render("Inventory", True, (255, 255, 255))
        screen.blit(title, (box.x + 20, box.y + 10))

        slot_size = 50
        padding = 10
        cols = 6
        start_x = box.x + 20
        start_y = box.y + 50

        item_list = list(self.items.items())
        
        # First pass: draw all items except the dragged one
        for i, (name, count) in enumerate(item_list):
            if count > 0 and i != self.dragged_item:
                self.draw_inventory_item(screen, name, count, i, start_x, start_y, slot_size, padding, cols, font)

        # Handle dragging logic
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Check for new drag
        if mouse_pressed[0] and self.dragged_item is None:
            for i, (name, count) in enumerate(item_list):
                if count > 0:
                    row = i // cols
                    col = i % cols
                    x = start_x + col * (slot_size + padding)
                    y = start_y + row * (slot_size + padding)
                    rect = pygame.Rect(x, y, slot_size, slot_size)
                    
                    if rect.collidepoint(mouse_pos):
                        self.dragged_item = i
                        break
        
        # Draw dragged item last (on top) if it exists
        if self.dragged_item is not None:
            if mouse_pressed[0]:
                # Draw dragged item at mouse position
                name, count = item_list[self.dragged_item]
                item = Config.RESOURCE_ITEMS[name]
                img = pygame.transform.scale(item.image, (slot_size - 10, slot_size - 10))
                screen.blit(img, (mouse_pos[0] - slot_size//2, mouse_pos[1] - slot_size//2))
            else:
                # Mouse released, check for drop
                for i, (name, count) in enumerate(item_list):
                    if count > 0:
                        row = i // cols
                        col = i % cols
                        x = start_x + col * (slot_size + padding)
                        y = start_y + row * (slot_size + padding)
                        rect = pygame.Rect(x, y, slot_size, slot_size)
                        
                        if rect.collidepoint(mouse_pos) and i != self.dragged_item:
                            # Swap items
                            keys = list(self.items.keys())
                            keys[self.dragged_item], keys[i] = keys[i], keys[self.dragged_item]
                            self.items = defaultdict(int, {k: self.items[k] for k in keys})
                self.dragged_item = None

    def draw_inventory_item(self, screen, name, count, index, start_x, start_y, slot_size, padding, cols, font):
        row = index // cols
        col = index % cols
        x = start_x + col * (slot_size + padding)
        y = start_y + row * (slot_size + padding)

        rect = pygame.Rect(x, y, slot_size, slot_size)
        pygame.draw.rect(screen, (180, 180, 180), rect, 2)
        
        item = Config.RESOURCE_ITEMS[name]
        img = pygame.transform.scale(item.image, (slot_size - 10, slot_size - 10))
        screen.blit(img, (x + 5, y + 5))

        count_surf = font.render(str(count), True, (255, 255, 255))
        screen.blit(count_surf, (x + slot_size - 35, y + slot_size - 20))
        def show_notification(self, text, color):
            font = pygame.font.SysFont(None, 30)
            self.notification = (font.render(text, True, color), pygame.time.get_ticks())
            self.notification_time = pygame.time.get_ticks()

    def toggle_inventory_view(self):
        """Toggle between full inventory and hotbar view"""
        self.full_view = not self.full_view
        self.show_swap_box = False  # Reset swap box when toggling
    
    def use_item(self, item_name):
        if self.items.get(item_name, 0) > 0:
            self.items[item_name] -= 1
            self.log_item_use(item_name)
            return True
        return False

    def log_item_use(self, item_name):
        with open("Data/inventory_usage.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([item_name])
    
    def handle_key_press(self, event):
        if event.key == pygame.K_1:
            self.select_item_for_swap(0)
        elif event.key == pygame.K_2:
            self.select_item_for_swap(1)
        elif event.key == pygame.K_3:
            self.select_item_for_swap(2)
        elif event.key == pygame.K_4:
            self.select_item_for_swap(3)
        elif event.key == pygame.K_5:
            self.select_item_for_swap(4)
        elif event.key == pygame.K_6:
            self.select_item_for_swap(5)


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
    def __init__(self, tile_x, tile_y, target_world='random', target_pos=(1, 1)):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.target_world = target_world  # Can be 'random', 'dungeon', or 'maze'
        self.target_pos = target_pos
        self.size = Config.get('bun_size')
        self.interact_text = "Enter portal (SPACE)"
        self.cooldown = 0

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
        """Handle the portal teleportation logic."""
        if self.cooldown <= 0:
            if self.target_world == 'maze':
                game.warp_to_maze()
            elif self.target_world == 'dungeon':
                game.warp_to_dungeon()
            elif self.target_world == 'farm':
                game.warp_to_farm()
            self.cooldown = 30  # Set cooldown only when leaving, not when returning
    
    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def interact(self, game):
        """Handle portal interaction with random destination"""
        if self.cooldown <= 0:
            if self.target_world == 'random':
                # 50% chance for either dungeon or maze
                if random.random() < 0.5:
                    game.warp_to_dungeon()
                else:
                    game.warp_to_maze()
            elif self.target_world == 'dungeon':
                game.warp_to_dungeon()
            elif self.target_world == 'maze':
                game.warp_to_maze()
            
            self.cooldown = 10  # Prevent immediate re-use

