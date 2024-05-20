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
