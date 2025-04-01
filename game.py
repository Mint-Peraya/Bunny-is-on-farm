import pygame
from config import Config
from login import *

class Game:
    def __init__(self):
        pygame.init()
        login = AuthSystem()
        login.run()

Game()
        


