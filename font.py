"""Module containing the Font class."""
import numpy as np
import pygame
import pygame.freetype
from scipy.spatial import KDTree

from consts import UNICODE_CHAR_BYTES, INT_BYTES, BOOL_BYTES, BYTE_ORDER


class Font:
    """
    Class representing font, tailored specifically for this project.
    Contains a dictionary of characters and their rendered surfaces
    and a KDTree of the average colors of the characters for fast lookup.
    """

    def __init__(
        self,
        font_name: str,
        font_size: int | str,
        bold,
        italic,
        char_set: set[int],
    ):
        if isinstance(font_size, str):
            try:
                font_size = int(font_size)
            except ValueError as e:
                raise ValueError(
                    "Font size must be an integer greater than or equal to 1"
                ) from e
        if font_size < 1:
            raise ValueError("Font size must be greater than or equal to 1")
        self.name = font_name
        self.font_size = font_size
        self.char_dict = {char_index: None for char_index in char_set}
        self.font = pygame.font.SysFont(font_name, font_size, bold, italic)
        self.kd_tree_index_map = []
        self.kd_tree = None
        freetype_font = pygame.freetype.SysFont(font_name, font_size, bold, italic)
        if not Font.name_exists(font_name):
            raise ValueError("Font with given name not found")
        max_width = max_height = 0
        # going through all the characters
        # and checking if they are printable and supported by the font
        for char in map(chr, list(self.char_dict.keys())):
            if not char.isprintable():
                self.char_dict.pop(ord(char))
                continue
            char_width, char_height = self.font.size(char)
            if freetype_font.get_metrics(char)[0] is None or char_width == 0:
                self.char_dict.pop(ord(char))
                continue
            max_width = max(max_width, char_width)
            max_height = max(max_height, char_height)
        self.size = (max_width, max_height)
        if len(self.char_dict) < 2:
            raise ValueError(
                "Not enough printable/font-supported characters in char set"
            )
        # rendering all the characters and calculating their average color
        try:
            char_averages = np.empty((len(self.char_dict), 3), dtype=np.float64)
            for i, char in enumerate(map(chr, sorted(list(self.char_dict.keys())))):
                char_surface = pygame.Surface(self.size)
                char_surface.fill((0, 0, 0))
                char_render = self.font.render(char, True, (255, 255, 255))
                center = (
                    (self.width() - char_render.get_size()[0]) // 2,
                    (self.height() - char_render.get_size()[1]) // 2,
                )
                char_surface.blit(char_render, center)
                rendered_char = char_surface.convert_alpha().premul_alpha().convert()
                average = np.array(
                    [
                        np.average(pygame.surfarray.pixels_red(rendered_char)),
                        np.average(pygame.surfarray.pixels_green(rendered_char)),
                        np.average(pygame.surfarray.pixels_blue(rendered_char)),
                    ]
                )
                char_averages[i][:] = average
                self.char_dict[ord(char)] = rendered_char
            # normalizing the average colors and creating a KDTree for them
            char_averages /= np.max(char_averages[:], axis=0)
            for i, char in enumerate(map(chr, sorted(list(self.char_dict.keys())))):
                self.kd_tree_index_map.append(ord(char))
            self.kd_tree = KDTree(char_averages, copy_data=True)
        except pygame.error as e:
            raise ValueError("Could not load font") from e

    def aspect_ratio(self) -> float:
        """Returns the aspect ratio of the font."""
        return self.size[0] / self.size[1]

    def width(self) -> int:
        """Returns the width of the font."""
        return self.size[0]

    def height(self) -> int:
        """Returns the height of the font."""
        return self.size[1]

    def get_closest_chars(self, image: np.array) -> list:
        """Returns a list of the closest characters to the given image."""
        return [
            [self.kd_tree_index_map[i] for i in row]
            for row in self.kd_tree.query(image / 255, p=2)[1]
        ]

    def get_rendered_char(self, char_index: int) -> pygame.Surface:
        """Returns a pygame.Surface of given character index."""
        return self.char_dict[char_index]

    def to_bytes(self) -> bytes:
        """
        Returns the font data as bytes.
        Only contains the minimum amount of data needed to recreate the font.
        """
        font_bytes = b""
        # font_name_bytes_length
        font_name_bytes = self.name.encode()
        font_bytes += len(font_name_bytes).to_bytes(INT_BYTES, byteorder=BYTE_ORDER)
        # font_name_bytes
        font_bytes += font_name_bytes
        # font_size
        font_bytes += self.font_size.to_bytes(INT_BYTES, byteorder=BYTE_ORDER)
        # bold
        font_bytes += self.font.get_bold().to_bytes(BOOL_BYTES, byteorder=BYTE_ORDER)
        # italic
        font_bytes += self.font.get_italic().to_bytes(BOOL_BYTES, byteorder=BYTE_ORDER)
        # char_set_length
        font_bytes += len(self.char_dict.keys()).to_bytes(
            INT_BYTES, byteorder=BYTE_ORDER
        )
        # char_set_bytes
        char_set_bytes = b""
        for char_index in self.char_dict.keys():
            char_set_bytes += char_index.to_bytes(
                UNICODE_CHAR_BYTES, byteorder=BYTE_ORDER
            )
        font_bytes += char_set_bytes
        return font_bytes

    @staticmethod
    def from_bytes(data: bytes) -> "Font":
        """Returns a Font object from the given bytes."""
        font_name_bytes_length = int.from_bytes(data[:INT_BYTES], byteorder=BYTE_ORDER)
        byte_pointer = INT_BYTES
        font_name = data[byte_pointer : byte_pointer + font_name_bytes_length].decode()
        byte_pointer += font_name_bytes_length
        font_size = int.from_bytes(
            data[byte_pointer : byte_pointer + INT_BYTES], byteorder=BYTE_ORDER
        )
        byte_pointer += INT_BYTES
        bold = bool.from_bytes(
            data[byte_pointer : byte_pointer + BOOL_BYTES], byteorder=BYTE_ORDER
        )
        byte_pointer += BOOL_BYTES
        italic = bool.from_bytes(
            data[byte_pointer : byte_pointer + BOOL_BYTES], byteorder=BYTE_ORDER
        )
        byte_pointer += BOOL_BYTES
        char_set_length = int.from_bytes(
            data[byte_pointer : byte_pointer + INT_BYTES], byteorder=BYTE_ORDER
        )
        byte_pointer += INT_BYTES
        char_set = set(
            int.from_bytes(
                data[
                    byte_pointer
                    + UNICODE_CHAR_BYTES * i : byte_pointer
                    + UNICODE_CHAR_BYTES * (i + 1)
                ],
                byteorder=BYTE_ORDER,
            )
            for i in range(char_set_length)
        )
        return Font(font_name, font_size, bold, italic, char_set)

    @staticmethod
    def name_exists(font_name: str) -> bool:
        """Checks if a font with the given name can be found through pygame."""
        try:
            freetype_font = pygame.freetype.SysFont(font_name, 12)
            if font_name != freetype_font.name.lower().replace(" ", ""):
                return False
            return True
        except AttributeError:
            return False
