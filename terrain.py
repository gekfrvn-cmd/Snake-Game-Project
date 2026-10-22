import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    TERRAIN_COLOR,
    TERRAIN_OUTLINE
)


class Terrain:

    def __init__(self, enabled=True):
        self.wall = list()

        # Giữ nguyên bố cục terrain ban đầu, chỉ đổi kiểu hiển thị từng ô.
        walls = [
            (7, 8, 10, 30),
            (18, 8, 21, 30),
            (29, 8, 32, 30),
            (40, 8, 43, 30)
        ]

        # enabled=False (tắt "Tường" trong Cài đặt) -> không có tường nào.
        if enabled:
            for x1, y1, x2, y2 in walls:
                for x in range(x1, x2 + 1):
                    for y in range(y1, y2):
                        self.wall.append([x, y])

        self._wall_set = {tuple(cell) for cell in self.wall}
        self._surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x, y in self.wall:
            outer = pygame.Rect(x * SIZE, y * SIZE, SIZE, SIZE)
            pygame.draw.rect(self._surface, TERRAIN_OUTLINE, outer)
            pygame.draw.rect(self._surface, TERRAIN_COLOR, outer.inflate(-6, -6))

    def draw(self, screen):
        screen.blit(self._surface, (0, 0))

    def hit_wall(self, x):
        return tuple(x) in self._wall_set
