"""Module containing the CharImage class."""
import math

import numpy as np
from PIL import Image
import pygame

from font import Font
from consts import UNICODE_CHAR_BYTES, INT_BYTES


class CharImage:
    """Class representing an image made out of characters."""
    def __init__(
        self,
        image_source: str | np.ndarray | list,
        char_count: int | str,
        font: Font,
    ):
        
        if isinstance(char_count, str):
            try:
                char_count = int(char_count)
            except ValueError as e:
                raise ValueError("Character count must be an integer") from e
        if char_count < 1:
            raise ValueError("Character count must be greater than or equal to 1")
        if font is None:
            raise ValueError("Font must be set")
        self.font = font
        # if image_source is a list, it is assumed to be a list of char indices
        if isinstance(image_source, list):
            self.chars = image_source
        # if image_source is a numpy array, it is assumed to be a array with RGB values of the image
        elif isinstance(image_source, np.ndarray):
            self.chars = self.font.get_closest_chars(image_source)
        # if image_source is a string, it is assumed to be a path to an image
        else:
            image = Image.open(image_source).convert("RGB")
            new_image_size = CharImage.calculate_new_size(
                (image.width, image.height), char_count, font
            )
            image = np.asarray(image.resize(new_image_size))
            self.chars = self.font.get_closest_chars(image)
        # an array containing pygame surfaces of the characters for each position in the image
        self.renders_array = [
            [self.font.get_rendered_char(char_index) for char_index in row]
            for row in self.chars
        ]

    def draw(self, spacing: float = 1.1) -> pygame.Surface:
        """Draws the CharImage on a pygame surface."""
        font_width, font_height = (
            self.font.width() * spacing,
            self.font.height() * spacing,
        )
        surface = pygame.Surface(
            (
                font_width * len(self.chars[0]),
                font_height * len(self.chars),
            )
        )
        for i, row in enumerate(self.renders_array):
            for j, render in enumerate(row):
                surface.blit(
                    render,
                    (
                        j * font_width,
                        i * font_height,
                    ),
                )
        return surface

    @staticmethod
    def calculate_new_size(
        size: tuple[int, int], char_count: int, font: Font
    ) -> tuple[int, int]:
        """Returns the new size of the image (in characters)."""
        aspect_ratio = size[0] / size[1] / font.aspect_ratio()
        image_width = math.ceil(math.sqrt(char_count * aspect_ratio))
        image_width += image_width % 2
        image_height = math.ceil(char_count / image_width)
        image_height += image_height % 2
        return image_width, image_height

    def chars_to_bytes(self) -> bytes:
        """Converts the chars list to bytes."""
        char_image_bytes = b""
        for row in self.chars:
            for char_index in row:
                char_image_bytes += char_index.to_bytes(UNICODE_CHAR_BYTES)
        return char_image_bytes

    @staticmethod
    def chars_from_bytes(data: bytes, shape: tuple[int, int]) -> list:
        """Converts the chars bytes to a list (shape needs to be provided)."""
        rows, columns = shape
        char_image = [
            [
                int.from_bytes(
                    data[
                        UNICODE_CHAR_BYTES
                        * (i * columns + j) : UNICODE_CHAR_BYTES
                        * (i * columns + j + 1)
                    ]
                )
                for j in range(columns)
            ]
            for i in range(rows)
        ]
        return char_image

    def as_file(self, file_name: str):
        """
        Saves the CharImage as a file.
        Only the necessary data is saved.
        """
        # saves the CharImage as a file (only the necessary data is saved)
        try:
            with open(file_name, "wb") as wf:
                # font_bytes_length
                font_bytes = self.font.to_bytes()
                wf.write(len(font_bytes).to_bytes(INT_BYTES))
                # font_bytes
                wf.write(font_bytes)
                # rows
                wf.write(len(self.chars).to_bytes(INT_BYTES))
                # columns
                wf.write(len(self.chars[0]).to_bytes(INT_BYTES))
                # char_image_bytes
                wf.write(self.chars_to_bytes())
        except OSError as e:
            raise OSError(f"Could not save CharImage to '{file_name}'") from e

    @staticmethod
    def from_file(file_name: str) -> "CharImage":
        """Loads a CharImage from a file."""
        try:
            with open(file_name, "rb") as rf:
                font_bytes_length = int.from_bytes(rf.read(INT_BYTES))
                font = Font.from_bytes(rf.read(font_bytes_length))
                rows = int.from_bytes(rf.read(INT_BYTES))
                columns = int.from_bytes(rf.read(INT_BYTES))
                char_image = CharImage.chars_from_bytes(rf.read(), (rows, columns))
                return CharImage(char_image, 1, font=font)
        except OSError as e:
            raise OSError(f"Could not load CharImage from '{file_name}'") from e
