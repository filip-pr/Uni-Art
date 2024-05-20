"""Module for converting an image to text using a font."""

import math

import numpy as np
from PIL import Image

from .image_query_font import ImageQueryFont


def image_convert(
    font: ImageQueryFont,
    image: Image.Image | str,
    num_characters: int,
    row_spacing: float = 1.0,
    distance_metric: str = "manhattan",
) -> str:
    """Function to convert an image to text using a font.

    Args:
        font (ImageQueryFont): Font to use for conversion.
        image (Image.Image | str): Image to convert (numpy array or a path to an image file).
        num_characters (int): Approximate number of characters to use in the output.
        row_spacing (float, optional): Spacing between rows. Defaults to 1.1.
        distance_metric (str, optional): Distance metric to be used for query.
        Defaults to "manhattan".

    Returns:
        str: String representation of the image.
    """
    if isinstance(image, str):
        image = Image.open(image)
    font_aspect_ratio = font.get_font_aspect_ratio()
    original_aspect_ratio = image.size[0] / image.size[1]
    new_aspect_ratio = original_aspect_ratio / font_aspect_ratio
    height = round(math.sqrt(num_characters * new_aspect_ratio) / new_aspect_ratio)
    new_size = font.get_new_image_size(image.size, height, row_spacing)
    image = image.resize(new_size)
    image_array = np.array(image)
    result = font.query(image_array, distance_metric)
    return result
