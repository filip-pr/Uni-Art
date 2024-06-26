"""query_font module"""

from .image_query_font import ImageQueryFont
from .image_convert import TextImage
from .video_convert import TextVideo
from .helpers import query_benchmark, get_system_fonts_paths

from .helpers import ready_render_temp as _ready_render_temp

_ready_render_temp()
