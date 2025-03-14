import pygame
import random
import sys
import math
from bunny import Frame

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600  # Screen size
CELL_SIZE = 64  # Each cell is 64x64 pixels
MAZE_WIDTH, MAZE_HEIGHT = 50 * CELL_SIZE, 50 * CELL_SIZE  # Maze size (12x9 grid)
ROWS, COLS = MAZE_HEIGHT // CELL_SIZE, MAZE_WIDTH // CELL_SIZE  # Grid size

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)

# Directions for maze carving (right, down, left, up)
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]  # 1 means wall
        self.generate_maze(1, 1)  # Start generating from (1, 1) to leave outer walls intact
        self.add_loops(10)  # Add loops to make the maze more complex
    
    def generate_maze(self, x, y):
        """Generate a maze using recursive backtracking."""
        self.grid[y][x] = 0  # Mark the starting point as a path (0)
        directions = DIRECTIONS.copy()
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 1:
                self.grid[y + dy][x + dx] = 0  # Create a passage to the new cell
                self.generate_maze(nx, ny)  # Recursively generate from the new position

    def add_loops(self, num_loops):
        """Add loops to the maze by randomly removing walls."""
        for _ in range(num_loops):
            x = random.randint(1, self.cols - 2)
            y = random.randint(1, self.rows - 2)
            if self.grid[y][x] == 1:  # Only remove walls
                self.grid[y][x] = 0

    def draw(self, screen, camera_x, camera_y):
        """Draw the maze on the screen with camera offset."""
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == 1:  # 1 means wall
                    pygame.draw.rect(screen, BLACK, (x * CELL_SIZE - camera_x, y * CELL_SIZE - camera_y, CELL_SIZE, CELL_SIZE))
                else:  # 0 means path
                    pygame.draw.rect(screen, WHITE, (x * CELL_SIZE - camera_x, y * CELL_SIZE - camera_y, CELL_SIZE, CELL_SIZE))

class Bunny:
    def __init__(self, x, y):
        self.x = x  # Grid position (column)
        self.y = y  # Grid position (row)
        self.normal_speed = 0.1  # Base speed (fraction of a cell per frame)
        self.speed = self.normal_speed
        self.target_x = x  # Target position for smooth movement
        self.target_y = y
        self.health = 100
        self.rect = pygame.Rect(self.x * CELL_SIZE, self.y * CELL_SIZE, CELL_SIZE, CELL_SIZE)  # Collision detection
        self.attack_cooldown = 0  

        # Speed Boost Variables
        self.speed_boost_active = False
        self.speed_boost_start_time = 0
        self.speed_boost_duration = 5000  # 5 seconds (5000 ms)

        # Cooldown Variables
        self.speed_boost_cooldown = False
        self.speed_boost_cooldown_time = 3000  # 3 seconds (3000 ms)
        self.speed_boost_cooldown_start = 0

        # Load sprite sheets
        self.front_sheet = Frame(pygame.image.load('BunnyWalk-Sheet.png').convert_alpha())
        self.back_sheet = Frame(pygame.image.load('BunnyWalkBack-Sheet.png').convert_alpha())
        self.right_sheet = Frame(pygame.image.load('BunnyWalkright-Sheet.png').convert_alpha())
        self.left_sheet = Frame(pygame.image.load('BunnyWalkleft-Sheet.png').convert_alpha())

        self.frames_front = [self.front_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_back = [self.back_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)]
        self.frames_right = [self.right_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]
        self.frames_left = [self.left_sheet.get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)]

        self.current_direction = 'front'
        self.current_frame = 0
        self.frame_time = 100  # Time between animation frames (in milliseconds)
        self.last_update_time = pygame.time.get_ticks()

    def move(self, keys, maze):
        """Update bunny's position based on key presses and maze walls."""
        moving = False
        current_time = pygame.time.get_ticks()
        new_direction = self.current_direction  # Track if direction changes

        # Handle Speed Boost Cooldown
        if self.speed_boost_cooldown and current_time - self.speed_boost_cooldown_start >= self.speed_boost_cooldown_time:
            self.speed_boost_cooldown = False

        if keys[pygame.K_f] and not self.speed_boost_active and not self.speed_boost_cooldown:
            self.speed_boost_active = True
            self.speed_boost_start_time = current_time
            self.speed = self.normal_speed * 2  

        if self.speed_boost_active and current_time - self.speed_boost_start_time >= self.speed_boost_duration:
            self.speed_boost_active = False
            self.speed = self.normal_speed  
            self.speed_boost_cooldown = True  
            self.speed_boost_cooldown_start = current_time  

        # Movement & Direction Change Detection
        if self.x == self.target_x and self.y == self.target_y:  # Only move if bunny has reached the target
            if keys[pygame.K_LEFT]:
                new_x = self.x - 1
                if 0 <= new_x < COLS and maze.grid[self.y][new_x] == 0:
                    self.target_x = new_x
                    new_direction = 'left'
                    moving = True
            elif keys[pygame.K_RIGHT]:
                new_x = self.x + 1
                if 0 <= new_x < COLS and maze.grid[self.y][new_x] == 0:
                    self.target_x = new_x
                    new_direction = 'right'
                    moving = True
            elif keys[pygame.K_UP]:
                new_y = self.y - 1
                if 0 <= new_y < ROWS and maze.grid[new_y][self.x] == 0:
                    self.target_y = new_y
                    new_direction = 'back'
                    moving = True
            elif keys[pygame.K_DOWN]:
                new_y = self.y + 1
                if 0 <= new_y < ROWS and maze.grid[new_y][self.x] == 0:
                    self.target_y = new_y
                    new_direction = 'front'
                    moving = True

        # Smoothly move towards the target position
        if self.x < self.target_x:
            self.x = min(self.x + self.speed, self.target_x)
        elif self.x > self.target_x:
            self.x = max(self.x - self.speed, self.target_x)
        if self.y < self.target_y:
            self.y = min(self.y + self.speed, self.target_y)
        elif self.y > self.target_y:
            self.y = max(self.y - self.speed, self.target_y)

        # If direction changed, reset animation frame
        if new_direction != self.current_direction:
            self.current_direction = new_direction
            self.current_frame = 0  # Reset frame to avoid out-of-range issues

        self.rect.topleft = (self.x * CELL_SIZE, self.y * CELL_SIZE)
        return moving

    def draw(self, screen, camera_x, camera_y):
        """Draw the bunny's current frame on the screen."""
        # Draw the current frame based on direction
        frame_dict = {
            'front': self.frames_front,
            'left': self.frames_left,
            'right': self.frames_right,
            'back': self.frames_back
        }

        # Ensure current_frame is within bounds
        frames = frame_dict.get(self.current_direction, [])
        if frames:
            self.current_frame = self.current_frame % len(frames)  # Prevent IndexError
            screen.blit(frames[self.current_frame], (self.x * CELL_SIZE - camera_x, self.y * CELL_SIZE - camera_y))

        # Draw health bar
        self.draw_health_bar(screen, camera_x, camera_y)

    def draw_health_bar(self, screen, camera_x, camera_y):
        """Draw the bunny's health bar on the screen."""
        pygame.draw.rect(screen, (255, 0, 0), (self.x * CELL_SIZE - camera_x + 8, self.y * CELL_SIZE - camera_y - 10, 50, 5))  # Red health bar background
        pygame.draw.rect(screen, (0, 255, 0), (self.x * CELL_SIZE - camera_x + 8, self.y * CELL_SIZE - camera_y - 10, self.health / 2, 5))  # Green health bar

    def update_animation(self, moving):
        """Update the frame if moving."""
        current_time = pygame.time.get_ticks()
        
        if moving and current_time - self.last_update_time > self.frame_time:
            frame_dict = {
                'front': self.frames_front,
                'left': self.frames_left,
                'right': self.frames_right,
                'back': self.frames_back
            }
            
            if self.current_direction in frame_dict:
                frames = frame_dict[self.current_direction]
                if frames:
                    self.current_frame = (self.current_frame + 1) % len(frames)  # Prevent IndexError
            
            self.last_update_time = current_time  # Update time

def get_random_exit(maze, bunny_x, bunny_y, min_distance=20):
    """Get a random exit position that is at least `min_distance` cells away from the bunny."""
    while True:
        exit_x, exit_y = random.randint(1, COLS - 2), random.randint(1, ROWS - 2)
        if maze.grid[exit_y][exit_x] == 0:  # Ensure exit is on a path
            distance = abs(exit_x - bunny_x) + abs(exit_y - bunny_y)  # Manhattan distance
            if distance >= min_distance:
                return exit_x, exit_y

def draw_text(screen, text, font_size, color, position):
    font = pygame.font.SysFont(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)

def draw_compass(screen, bunny, exit_x, exit_y, camera_x, camera_y):
    """Draw a compass pointing from the bunny to the exit."""
    # Calculate the angle between the bunny and the exit
    dx = exit_x - bunny.x
    dy = exit_y - bunny.y
    angle = math.atan2(dy, dx)  # Angle in radians

    # Compass position (top-right corner of the screen)
    compass_x = SCREEN_WIDTH - 100
    compass_y = 50
    compass_radius = 40

    # Draw compass circle
    pygame.draw.circle(screen, WHITE, (compass_x, compass_y), compass_radius, 2)

    # Calculate the end point of the arrow
    arrow_length = compass_radius - 10
    arrow_end_x = compass_x + arrow_length * math.cos(angle)
    arrow_end_y = compass_y + arrow_length * math.sin(angle)

    # Draw the arrow
    pygame.draw.line(screen, RED, (compass_x, compass_y), (arrow_end_x, arrow_end_y), 3)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    maze = Maze(ROWS, COLS)
    bunny = Bunny(1, 1)  # Start bunny inside the maze, not on the wall
    exit_x, exit_y = get_random_exit(maze, bunny.x, bunny.y, min_distance=5)  # Ensure exit is far from bunny

    running = True
    game_over = False

    # Camera offset
    camera_x, camera_y = 0, 0
    camera_speed = 0.1  # Speed of camera movement

    while running:
        screen.fill((0,0,0))  # Fill the background with black

        # Smoothly move the camera towards the bunny's position
        camera_x += (bunny.x * CELL_SIZE - SCREEN_WIDTH // 2 - camera_x) * camera_speed
        camera_y += (bunny.y * CELL_SIZE - SCREEN_HEIGHT // 2 - camera_y) * camera_speed

        # Draw maze with camera offset
        maze.draw(screen, camera_x, camera_y)
        bunny.draw(screen, camera_x, camera_y)
        
        # Draw start and exit
        pygame.draw.rect(screen, GREEN, (1 * CELL_SIZE - camera_x, 1 * CELL_SIZE - camera_y, CELL_SIZE, CELL_SIZE))  # Start portal
        pygame.draw.rect(screen, BROWN, (exit_x * CELL_SIZE - camera_x, exit_y * CELL_SIZE - camera_y, CELL_SIZE, CELL_SIZE))  # Exit
        pygame.draw.rect(screen, GREEN, (exit_x * CELL_SIZE - camera_x, exit_y * CELL_SIZE - camera_y, CELL_SIZE, CELL_SIZE), 3)  # End portal
        
        # Draw compass
        draw_compass(screen, bunny, exit_x, exit_y, camera_x, camera_y)
        
        # If the bunny has reached the exit
        if bunny.x == exit_x and bunny.y == exit_y:
            game_over = True
            draw_text(screen, "You Win!", 55, GREEN, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 30))
            pygame.display.flip()
            pygame.time.wait(2000)  # Wait for 2 seconds before restarting the game
            maze = Maze(ROWS, COLS)  # Regenerate maze
            bunny = Bunny(1, 1)  # Reset bunny
            exit_x, exit_y = get_random_exit(maze, bunny.x, bunny.y, min_distance=5)  # Get a new exit position
            game_over = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_r:  # Restart the game
                    maze = Maze(ROWS, COLS)
                    bunny = Bunny(1, 1)
                    exit_x, exit_y = get_random_exit(maze, bunny.x, bunny.y, min_distance=5)
        
        # Get key presses
        keys = pygame.key.get_pressed()
        moving = bunny.move(keys, maze)
        bunny.update_animation(moving)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()