import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    SNAKE_COLOR
)


class Snake:

    def __init__(self):

        self.reset()

    # =========================
    # RESET
    # =========================

    def reset(self):

        self.pos = [
            [0, 0],
            [1, 0],
            [2, 0]
        ]

        self.direction = "right"
        self.next_direction = "right"

    # =========================
    # CHANGE DIRECTION
    # =========================

    def change_direction(self, direction):

        if direction == "up":

            if self.direction != "down":
                self.next_direction = "up"

        elif direction == "down":

            if self.direction != "up":
                self.next_direction = "down"

        elif direction == "left":

            if self.direction != "right":
                self.next_direction = "left"

        elif direction == "right":

            if self.direction != "left":
                self.next_direction = "right"

    # =========================
    # GET NEW HEAD
    # =========================

    def get_new_head(self):

        head_x = self.pos[-1][0]
        head_y = self.pos[-1][1]

        if self.direction == "right":
            if head_x>=WIDTH//SIZE-1:
                return [0,head_y]
            return [head_x + 1, head_y]

        elif self.direction == "left":
            if head_x<=0:
                return [WIDTH//SIZE-1,head_y]
            return [head_x - 1, head_y]

        elif self.direction == "down":
            if head_y>=HEIGHT//SIZE-1:
                return [head_x,0]
            return [head_x, head_y + 1]

        else:
            if head_y<=0:
                return [head_x,HEIGHT//SIZE-1]
            return [head_x, head_y - 1]

    # =========================
    # MOVE
    # =========================

    def move(self,grow=False,type=""):

        # Commit hướng mới
        self.direction = self.next_direction

        new_head = self.get_new_head()

        # Thêm đầu mới
        self.pos.append(new_head)

        # Nếu không ăn food thì bỏ đuôi
        if grow==False or type!="apple":
            self.pos.pop(0)

    # =========================
    # CHECK BODY COLLISION
    # =========================

    def hit_body(self):

        head = self.pos[-1]

        return head in self.pos[:-1]

    # =========================
    # DRAW
    # =========================

    def draw(self, screen):

        for part in self.pos:

            pygame.draw.rect(
                screen,
                SNAKE_COLOR,
                (
                    part[0] * SIZE,
                    part[1] * SIZE,
                    SIZE,
                    SIZE
                )
            )