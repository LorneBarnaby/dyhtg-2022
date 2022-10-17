from dataclasses import dataclass
import pygame

@dataclass
class FloorTile:

    x: int
    y: int
    _visited: bool


    def __hash__(self) -> int:
        return hash((self.x, self.y))


    def __eq__(self, __o: object) -> bool:
        return self.x == __o.x and self.y == __o.y

    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, v):
        self._visited = v

    def draw(self,surface):
        if not self.visited:
            pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(self.x, self.y, 8, 8))
        else:
            pygame.draw.rect(surface, (255, 0, 0), pygame.Rect(self.x, self.y, 8, 8))
        return True