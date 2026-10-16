# =========================
# CẤU HÌNH CHUNG
# =========================
#
# GAME NAY DUOC VE O "DO PHAN GIAI PIXEL": toan bo canvas la 510 x 390 diem anh,
# moi o luoi = 10 x 10 diem anh. pygame.SCALED se phong to canvas len cua so
# (nguyen lan, khong lam mo) => pixel art sac net nhu game indie that su.
# So o luoi van la 51 x 39 nhu ban cu, nen luat choi khong doi.

WIDTH = 510
HEIGHT = 390
SIZE = 10                 # 1 o luoi = 10 diem anh
COLS = WIDTH // SIZE      # 51
ROWS = HEIGHT // SIZE     # 39

FPS = 60
MOVE_DELAY = 120          # giữ lại để tương thích code cũ

GAME_TITLE = "SNAKE"
VERSION = "3.0"
AUTHOR_NAME = "Tên của bạn"   # <- sửa tên bạn ở đây (hiện trong màn hình Credit)

# Độ khó: thời gian giữa 2 bước đi (ms), càng nhỏ rắn càng nhanh
DIFFICULTY_NAMES = ["Dễ", "Thường", "Khó"]
DIFFICULTY_DELAY = [160, 120, 85]

# =========================
# BẢNG MÀU (ngục tối + lửa + tế bào)
# =========================

INK = (10, 8, 18)             # đen mực dùng làm viền cho mọi thứ
STONE_0 = (18, 16, 30)
STONE_1 = (30, 27, 46)
STONE_2 = (46, 42, 66)
STONE_3 = (70, 64, 94)
STONE_4 = (104, 96, 128)

GOLD = (240, 196, 96)
EMBER = (255, 140, 56)
CELL = (110, 220, 255)
TEAL = (84, 224, 176)
BLOOD = (214, 52, 66)

# Tên màu giao diện (giữ tên cũ cho dễ đọc code)
ACCENT = GOLD
TEXT = (236, 228, 214)
TEXT_DIM = (140, 130, 158)
GOOD = (112, 240, 150)
BAD = (240, 84, 84)
WARN = (255, 200, 90)
INFO = (120, 190, 255)

# Màu cũ (giữ để tương thích)
SNAKE_COLOR = (0, 200, 0)
MAP_COLOR = (30, 30, 30)
LINE_COLOR = (150, 150, 150)
FOOD_COLOR = (240, 0, 50)
EFFECT_COLOR = (255, 10, 100)
GAMBLING_COLOR = (20, 255, 60)
SIGN_COLOR = (255, 255, 255)
TERRAIN_COLOR = (122, 59, 18)

# Màu rắn (skin). tail -> body: dải màu thân; belly: hoa văn vảy; light: điểm sáng; head: đầu
SKINS = [
    {"name": "Lá xanh", "tail": (18, 84, 70), "body": (52, 196, 110), "belly": (150, 230, 120),
     "light": (200, 255, 180), "head": (120, 240, 150), "glow": (90, 255, 160)},
    {"name": "Đại dương", "tail": (24, 50, 130), "body": (52, 140, 240), "belly": (130, 210, 255),
     "light": (210, 240, 255), "head": (120, 200, 255), "glow": (100, 190, 255)},
    {"name": "Tím mộng mơ", "tail": (56, 26, 118), "body": (150, 84, 240), "belly": (214, 160, 255),
     "light": (240, 214, 255), "head": (206, 150, 255), "glow": (190, 120, 255)},
    {"name": "Cam lửa", "tail": (130, 36, 24), "body": (240, 130, 36), "belly": (255, 206, 110),
     "light": (255, 236, 170), "head": (255, 190, 90), "glow": (255, 150, 60)},
    {"name": "Cầu vồng", "tail": (255, 255, 255), "body": (255, 255, 255), "belly": (255, 255, 255),
     "light": (255, 255, 255), "head": (255, 255, 255), "glow": (255, 255, 255), "rainbow": True},
    {"name": "Lửa ma", "tail": (28, 22, 40), "body": (74, 58, 92), "belly": (120, 96, 130),
     "light": (170, 150, 180), "head": (40, 34, 52), "glow": (255, 150, 50), "ember": True},
    {"name": "Tế bào", "tail": (14, 62, 92), "body": (40, 164, 204), "belly": (130, 232, 255),
     "light": (230, 255, 255), "head": (170, 250, 255), "glow": (110, 220, 255)},
]

# Khu vực (đổi theo cấp, mỗi khu có màu ánh sáng riêng giống các biome của Dead Cells)
BIOMES = [
    {"name": "NGỤC TÙ", "ambient": (150, 148, 196), "torch": (255, 150, 70), "dust": (190, 180, 210)},
    {"name": "CỐNG ĐỘC", "ambient": (118, 176, 140), "torch": (160, 255, 110), "dust": (160, 210, 140)},
    {"name": "THÀNH LŨY", "ambient": (118, 150, 214), "torch": (120, 205, 255), "dust": (190, 215, 245)},
    {"name": "HẦM MỘ", "ambient": (176, 118, 164), "torch": (255, 100, 170), "dust": (230, 160, 205)},
    {"name": "ĐỈNH THÁP", "ambient": (190, 170, 120), "torch": (255, 214, 110), "dust": (245, 225, 170)},
]


def biome_for_level(level):
    return min(len(BIOMES) - 1, max(0, (level - 1) // 3))
