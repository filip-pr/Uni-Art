"""Main module of the application."""

import os

from flask import Flask, render_template, jsonify, request
from PIL import UnidentifiedImageError

from media2text import get_system_fonts_paths, ImageQueryFont, TextImage, TextVideo

app = Flask(__name__)

FONTS_DIR = "fonts/"
MEDIA_DIR = "media/"


class TextMedia:
    """Class to store the current font and player."""

    font = None
    media = None


@app.route("/")
def index():
    """Index route."""
    return render_template("index.html")


@app.route("/get_fonts")
def get_fonts():
    """Get a list of system fonts."""
    fonts = get_system_fonts_paths()
    for font in os.listdir(FONTS_DIR):
        font_path = os.path.join(FONTS_DIR, font)
        if (
            os.path.isfile(font_path)
            and not font.startswith(".")
            and font.endswith((".ttf", ".otf"))
        ):
            fonts.append(font_path.replace("\\", "/"))
    return jsonify(sorted(fonts, key=lambda x: x.split("/")[-1].lower()))


@app.route("/get_media")
def get_media():
    """Get a list of media files."""
    media_files = []
    for media_file in os.listdir(MEDIA_DIR):
        media_path = os.path.join(MEDIA_DIR, media_file)
        if os.path.isfile(media_path) and not media_file.startswith("."):
            media_files.append(media_path.replace("\\", "/"))
    return jsonify(media_files)


@app.route("/set_font", methods=["POST"])
def set_font():
    """Set the font to be used."""
    font_data = request.json
    if font_data is None:
        return jsonify(success=False, error="Unknown error")
    try:
        font_path = font_data["font"]
        charset = font_data["charset"]
        match charset:
            case "ascii":
                charset = set(chr(i) for i in range(127))
            case "unicode":
                charset = set(chr(i) for i in range(0x110000))
            case _:
                charset = set(charset)
        text_color = tuple(font_data["textColor"])
        background_color = tuple(font_data["backgroundColor"])
        embedded_color = font_data["embeddedColor"]
        kerning = font_data["kerning"]
        ligatures = font_data["ligatures"]
        force_monospace = font_data["forceMonospace"]
        render_size = int(font_data["renderSize"])
        new_font = ImageQueryFont(
            font_path,
            charset,
            text_color,
            background_color,
            embedded_color,
            kerning,
            ligatures,
            force_monospace,
            render_size,
        )
        TextMedia.font = new_font
    except Exception as e:  # pylint: disable=broad-except
        return jsonify(success=False, error=str(e))
    return jsonify(success=True, loadedChars=TextMedia.font.num_characters)


@app.route("/set_media", methods=["POST"])
def set_media():
    """Set the media to be used."""
    media_data = request.json
    if media_data is None:
        return jsonify(success=False, error="Unknown error")
    try:
        if TextMedia.font is None:
            raise ValueError("No font loaded")
        media_path = media_data["media"]
        character_count = int(media_data["characterCount"])
        row_spacing = float(media_data["rowSpacing"])
        distance_metric = media_data["distanceMetric"]
        frame_rate = int(media_data["frameRate"])
        chunk_length = int(media_data["chunkLength"])
        try:
            new_media = TextImage(
                TextMedia.font,
                media_path,
                character_count,
                row_spacing,
                distance_metric,
            )
            TextMedia.media = new_media
            detected_type = "image"
        except UnidentifiedImageError:
            new_media = TextVideo(
                TextMedia.font,
                media_path,
                frame_rate,
                character_count,
                row_spacing,
                distance_metric,
                chunk_length,
            )
            TextMedia.media = new_media
            detected_type = "video"
    except Exception as e:  # pylint: disable=broad-except
        return jsonify(success=False, error=str(e))
    return jsonify(success=True, detectedType=detected_type)


if __name__ == "__main__":
    if not os.path.exists(FONTS_DIR):
        os.makedirs(FONTS_DIR)
    if not os.path.exists(MEDIA_DIR):
        os.makedirs(MEDIA_DIR)
    app.run(debug=True, threaded=True)
