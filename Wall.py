from dataclasses import dataclass
import pygame

@dataclass
class Wall:
    x: int
    y: int

    def __hash__(self) -> int:
        return hash((self.x, self.y))


    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y


    def draw(self,surface):
        pygame.draw.rect(surface, (84, 84, 84), pygame.Rect(self.x, self.y, 8, 8))
        return True

