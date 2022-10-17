from dataclasses import  dataclass
import pygame

@dataclass
class GameComponent:

    x: int
    y: int

    def draw(self, surface):
        # pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(self.x, self.y, 8, 8))
        return False