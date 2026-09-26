import pygame
import random

pygame.init()

WIDTH = 640
HEIGHT = 480
SIZE = 20

snake_color = (0, 200, 0)
map_color = (30, 30, 30)
line_color = (150, 150, 150)
food_color = (240, 0, 50)
sign_color = (255, 255, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

font_small = pygame.font.SysFont("sans", 20)
font_big = pygame.font.SysFont("sans", 45)

clock = pygame.time.Clock()

# =========================
# GAME STATE
# =========================

snake_pos = [[0, 0],[1, 0],[2, 0]]

snake_direction = "right"
next_direction = "right"

score = 0
pausing = False

food = [random.randint(0, WIDTH // SIZE - 1),random.randint(0, HEIGHT // SIZE - 1)]

# Snake moves every 1000/MOVE_DELAY moves/second
MOVE_DELAY = 120
last_move_time = pygame.time.get_ticks()

running = True

while running:

    # ==================================
    # 1. INPUT
    # ==================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            # Restart
            if event.key == pygame.K_SPACE and pausing:

                snake_pos = [[0, 0],[1, 0],[2, 0]]

                snake_direction = "right"
                next_direction = "right"

                score = 0
                pausing = False

                food = [
                    random.randint(0, WIDTH // SIZE - 1),
                    random.randint(0, HEIGHT // SIZE - 1)
                ]

                # Không để food nằm trên snake
                while food in snake_pos:
                    food = [
                        random.randint(0, WIDTH // SIZE - 1),
                        random.randint(0, HEIGHT // SIZE - 1)
                    ]

                last_move_time = pygame.time.get_ticks()

            # Chỉ nhận hướng mới khi game đang chạy
            if not pausing:

                if event.key == pygame.K_w:
                    if snake_direction != "down":
                        next_direction = "up"

                elif event.key == pygame.K_s:
                    if snake_direction != "up":
                        next_direction = "down"

                elif event.key == pygame.K_a:
                    if snake_direction != "right":
                        next_direction = "left"

                elif event.key == pygame.K_d:
                    if snake_direction != "left":
                        next_direction = "right"

    # ==================================
    # 2. UPDATE SNAKE
    # ==================================

    current_time = pygame.time.get_ticks()

    if not pausing and current_time - last_move_time >= MOVE_DELAY:

        # Chỉ đổi hướng đúng 1 lần mỗi movement tick
        snake_direction = next_direction

        # Lấy đầu hiện tại
        head_x = snake_pos[-1][0]
        head_y = snake_pos[-1][1]

        # Tạo đầu mới
        if snake_direction == "right":
            new_head = [head_x + 1, head_y]

        elif snake_direction == "left":
            new_head = [head_x - 1, head_y]

        elif snake_direction == "down":
            new_head = [head_x, head_y + 1]

        else:  # up
            new_head = [head_x, head_y - 1]

        # Kiểm tra ăn food
        eating = new_head == food

        # Thêm đầu mới
        snake_pos.append(new_head)

        # Nếu không ăn thì bỏ đuôi
        if not eating:
            snake_pos.pop(0)

        # Nếu ăn food
        if eating:

            score += 1

            food = [
                random.randint(0, WIDTH // SIZE - 1),
                random.randint(0, HEIGHT // SIZE - 1)
            ]

            # Không spawn food trong thân
            while food in snake_pos:
                food = [
                    random.randint(0, WIDTH // SIZE - 1),
                    random.randint(0, HEIGHT // SIZE - 1)
                ]

        # ==================================
        # CHECK WALL
        # ==================================

        head = snake_pos[-1]

        if (
            head[0] < 0
            or head[0] >= WIDTH // SIZE
            or head[1] < 0
            or head[1] >= HEIGHT // SIZE
        ):
            pausing = True

        # ==================================
        # CHECK BODY
        # ==================================

        if snake_pos[-1] in snake_pos[:-1]:
            pausing = True

        last_move_time = current_time

    # ==================================
    # 3. DRAW
    # ==================================

    screen.fill(map_color)

    # Draw grid
    # for i in range(HEIGHT // SIZE + 1):
    #     pygame.draw.line(
    #         screen,
    #         line_color,
    #         (0, i * SIZE),
    #         (WIDTH, i * SIZE)
    #     )

    # for i in range(WIDTH // SIZE + 1):
    #     pygame.draw.line(
    #         screen,
    #         line_color,
    #         (i * SIZE, 0),
    #         (i * SIZE, HEIGHT)
    #     )

    # Draw snake
    for part in snake_pos:
        pygame.draw.rect(
            screen,
            snake_color,
            (
                part[0] * SIZE,
                part[1] * SIZE,
                SIZE,
                SIZE
            )
        )

    # Draw food
    pygame.draw.rect(
        screen,
        food_color,
        (
            food[0] * SIZE,
            food[1] * SIZE,
            SIZE,
            SIZE
        )
    )

    # Score
    score_print = font_small.render(
        f"Score: {score}",
        True,
        sign_color
    )

    screen.blit(score_print, (0, 0))

    # ==================================
    # GAME OVER
    # ==================================

    if pausing:

        game_over_txt = font_big.render(
            f"GAME OVER, SCORE: {score}",
            True,
            sign_color
        )

        screen.blit(
            game_over_txt,
            (WIDTH // 6, HEIGHT // 3)
        )

        press_to_restart = font_big.render(
            "Press SPACE to restart",
            True,
            sign_color
        )

        screen.blit(
            press_to_restart,
            (WIDTH // 5, HEIGHT // 3 + 50)
        )

    pygame.display.flip()

    # Game render = 60 FPS
    clock.tick(60)

pygame.quit()