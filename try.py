import pygame
import sys
from config import Config

class Scene:
    def __init__(self,screen,clock,story_text, font, font_size, typing_speed=0.03):
        self.screen = screen
        self.clock = clock
        self.story = story_text
        self.speed = typing_speed
        self.displayed_text = ""
        self.text_index = 0
        self.timer = 0
        self.done_typing = False

        self.font = pygame.font.Font(font, font_size)
        self.littlefont = pygame.font.Font(font, font_size-5)
        self.run()
    
    def run(self):
        
        press_text = self.littlefont.render("-Press Space to continue-", True, (200, 200, 200))
        press_rect = press_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 50))
        
        while True:
            dt = self.clock.tick(60) / 1000  # Time passed in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.done_typing and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return  # Exit story screen

            # Typing effect
            if not self.done_typing:
                self.timer += dt
                if self.timer >= self.speed and self.text_index < len(self.story):
                    self.displayed_text += self.story[self.text_index]
                    self.text_index += 1
                    self.timer = 0
                if self.text_index == len(self.story):
                    self.done_typing = True

            # Drawing
            screen.fill((0,0,0))
            
            wrapped_lines = self.wrap_text(self.displayed_text, screen.get_width() - 100)
            for i, line in enumerate(wrapped_lines):
                line_surface = self.font.render(line, True, (255, 255, 255))
                screen.blit(line_surface, (50, 200 + i * 40))

            if self.done_typing:
                screen.blit(press_text, press_rect)

            pygame.display.flip()

        
    def wrap_text(self,text, max_width):
        """Helper function to wrap long text lines within max_width."""
        words = text.split(" ")
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        if current_line:
            lines.append(current_line)
        return lines


pygame.init()
screen = pygame.display.set_mode((800, 600))
font = "assets/fonts/pixel.ttf"
font_size = 32

story = "  A long time ago, in a peaceful valley far away, you inherited a piece of land where your new farming journey begins."

s = Scene(screen,pygame.time.Clock(),story,font,font_size)