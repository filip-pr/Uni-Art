from fontTools.ttLib import TTFont

from .constants import SYSTEM_FONT_PATH, BLACK, WHITE


class QueryFont:
    def __init__(
        self,
        font_path: str,
        font_size: int = 50,
        charset: set[int] | None = None,
        text_color: tuple[int, int, int] = BLACK,
        bg_color: tuple[int, int, int] = WHITE,
        use_embedded_color: bool = True,
        allow_kerning: bool = True,
        force_monospace: bool = False,
    ) -> None:
        try:
            self.font = TTFont(font_path)
        except FileNotFoundError:
            self.font = TTFont(SYSTEM_FONT_PATH + font_path)
        self.font_size = font_size
        self.cmap, self.rev_cmap = self._create_cmaps(charset)

        self.text_color = text_color
        self.bg_color = bg_color

        self.use_embedded_color = use_embedded_color

        self.allow_kerning = allow_kerning
        self.force_monospace = force_monospace

    def _create_cmaps(
        self, charset: set[int] | None
    ) -> tuple[dict[int, str], dict[str, int]]:
        font_cmap = self.font.getBestCmap()
        if charset is None:
            charset = set(font_cmap.keys())
        if ord("\n") in charset:
            charset.remove(ord("\n"))
        rev_cmap = {}
        # removing some unwanted characters (and duplicate glyphs)
        for idx, glyph in font_cmap.items():
            if idx not in charset:
                continue
            if not chr(idx).isprintable():
                continue
            if self.font["hmtx"].metrics[glyph][0] == 0:  # type: ignore
                continue
            if glyph in rev_cmap and idx > rev_cmap[glyph]:
                continue
            rev_cmap[glyph] = idx
        cmap = {idx: glyph for glyph, idx in rev_cmap.items()}
        return cmap, rev_cmap

    def _is_monospace(self) -> bool:
        widths = set()
        for glyph in self.cmap.values():
            width = self.font["hmtx"].metrics[glyph][0]  # type: ignore
            widths.add(width)
        return len(widths) == 1

    def _units_to_pixels(self, units: int) -> int:
        return units * self.font_size // self.font["head"].unitsPerEm  # type: ignore


font = QueryFont("consola.ttf")
