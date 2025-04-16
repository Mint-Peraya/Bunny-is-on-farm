import pygame
import math
from config import *

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

import pygame

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

import math  # Added missing import
from config import *

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


