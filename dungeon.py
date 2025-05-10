import pygame
import math, csv
import random
from config import *
from farm import Tile

class Dungeon:
    def __init__(self, width, height, bunny):
        self.width = width
        self.height = height
        self.layout = self.generate_dungeon_layout()  # Generate layout (rooms/corridors)
        self.tiles = self.create_tiles()  # Initialize tiles
        self.enemies = []
        self.create_rooms_and_enemies()
        self.loot_boxes = []  # For storing loot boxes from dead enemies
        self.exit_x = self.width - 2  # Example exit coordinates
        self.exit_y = self.height - 2
        self.bunny = bunny

    def create_tiles(self):
        """Create a grid of tiles with types for the dungeon."""
        tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                if random.random() > 0.8:
                    row.append(Tile(x, y, 'tree'))  # Example: random trees
                else:
                    row.append(Tile(x, y, 'empty'))  # Example: empty space
            tiles.append(row)
        return tiles

    def update(self, bunny):
        """Update the state of the dungeon. For example, update enemies or check conditions."""
        # Update enemies (patrolling, checking if they see the player, etc.)
        for enemy in self.enemies:
            enemy.update(bunny, self)  # Now you can use bunny properly

        # Update any loot boxes or special effects
        for loot_box in self.loot_boxes:
            loot_box.update(bunny)


    def generate_dungeon_layout(self):
        """Generate a fixed dungeon layout with rooms and corridors"""
        layout = [['#' for _ in range(self.width)] for _ in range(self.height)]
        
        # Create main rooms
        main_room = (10, 5, 10, 10)  # Central room for the boss
        room_1 = (3, 3, 6, 6)        # Top-left room
        room_2 = (21, 3, 6, 6)       # Top-right room
        room_3 = (3, 15, 6, 6)       # Bottom-left room
        room_4 = (21, 15, 6, 6)      # Bottom-right room
        
        self.create_room(layout, main_room)
        self.create_room(layout, room_1)
        self.create_room(layout, room_2)
        self.create_room(layout, room_3)
        self.create_room(layout, room_4)
        
        # Create corridors connecting to central room
        self.create_corridor(layout, (9, 5), (9, 3))    # Vertical to top
        self.create_corridor(layout, (9, 15), (9, 20))  # Vertical to bottom
        self.create_corridor(layout, (5, 10), (3, 10))  # Horizontal to left
        self.create_corridor(layout, (15, 10), (21, 10)) # Horizontal to right
        
        # Create some decorative walls/pillars
        for x, y in [(8, 8), (12, 8), (8, 12), (12, 12)]:
            layout[y][x] = '#'
        
        return layout

    def create_room(self, layout, room):
        """Mark room area in the dungeon layout"""
        x, y, w, h = room
        for i in range(y, y + h):
            for j in range(x, x + w):
                if 0 <= i < self.height and 0 <= j < self.width:
                    layout[i][j] = '.'

    def create_corridor(self, layout, start, end):
        """Create a simple corridor between two points"""
        x1, y1 = start
        x2, y2 = end
        if x1 == x2:  # Vertical corridor
            for i in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= i < self.height:
                    layout[i][x1] = '.'
        elif y1 == y2:  # Horizontal corridor
            for i in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= i < self.width:
                    layout[y1][i] = '.'

    def create_rooms_and_enemies(self):
        """Place enemies in predefined positions"""
        # Boss in the center room
        self.enemies.append(Boss(15, 10))

        # Normal enemies (guards)
        self.enemies.append(Enemy(5, 5, "normal"))    # Top-left room
        self.enemies.append(Enemy(7, 7, "normal"))    # Top-left room
        self.enemies.append(Enemy(24, 5, "normal"))   # Top-right room
        self.enemies.append(Enemy(22, 7, "normal"))   # Top-right room
        self.enemies.append(Enemy(5, 18, "normal"))   # Bottom-left room
        self.enemies.append(Enemy(7, 16, "normal"))  # Bottom-left room
        self.enemies.append(Enemy(24, 18, "normal")) # Bottom-right room
        self.enemies.append(Enemy(22, 16, "normal")) # Bottom-right room

        # Rare enemies (with shields and fire)
        self.enemies.append(Enemy(5, 7, "rare"))     # Top-left room
        self.enemies.append(Enemy(24, 16, "rare"))   # Bottom-right room

    def render(self, screen, camera_x, camera_y):
        """Render the dungeon layout"""
        for i in range(self.height):
            for j in range(self.width):
                if self.layout[i][j] == '#':
                    pygame.draw.rect(screen, (50, 50, 70), 
                                (j * Config.get('bun_size') - camera_x, 
                                    i * Config.get('bun_size') - camera_y, 
                                    Config.get('bun_size'), 
                                    Config.get('bun_size')))
                elif self.layout[i][j] == '.':
                    pygame.draw.rect(screen, (80, 80, 100), 
                                (j * Config.get('bun_size') - camera_x, 
                                    i * Config.get('bun_size') - camera_y, 
                                    Config.get('bun_size'), 
                                    Config.get('bun_size')))
        
        # Render enemies
        for enemy in self.enemies[:]:
            enemy.update(self.bunny, self)
            if enemy.health <= 0:
                        # In the render method where loot boxes are created:
                if isinstance(enemy, Boss):
                    # Pass bunny reference when creating loot box
                    self.loot_boxes.append(LootBox(enemy.x, enemy.y, "boss", self.bunny))
                elif not enemy.has_dropped_loot:
                    loot_type = "health_potion" if random.random() > 0.5 else "coins"
                    self.loot_boxes.append(LootBox(enemy.x, enemy.y, loot_type, self.bunny))
                    enemy.has_dropped_loot = True
                with open('Data/Enemy_difficulty.csv', 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([enemy.enemy_type, "kill"])

                self.enemies.remove(enemy)
            else:
                enemy.render(screen, camera_x, camera_y)
                if self.bunny.health<= 0:
                    with open('Data/Enemy_difficulty.csv', 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([enemy.enemy_type,"fainted"])
        
        # Render loot boxes
        for loot_box in self.loot_boxes:
            loot_box.update(self.bunny)  # Check if loot box is opened by bunny
            loot_box.render(screen, camera_x, camera_y)
    
    def is_valid_position(self, x, y):
        """Check if position is walkable (not a wall)"""
        grid_x, grid_y = int(x), int(y)
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            return self.layout[grid_y][grid_x] == '.'
        return False
        



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
        self.fire_particles = []
        self.fire_timer = 0
        self.special_attack_timer = 0  # Add this line
        self.attack_cooldown = 0  # Add this line
        
        # Set stats based on type
        if enemy_type == "boss":
            self.health = 500
            self.max_health = 500
            self.attack_power = 40
            self.speed = 0  # Boss doesn't move
            self.color = (200, 0, 0)  # Dark red
            self.size = Config.get('bun_size') * 1.5  # Bigger size
        elif enemy_type == "normal":
            self.health = 100
            self.max_health = 100
            self.attack_power = 15
            self.speed = 0.05
            self.color = (150, 150, 150)  # Gray
            self.size = Config.get('bun_size')
            self.direction = random.choice(["left", "right", "up", "down"])
            self.direction_timer = 0
        elif enemy_type == "rare":
            self.health = 200
            self.max_health = 200
            self.attack_power = 25
            self.speed = 0.03
            self.color = (0, 0, 200)  # Blue
            self.size = Config.get('bun_size')
            self.direction = random.choice(["left", "right", "up", "down"])
            self.direction_timer = 0
            self.shield_active = True
            self.shield_health = 50

    def update(self, bunny, dungeon):
        """Update enemy state"""
        if not self.is_awake:
            dist = ((self.x - bunny.x)**2 + (self.y - bunny.y)**2)**0.5
            if dist < 5:  # Detection radius
                self.is_awake = True
        
        if self.is_awake:
            self.patrol(dungeon)
            if self.rect.colliderect(bunny.rect):
                self.attack_player(bunny)

    # In the Enemy class, modify the patrol method:
    def patrol(self, dungeon):
        """Patrol behavior for normal and rare enemies"""
        if self.direction_timer <= 0:
            self.direction = random.choice(["left", "right", "up", "down"])
            self.direction_timer = random.randint(30, 120)
        else:
            self.direction_timer -= 1

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
        
        # Check if new position is valid (using more precise collision)
        if self.is_valid_position(new_x, new_y, dungeon):
            self.x, self.y = new_x, new_y
        else:
            self.direction_timer = 0  # Change direction if blocked
        
        # Update rect position
        self.rect.x = self.x * Config.get('bun_size')
        self.rect.y = self.y * Config.get('bun_size')

    def is_valid_position(self, x, y, dungeon):
        """Check if position is valid (not a wall) with fractional coordinates"""
        # Check all four corners of the enemy's hitbox
        size = self.size / Config.get('bun_size')  # Convert to tile units
        corners = [
            (x, y),
            (x + size, y),
            (x, y + size),
            (x + size, y + size)
        ]
        
        for corner_x, corner_y in corners:
            grid_x, grid_y = int(corner_x), int(corner_y)
            if not (0 <= grid_x < dungeon.width and 0 <= grid_y < dungeon.height):
                return False
            if dungeon.layout[grid_y][grid_x] != '.':
                return False
        return True
    
    def attack_player(self, player):
        """Attack the player"""
        player.take_damage(self.attack_power)
    
    def take_damage(self, amount):
        """Take damage from player's attack"""
        if self.enemy_type == "rare" and self.shield_active:
            self.shield_health -= amount
            if self.shield_health <= 0:
                self.shield_active = False
        else:
            self.health -= amount
    
    def create_fire_effect(self):
        """Create fire particles around rare enemy"""
        for _ in range(5):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(0.5, 1.5)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            lifetime = random.randint(30, 60)
            self.fire_particles.append([
                self.x * Config.get('bun_size'), 
                self.y * Config.get('bun_size'), 
                dx, dy, lifetime
            ])
    
    def drop_loot(self):
        """Drop loot when enemy dies"""
        if self.enemy_type == "normal":
            loot_type = random.choice(["health_potion", "coins", "weapon"])
        elif self.enemy_type == "rare":
            loot_type = random.choice(["rare_weapon", "magic_orb", "shield"])
        print(f"Dropped {loot_type} from {self.enemy_type} enemy")
        # You would add the loot to the game world here
    
    def render(self, screen, camera_x, camera_y):
        """Render the enemy"""
        # Draw enemy body
        pygame.draw.rect(screen, self.color, 
                        (self.rect.x - camera_x, 
                         self.rect.y - camera_y, 
                         self.size, self.size))
        
        # Draw fire particles for rare enemy
        if self.enemy_type == "rare":
            for particle in self.fire_particles:
                pygame.draw.circle(screen, (255, 100, 0), 
                                 (int(particle[0] - camera_x), 
                                 int(particle[1] - camera_y)), 
                                 3)
        
        # Draw shield for rare enemy if active
        if self.enemy_type == "rare" and self.shield_active:
            shield_rect = pygame.Rect(
                self.rect.x - camera_x - 5, 
                self.rect.y - camera_y - 5, 
                self.size + 10, 
                self.size + 10
            )
            pygame.draw.rect(screen, (0, 100, 255), shield_rect, 2)
        
        # Draw health bar
        health_percent = self.health / self.max_health
        bar_width = self.size
        bar_height = 5
        pygame.draw.rect(screen, (255, 0, 0), 
                         (self.rect.x - camera_x, 
                          self.rect.y - camera_y - 10, 
                          bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                         (self.rect.x - camera_x, 
                          self.rect.y - camera_y - 10, 
                          int(bar_width * health_percent), bar_height))

class Boss(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "boss")
        self.patrol_direction = 'left'  # Add this line
        self.direction_timer = 5  # Add this line
        self.special_attack_timer = 180  # Add this line
        self.attack_cooldown = 0  # Add this line
    
        # In the Boss class, modify the patrol method:
    def patrol(self, dungeon):
        """Boss-specific patrol that integrates with parent class"""
        if self.direction_timer <= 0:
            self.change_direction()
            self.direction_timer = 30  # Longer timer for smoother movement
        else:
            self.direction_timer -= 1

        # Move with fractional coordinates for smooth movement
        new_x, new_y = self.x, self.y
        if self.patrol_direction == 'left':
            new_x -= self.speed * 0.5  # Slower movement for boss
        elif self.patrol_direction == 'right':
            new_x += self.speed * 0.5
        
        if self.is_valid_position(new_x, new_y, dungeon):
            self.x, self.y = new_x, new_y
        
        # Update rect position
        self.rect.x = self.x * Config.get('bun_size')
        self.rect.y = self.y * Config.get('bun_size')

    def change_direction(self):
        """Change the patrol direction"""
        if self.patrol_direction == 'left':
            self.patrol_direction = 'right'
        else:
            self.patrol_direction = 'left'

    def move_in_direction(self):
        """Move the boss in its current patrol direction"""
        if self.patrol_direction == 'left':
            self.x -= 1
        elif self.patrol_direction == 'right':
            self.x += 1

    def render(self, screen, camera_x, camera_y):
        """Render the Boss, with special effects like aura"""
        super().render(screen, camera_x, camera_y)
        # Add any unique rendering logic here (like aura effects)
         # Draw special aura when awake
        if self.is_awake:
            time = pygame.time.get_ticks() / 500
            pulse = math.sin(time) * 3 + 5
            aura_rect = pygame.Rect(
                self.rect.x - camera_x - pulse, 
                self.rect.y - camera_y - pulse, 
                self.size + pulse * 2, 
                self.size + pulse * 2
            )
            pygame.draw.rect(screen, (255, 100, 100, 50), aura_rect, 2)

    def update(self, player, dungeon):
        """Boss-specific update"""
        super().update(player, dungeon)
        
        if self.is_awake:
            # Special attack every few seconds
            if self.special_attack_timer <= 0:
                self.special_attack(player)
                self.special_attack_timer = 180  # 3 seconds at 60 FPS
            else:
                self.special_attack_timer -= 1
            
            # Regular attack cooldown
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
    
    def special_attack(self, player):
        """Boss's special attack (shockwave)"""
        print("Boss uses shockwave attack!")
        # This would create a shockwave that damages player if in range
    

class LootBox:
    def __init__(self, x, y, loot_type, bunny=None):  # Add bunny parameter
        self.x = x
        self.y = y
        self.loot_type = loot_type
        self.rect = pygame.Rect(
            x * Config.get('bun_size'), 
            y * Config.get('bun_size'), 
            Config.get('bun_size'), 
            Config.get('bun_size'))
        self.opened = False
        self.bunny = bunny  # Store bunny reference
    
    def update(self, bunny):
        """Check if the bunny interacts with the loot box"""
        if not self.opened and self.rect.colliderect(bunny.rect):
            self.bunny = bunny  # Ensure bunny reference is set
            self.open()
    
    def open(self):
        """Open the loot box and give items to the bunny"""
        if not self.opened and self.bunny:  # Check if bunny exists
            print(f"Bunny opened loot box with {self.loot_type}!")
            self.opened = True
            
            if self.loot_type == "health_potion":
                self.bunny.heal(50)
                self.bunny.inventory.show_notification("Health +50!", (0, 255, 0))
            elif self.loot_type == "coins":
                coins = random.randint(10, 50)
                self.bunny.money += coins
                self.bunny.inventory.show_notification(f"Found {coins} coins!", (255, 255, 0))
            elif self.loot_type == "boss":
                # Grant special boss loot
                dd = random.randint(1,3)
                self.bunny.inventory.items["boss_key"] = 1
                self.bunny.inventory.items["diamond"] = dd
                self.bunny.inventory.show_notification("You got the BOSS KEY!", (255, 215, 0))
                self.bunny.money += 100

    def give_health_potion(self):
        """Example loot: health potion"""
        # Add health potion to the bunny's inventory (or apply effect directly)
        pass
    
    def render(self, screen, camera_x, camera_y):
        """Render the loot box"""
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

