from sys import platform


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

if platform == "win32":
    SYSTEM_FONT_PATH = "C:/Windows/Fonts/"
elif platform in ("linux", "linux2"):
    SYSTEM_FONT_PATH = "/usr/share/fonts/"
elif platform == "darwin":
    SYSTEM_FONT_PATH = "/Library/Fonts/"
else:
    SYSTEM_FONT_PATH = ""
