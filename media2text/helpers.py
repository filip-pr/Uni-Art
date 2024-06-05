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
    TEXT_IMAGE_MAGIC_NUMBER,
    TEXT_VIDEO_MAGIC_NUMBER,
    BYTE_ORDER,
    INT_SIZE,
)

from .video_convert import TextVideoPlayer


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


def benchmark(
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


def get_system_font_paths() -> list[str]:
    """Get a list of system font path.

    Returns:
        list[str]: List of system font paths.
    """
    fonts = []
    for file in os.listdir(SYSTEM_FONT_PATH):
        if file.endswith((".ttf", ".otf")):
            fonts.append(os.path.join(SYSTEM_FONT_PATH, file))
    return fonts


def save_text_image(image: str, path: str):
    """Function to save an image to a file.

    Args:
        image (str): Image to save.
        path (str): Path to save the image.
    """
    with open(path, "wb") as file:
        file.write(TEXT_IMAGE_MAGIC_NUMBER.to_bytes(INT_SIZE, BYTE_ORDER))
        file.write(image.encode("utf-8"))


def save_text_video(video_player: TextVideoPlayer, path: str):
    """Function to save a video to a file.

    Args:
        video_player (TextVideoPlayer): Video player to save.
        path (str): Path to save the video.
    """
    video_player.set_time(0)
    frame_count = 0
    with open(path + ".tmp", "wb") as file:
        for frame in video_player.iter_frames():
            frame_bytes = frame.encode("utf-8")
            file.write(len(frame_bytes).to_bytes(INT_SIZE, BYTE_ORDER))
            file.write(frame_bytes)
            frame_count += 1
    with open(path, "wb") as file:
        file.write(TEXT_VIDEO_MAGIC_NUMBER.to_bytes(INT_SIZE, BYTE_ORDER))
        file.write(video_player.frame_rate.to_bytes(INT_SIZE, BYTE_ORDER))
        file.write(frame_count.to_bytes(INT_SIZE, BYTE_ORDER))
        frames_offset = 3 * INT_SIZE + frame_count * INT_SIZE
        with open(path + ".tmp", "rb") as tmp_file:
            for _ in range(frame_count):
                offset = tmp_file.tell() + frames_offset
                file.write(offset.to_bytes(INT_SIZE, BYTE_ORDER))
                frame_size = int.from_bytes(tmp_file.read(INT_SIZE), BYTE_ORDER)
                tmp_file.seek(frame_size, 1)
            tmp_file.seek(0)
            for _ in range(frame_count):
                frame_size = int.from_bytes(tmp_file.read(INT_SIZE), BYTE_ORDER)
                frame = tmp_file.read(frame_size)
                file.write(frame_size.to_bytes(INT_SIZE, BYTE_ORDER))
                file.write(frame)
            file.write(tmp_file.read())
        os.remove(path + ".tmp")
