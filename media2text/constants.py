"""Module containing query_font constants"""

from sys import platform

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

match platform:
    case "win32":
        SYSTEM_FONT_PATH = "C:/Windows/Fonts/"
    case "linux" | "linux2":
        SYSTEM_FONT_PATH = "/usr/share/fonts/"
    case "darwin":
        SYSTEM_FONT_PATH = "/Library/Fonts/"
    case _:
        SYSTEM_FONT_PATH = ""

LOOKUP_TYPE_LIGATURE = 4

RENDER_TEMP_DIR = "render_temp"
PROCESS_REFRESH_RATE = 0.1  # seconds

TEXT_IMAGE_MAGIC_NUMBER = 157450653
TEXT_VIDEO_MAGIC_NUMBER = 94987465

BYTE_ORDER = "big"
INT_SIZE = 4
