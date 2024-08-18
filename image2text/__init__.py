"""query_font module"""

from .helpers import get_system_fonts_paths, query_benchmark
from .helpers import ready_render_temp as _ready_render_temp
from .image_convert import TextImage
from .image_query_font import ImageQueryFont
from .video_convert import TextVideo

_ready_render_temp()

__all__ = [
    "ImageQueryFont",
    "TextImage",
    "TextVideo",
    "query_benchmark",
    "get_system_fonts_paths",
]
