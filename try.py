import pygame
from config import Config

class Bunny:
    def __init__(self, x, y, mode="farming"):
        """Initialize Bunny with a position and default mode."""
        self.x, self.y = x, y
        self.mode = mode  # Modes: "maze", "farming", "dungeon"
        self.health = 100
        self.attack_power = 10
        self.speed = 0.1
        self.target_x, self.target_y = x, y

    def load_bunny(self):
        """Load all sprite sheets."""
        self.sheet = Config.get("bun_sheet")
        self.frames = {
            "front": [self.sheet["front_sheet"].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)],
            "back": [self.sheet["back_sheet"].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(5)],
            "left": [self.sheet["left_sheet"].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)],
            "right": [self.sheet["right_sheet"].get_image(i, 32, 32, 2, (0, 0, 0)) for i in range(8)],
            "front_damage": [self.sheet["front_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "back_damage": [self.sheet["back_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(5)],
            "left_damage": [self.sheet["left_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
            "right_damage": [self.sheet["right_damage_sheet"].get_image(i, 32, 32, 1, (0, 0, 0)) for i in range(8)],
        }
    
    def 
