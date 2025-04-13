import pygame
import math
import random
import numpy as np
import os

# Initialize Pygame
pygame.init()

# Define constants for screen width and height
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Define colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Set up the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("AI Enemy with Q-Learning")

# Q-learning parameters
ALPHA = 0.1  # Learning rate
GAMMA = 0.9  # Discount factor
EPSILON = 0.2  # Exploration factor

# Possible actions
ACTIONS = ['move_towards', 'patrol']

# File to save/load the Q-table
Q_TABLE_FILE = "q_table.npy"

class Player:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
    
    def move(self, keys):
        if keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.y += self.speed

class Enemy:
    def __init__(self, x, y, size, speed, patrol_points):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.patrol_points = patrol_points
        self.patrol_index = 0
        self.state = "Patrolling"
        
        # Load Q-table from file, if it exists
        if os.path.exists(Q_TABLE_FILE):
            self.q_table = np.load(Q_TABLE_FILE)
        else:
            # Initialize Q-table if it doesn't exist
            self.q_table = np.zeros((100, len(ACTIONS)))  # Q-table: 100 states x 2 actions
    
    def move_towards_player(self, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance != 0:
            dx /= distance
            dy /= distance
        
        self.x += dx * self.speed
        self.y += dy * self.speed
    
    def move_patrol(self):
        target_x, target_y = self.patrol_points[self.patrol_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance != 0:
            dx /= distance
            dy /= distance
        
        self.x += dx * self.speed
        self.y += dy * self.speed
        
        if distance < 5:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
    
    def choose_action(self, state):
        # Exploration vs exploitation (epsilon-greedy)
        if random.uniform(0, 1) < EPSILON:
            return random.choice(ACTIONS)
        else:
            action_index = np.argmax(self.q_table[state])
            return ACTIONS[action_index]
    
    def update_q_value(self, state, action, reward, next_state):
        action_index = ACTIONS.index(action)
        best_next_action = np.argmax(self.q_table[next_state])
        current_q_value = self.q_table[state, action_index]
        future_q_value = self.q_table[next_state, best_next_action]
        
        # Q-learning update
        self.q_table[state, action_index] = current_q_value + ALPHA * (reward + GAMMA * future_q_value - current_q_value)
    
    def update(self, player_x, player_y):
        state = int(abs(self.x - player_x) // 50)  # Simplified state based on distance
        action = self.choose_action(state)
        
        # Distance from player
        distance = math.sqrt((self.x - player_x) ** 2 + (self.y - player_y) ** 2)
        
        if action == 'move_towards':
            self.move_towards_player(player_x, player_y)
            
            # Reward: +10 for getting closer, -10 for getting farther
            if distance < 100:  # Close range
                reward = 10
            elif distance > 200:  # Far range
                reward = -10
            else:
                reward = 1  # Small reward for movement towards player
        elif action == 'patrol':
            self.move_patrol()
            reward = 0  # No immediate reward for patrolling
        
        next_state = int(abs(self.x - player_x) // 50)  # Next state after the action
        self.update_q_value(state, action, reward, next_state)

    def save_q_table(self):
        # Save the Q-table to a file after each update
        np.save(Q_TABLE_FILE, self.q_table)

class Game:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 50, 5)
        self.enemy = Enemy(100, 100, 50, 3, [(100, 100), (700, 100), (700, 500), (100, 500)])
        self.running = True
        self.clock = pygame.time.Clock()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        keys = pygame.key.get_pressed()
        self.player.move(keys)
        self.enemy.update(self.player.x, self.player.y)

    def draw(self):
        screen.fill(WHITE)
        pygame.draw.rect(screen, BLUE, (self.player.x, self.player.y, self.player.size, self.player.size))
        pygame.draw.rect(screen, RED, (self.enemy.x, self.enemy.y, self.enemy.size, self.enemy.size))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            self.enemy.save_q_table()  # Save Q-table after each game loop

# Main program
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
