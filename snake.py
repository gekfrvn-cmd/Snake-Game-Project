import pygame

from settings import (
    WIDTH,
    HEIGHT,
    SIZE,
    SNAKE_COLOR,
    SNAKE_OUTLINE,
    SNAKE_HEAD_COLOR
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
        # Thân gồm các ô vuông có viền riêng để vẫn thấy từng đốt khi uốn lượn.
        for part in self.pos[:-1]:
            rect = pygame.Rect(part[0] * SIZE, part[1] * SIZE, SIZE, SIZE)
            pygame.draw.rect(screen, SNAKE_OUTLINE, rect)
            pygame.draw.rect(screen, SNAKE_COLOR, rect.inflate(-3, -3))

        # Đầu vuông sáng hơn thân, có mắt chỉ theo hướng di chuyển.
        head = self.pos[-1]
        rect = pygame.Rect(head[0] * SIZE, head[1] * SIZE, SIZE, SIZE)
        pygame.draw.rect(screen, SNAKE_OUTLINE, rect)
        pygame.draw.rect(screen, SNAKE_HEAD_COLOR, rect.inflate(-3, -3))

        x, y = rect.center
        offset = SIZE // 4
        if self.direction == "right":
            eyes = [(x + offset, y - offset), (x + offset, y + offset)]
        elif self.direction == "left":
            eyes = [(x - offset, y - offset), (x - offset, y + offset)]
        elif self.direction == "up":
            eyes = [(x - offset, y - offset), (x + offset, y - offset)]
        else:
            eyes = [(x - offset, y + offset), (x + offset, y + offset)]
        for eye in eyes:
            pygame.draw.rect(screen, (15, 30, 18), (eye[0] - 1, eye[1] - 1, 3, 3))
