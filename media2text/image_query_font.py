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
        self.char_height = self._units_to_pixels(
            font["hhea"].ascender - font["hhea"].descender
        )
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
        self.max_char_width = self._units_to_pixels(
            max(font["hmtx"].metrics[glyph][0] for glyph in cmap.values())
        )
        averages_dict = self._create_averages_dict(
            font, draw_font, text_color, bg_color, use_embedded_color, cmap, rev_cmap
        )
        self.char_widths = {
            char: self._units_to_pixels(font["hmtx"].metrics[glyph][0])
            for char, glyph in cmap.items()
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
        glyph_height = self.char_height
        glyph_width = self.max_char_width
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
        # normalizing the colors to 0-255 range
        for char, average in averages_dict.items():
            averages_dict[char] = (average - min_color) / (max_color - min_color) * 255
        return averages_dict

    def _create_kdtree_and_index_char_dict(
        self, averages_dict: dict[str, np.ndarray]
    ) -> tuple[cKDTree, dict[int, str]]:
        averages_array = np.empty((len(averages_dict) + 1, 3))
        index_char_dict = {}
        for i, (char, average) in enumerate(averages_dict.items()):
            averages_array[i] = average
            index_char_dict[i] = char
        # dummy value for out of bounds queries
        averages_array[len(averages_dict)] = (-255, -255, -255)
        index_char_dict[len(averages_dict)] = ""
        kdtree = KDTree(averages_array)
        return kdtree, index_char_dict

    def _calculate_offset_colors(
        self, image: np.ndarray, start_offsets: np.ndarray
    ) -> np.ndarray:
        line_width = image.shape[1] * self.char_height
        offset_colors = np.empty((image.shape[0], 3))
        for i, row in enumerate(image):
            if start_offsets[i] >= line_width:
                offset_colors[i] = (-255, -255, -255)
                continue
            offset_colors[i] = row[start_offsets[i] // self.char_height]
        return offset_colors

    def _query_monospace(self, image: np.ndarray, distance_metric: int) -> str:
        cols = image.shape[1]
        image = image.reshape(-1, 3)
        _, indices = self.kdtree.query(image, p=distance_metric)
        indices = indices.reshape(-1, cols)
        return "\n".join(
            "".join(self.index_char_dict[i] for i in row) for row in indices
        )

    def _query_non_monospace(self, image: np.ndarray, distance_metric: int) -> str:
        col_offsets = np.zeros(image.shape[0], dtype=np.int32)
        finished = False
        result = ["" for _ in range(image.shape[0])]
        while not finished:
            finished = True
            averages = self._calculate_offset_colors(image, col_offsets)
            _, indices = self.kdtree.query(averages, p=distance_metric)
            for i, result_index in enumerate(indices):
                result_char = self.index_char_dict[result_index]
                result[i] += result_char
                if result_index != len(self.index_char_dict) - 1:
                    finished = False
                    char_width = self.char_widths[result_char]
                    if (
                        self.kerning
                        and len(result[i]) > 1
                        and result[i][-2:] in self.kerning
                    ):
                        char_width += self.kerning[result[i][-2:]]
                    col_offsets[i] += char_width
        return "\n".join(result)

    def get_new_image_size(
        self,
        original_size: tuple[int, int],
        num_rows: int,
        row_spacing: float = 1.0,
    ) -> tuple[int, int]:
        """Returns the shape that the image should be resized to in order to have the desired
        number of rows and columns while preserving the original aspect ratio in this font.

        Args:
            original_size (tuple[int, int]): Original size of the image (width, height).
            num_rows (int): Number of rows that the image should have.
            row_spacing (float, optional): Spacing between rows, to get the best results
            some experimentation might be necessary. Defaults to 1.0.

        Returns:
            tuple[int, int]: Shape that the image should be resized to (width, height).
        """
        row_height = round(row_spacing * self.char_height)
        original_aspect_ratio = original_size[0] / original_size[1]
        if self.is_monospace:
            font_aspect_ratio = self.max_char_width / row_height
            new_aspect_ratio = original_aspect_ratio / font_aspect_ratio
            num_cols = round(num_rows * new_aspect_ratio)
            return num_cols, num_rows
        return round(num_rows * original_aspect_ratio * row_spacing), num_rows

    def query(self, image: np.ndarray, distance_metric: str = "manhattan") -> str:
        """Makes a string representation of the image using the font.

        Args:
            image (np.ndarray): Source image.
            distance_metric (str, optional): Type of distance metric to be used.
            Defaults to manhattan.

        Returns:
            str: A string representation of the image using the font.
        """
        distance_metrics = {"manhattan": 1, "euclidean": 2}
        if distance_metric not in distance_metrics:
            raise ValueError(
                f"Invalid distance metric, use one of: {' '.join(distance_metrics.keys())}"
            )
        metric_index = distance_metrics[distance_metric]
        if self.is_monospace:
            return self._query_monospace(image, metric_index)
        return self._query_non_monospace(image, metric_index)
