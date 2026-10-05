import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    TERRAIN_COLOR
)

class Terrain:

    def __init__(self):
        self.wall = list()

        walls = [
            (7,8,10,30),
            (18,8,21,30),
            (29,8,32,30),
            (40,8,43,30)
        ]

        for x1,y1,x2,y2 in walls:
            for x in range(x1,x2+1):
                for y in range(y1,y2):
                    self.wall.append([x,y])

    def draw(self,screen):
        for x,y in self.wall:
            pygame.draw.rect(
                screen,
                TERRAIN_COLOR,
                (x*SIZE,y*SIZE,SIZE,SIZE)
            )                

    def hit_wall(self,x):
        if x in self.wall:
            return True
        return False
    
