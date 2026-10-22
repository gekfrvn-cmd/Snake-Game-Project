import os

WIDTH = 1020
HEIGHT = 780
SIZE = 20

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BACKGROUND_IMAGES = (
    os.path.join(ASSET_DIR, "background.png"),
    os.path.join(ASSET_DIR, "background.jpg"),
    os.path.join(ASSET_DIR, "background.jpeg"),
)

FPS = 60
MOVE_DELAY = 120

# =========================
# COLORS
# =========================

SNAKE_COLOR = (0, 200, 0)
MAP_COLOR = (30, 30, 30)
BACKGROUND_TILE_A = (232, 199, 157)
BACKGROUND_TILE_B = (226, 190, 146)
GRID_COLOR = (107, 77, 49)
SNAKE_OUTLINE = (0, 115, 35)
SNAKE_HEAD_COLOR = (34, 211, 78)
FOOD_COLOR = (240, 0, 50)
EFFECT_COLOR=(255,10,100)
GAMBLING_COLOR=(20,255,60)
SIGN_COLOR = (255, 255, 255)
TERRAIN_COLOR = (242, 67, 32)
TERRAIN_OUTLINE = (22, 18, 16)
