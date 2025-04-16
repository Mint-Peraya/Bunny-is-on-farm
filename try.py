import pygame

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, image, name):
        super().__init__()
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.name = name

class Inventory:
    def __init__(self, capacity=5):
        self.capacity = capacity
        self.items = []

    def is_full(self):
        return len(self.items) >= self.capacity

    def add_item(self, item):
        if not self.is_full():
            self.items.append(item)
            return True
        return False

    def draw(self, screen):
        slot_size = 64
        padding = 10
        start_x = (screen.get_width() - (slot_size + padding) * self.capacity) // 2
        y = screen.get_height() - slot_size - 10

        for i in range(self.capacity):
            rect = pygame.Rect(start_x + i * (slot_size + padding), y, slot_size, slot_size)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2)

            if i < len(self.items):
                item_img = pygame.transform.scale(self.items[i].image, (slot_size - 10, slot_size - 10))
                screen.blit(item_img, (rect.x + 5, rect.y + 5))
