"""Module containing constants used in the project."""
import os

UNICODE_CHAR_BYTES = 3
INT_BYTES = 4
BOOL_BYTES = 1
BYTE_ORDER = "big"
NUMPY_BYTE_ORDER = ">"
AUDIO_BYTES_PER_SAMPLE = 2
RENDER_TEMPS_PATH = os.path.join(os.getcwd(), "charvid_render_temp")
