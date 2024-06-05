"""Module for converting an image to text using a font."""

import numpy as np
from PIL import Image

from .image_query_font import ImageQueryFont
from .constants import TEXT_IMAGE_MAGIC_NUMBER, BYTE_ORDER, INT_SIZE
from .helpers import estimate_new_size


class TextImage:
    """Class for converting an image to text."""

    def __init__(
        self,
        font: ImageQueryFont,
        image: Image.Image | str,
        num_characters: int,
        row_spacing: float = 1.0,
        distance_metric: str = "manhattan",
    ):
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
            with open(image, "rb") as file:
                magic_number = int.from_bytes(file.read(INT_SIZE), BYTE_ORDER)
                if magic_number == TEXT_IMAGE_MAGIC_NUMBER:
                    self.text = file.read().decode("utf-8")
            image = Image.open(image)
        new_size = estimate_new_size(font, image.size, num_characters, row_spacing)
        image = image.resize(new_size)
        image_array = np.array(image)
        self.text = font.query(image_array, distance_metric)

    def save(self, path: str):
        """Function to save an image to a file.

        Args:
            image (str): Image to save.
            path (str): Path to save the image.
        """
        with open(path, "wb") as file:
            file.write(TEXT_IMAGE_MAGIC_NUMBER.to_bytes(INT_SIZE, BYTE_ORDER))
            file.write(self.text.encode("utf-8"))
