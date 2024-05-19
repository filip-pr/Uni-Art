"""Module for font allowing for color to character queries"""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, features
import numpy as np
from scipy.spatial import KDTree, cKDTree

from .constants import SYSTEM_FONT_PATH, BLACK, WHITE, LOOKUP_TYPE_LIGATURE


class ImageQueryFont:
    """Class for querying font for color to character mappings"""

    def __init__(
        self,
        font_path: str,
        charset: set[str] | None = None,
        text_color: tuple[int, int, int] = BLACK,
        bg_color: tuple[int, int, int] = WHITE,
        use_embedded_color: bool = True,
        use_kerning: bool = True,
        use_ligatures: bool = True,
        force_monospace: bool = False,
        font_render_size: int = 100,
    ):
        font_path = self._get_font_path(font_path)
        font = TTFont(font_path)
        self.ppem_ratio = font_render_size / font["head"].unitsPerEm
        cmap, rev_cmap = self._create_cmaps(font, charset)
        self.kerning = (
            None if not use_kerning else self._create_kerning_dict(font, rev_cmap)
        )
        self.is_monospace = True if force_monospace else self._is_monospace(font, cmap)
        self.unit_char_height = font["hhea"].ascender - font["hhea"].descender
        layout_engine = (
            ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC
        )
        if use_ligatures and layout_engine == ImageFont.Layout.BASIC:
            print("Warning: Ligatures are not supported without RAQM layout engine.")
        if use_ligatures:
            ligature_dict, rev_ligature_dict = self._create_ligature_dicts(
                font, rev_cmap
            )
            cmap = ligature_dict | cmap
            rev_cmap = rev_ligature_dict | rev_cmap
        draw_font = ImageFont.truetype(
            font_path,
            font_render_size,
            encoding="unic",
            layout_engine=layout_engine,
        )
        self.max_unit_char_width = max(
            font["hmtx"].metrics[glyph][0] for glyph in cmap.values()
        )
        averages_dict = self._create_averages_dict(
            font, draw_font, text_color, bg_color, use_embedded_color, cmap, rev_cmap
        )
        self.unit_char_widths = {
            char: font["hmtx"].metrics[glyph][0] for char, glyph in cmap.items()
        }
        self.kdtree, self.index_char_dict = self._create_kdtree_and_index_char_dict(
            averages_dict
        )

    def _units_to_pixels(self, units: int) -> int:
        return round(units * self.ppem_ratio)

    def _get_font_path(self, font_path: str) -> str:
        if Path(font_path).is_file():
            return font_path
        if Path(SYSTEM_FONT_PATH, font_path).is_file():
            return str(Path(SYSTEM_FONT_PATH, font_path))
        raise FileNotFoundError(f"Font file not found: {font_path}")

    def _create_cmaps(
        self, font: TTFont, charset: set[str] | None
    ) -> tuple[dict[str, str], dict[str, str]]:
        font_cmap = font.getBestCmap()
        if charset is None:
            charset = set(chr(idx) for idx in font_cmap.keys())
        if "\n" in charset:
            charset.remove("\n")
        rev_cmap = {}
        for idx, glyph in font_cmap.items():
            if chr(idx) not in charset:
                continue
            if glyph in rev_cmap and idx > ord(rev_cmap[glyph]):
                continue
            rev_cmap[glyph] = chr(idx)
        cmap = {char: glyph for glyph, char in rev_cmap.items()}
        return cmap, rev_cmap

    def _create_kerning_dict(
        self, font: TTFont, rev_cmap: dict[str, str]
    ) -> dict[str, int] | None:
        kerning = None
        if "kern" in font:
            kerning = {}
            for (left, right), value in font["kern"].kernTables[0].kernTable.items():
                if not left in rev_cmap or not right in rev_cmap:
                    continue
                kerning[rev_cmap[left] + rev_cmap[right]] = value
        return kerning

    def _is_monospace(self, font: TTFont, cmap: dict[str, str]) -> bool:
        widths = set()
        for glyph in cmap.values():
            width = font["hmtx"].metrics[glyph][0]
            widths.add(width)
        if 0 in widths:
            widths.remove(0)
        return len(widths) == 1

    def _create_ligature_dicts(
        self, font: TTFont, rev_cmap: dict[str, str]
    ) -> tuple[dict[str, str], dict[str, str]]:
        ligature_dict = {}
        if "GSUB" not in font:
            return {}, {}
        ligature_lookups = [
            lookup
            for lookup in font["GSUB"].table.LookupList.Lookup
            if lookup.LookupType == LOOKUP_TYPE_LIGATURE
        ]
        ligature_subtables = [
            subtable
            for subtable_list in [lookup.SubTable for lookup in ligature_lookups]
            for subtable in subtable_list
        ]
        if not ligature_subtables:
            return {}, {}
        for subtable in ligature_subtables:
            for first_comp, ligatures in subtable.ligatures.items():
                for ligature in ligatures:
                    result_glyph = ligature.LigGlyph
                    components = [first_comp] + ligature.Component
                    if not all(component in rev_cmap for component in components):
                        continue
                    components = "".join(
                        [rev_cmap[component] for component in components]
                    )
                    if not result_glyph in ligature_dict:
                        ligature_dict[components] = result_glyph
        rev_ligature_dict = {value: key for key, value in ligature_dict.items()}
        return ligature_dict, rev_ligature_dict

    def _create_averages_dict(
        self,
        font: TTFont,
        draw_font: ImageFont.FreeTypeFont,
        text_color: tuple[int, int, int],
        bg_color: tuple[int, int, int],
        use_embedded_color: bool,
        cmap: dict[str, str],
        rev_cmap: dict[str, str],
    ) -> dict[str, np.ndarray]:
        glyph_height = self._units_to_pixels(self.unit_char_height)
        glyph_width = self._units_to_pixels(self.max_unit_char_width)
        averages_dict = {}
        for char, glyph in list(cmap.items()):
            if not self.is_monospace:
                glyph_width = self._units_to_pixels(font["hmtx"].metrics[glyph][0])
            if glyph_width == 0:
                cmap.pop(char)
                rev_cmap.pop(glyph)
                continue
            image = Image.new("RGB", (glyph_width, glyph_height), bg_color)
            draw = ImageDraw.Draw(image)
            draw.text(
                (0, 0), char, text_color, draw_font, embedded_color=use_embedded_color
            )
            colors_average = np.average(np.array(image), axis=(0, 1))
            if (colors_average == bg_color).all() and not char.isspace():
                cmap.pop(char)
                rev_cmap.pop(glyph)
                continue
            averages_dict[char] = colors_average
        min_color = np.min(list(averages_dict.values()), axis=0)
        max_color = np.max(list(averages_dict.values()), axis=0)
        for char, average in averages_dict.items():
            averages_dict[char] = (average - min_color) / (max_color - min_color) * 255
        return averages_dict

    def _create_kdtree_and_index_char_dict(
        self, averages_dict: dict[str, np.ndarray]
    ) -> tuple[cKDTree, dict[int, str]]:
        averages_array = np.empty((len(averages_dict), 3))
        index_char_dict = {}
        for i, (char, average) in enumerate(averages_dict.items()):
            averages_array[i] = average
            index_char_dict[i] = char
        kdtree = KDTree(averages_array)
        return kdtree, index_char_dict
