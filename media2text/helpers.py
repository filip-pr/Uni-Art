"""Module to provide helper functions for the media2text package."""

import math
import time
import os

import numpy as np
from PIL import Image

from .image_query_font import ImageQueryFont
from .constants import (
    SYSTEM_FONT_PATH,
    RENDER_TEMP_DIR,
)


def estimate_new_size(
    font: ImageQueryFont,
    image_size: tuple[int, int],
    num_characters: int,
    row_spacing: float,
) -> tuple[int, int]:
    """Function to estimate the new size of an image based on the arguments.

    Args:
        font (ImageQueryFont): Font to use for conversion.
        image_size (tuple[int, int]): Size of the image to convert.
        num_characters (int): Approximate number of characters to use in the output.
        row_spacing (float): Spacing between rows.

    Returns:
        tuple[int, int]: New size of the image.
    """
    font_aspect_ratio = font.get_font_aspect_ratio()
    original_aspect_ratio = image_size[0] / image_size[1]
    new_aspect_ratio = original_aspect_ratio / font_aspect_ratio
    height = round(math.sqrt(num_characters / new_aspect_ratio))
    new_size = font.get_resize_size(image_size, height, row_spacing)
    return new_size


def ready_render_temp():
    """Function to prepare the render_temp directory for use."""
    if not os.path.isdir(RENDER_TEMP_DIR):
        os.mkdir(RENDER_TEMP_DIR)
    for file in os.listdir(RENDER_TEMP_DIR):
        try:
            os.remove(os.path.join(RENDER_TEMP_DIR, file))
        except PermissionError:
            pass


def query_benchmark(
    font: ImageQueryFont, image: Image.Image | str, num_characters: int, repeats: int
) -> float:
    """Function to benchmark the image_convert function.

    Args:
        font (ImageQueryFont): Font to use for conversion.
        image (Image): Image to convert.
        num_characters (int): Approximate number of characters to use in the output.
        repeats (int): Number of times to repeat 1s benchmark.

    Returns:
        float: Average number of images converted in a second.
    """
    new_size = estimate_new_size(font, image.size, num_characters, 1)
    image = image.resize(new_size)
    image_array = np.array(image)
    repeat_count = repeats
    count = 0
    average = 0
    stopwatch = time.time()
    while repeat_count > 0:
        font.query(image_array)
        count += 1
        if stopwatch < time.time() - 1:
            average += count
            count = 0
            repeat_count -= 1
            stopwatch = time.time()
    return average / repeats


def get_system_fonts_paths() -> list[str]:
    """Get a list of system font path.

    Returns:
        list[str]: List of system font paths.
    """
    fonts = []
    for file in os.listdir(SYSTEM_FONT_PATH):
        file_path = os.path.join(SYSTEM_FONT_PATH, file)
        if os.path.isfile(file_path) and file_path.endswith((".ttf", ".otf")):
            fonts.append(file_path)
    return fonts
