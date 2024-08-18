"""Module containing the Uni-Art app CLI."""

import argparse

from PIL import UnidentifiedImageError

from image2text import ImageQueryFont, TextImage, TextVideo


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--mode", choices=["file", "terminal"], help="Mode", required=True
    )
    parser.add_argument("-s", "--media-source", help="Media source file", required=True)
    parser.add_argument("-f", "--font-source", help="Font source file", required=True)
    parser.add_argument(
        "--charset", help="Charset (string of characters)", default="unicode"
    )
    parser.add_argument("--text-color", help="Text color (#RRGGBB)", default="#000000")
    parser.add_argument(
        "--background-color", help="Background color (#RRGGBB)", default="#FFFFFF"
    )
    parser.add_argument("--color", action="store_true", help="Use embedded color")
    parser.add_argument("--kerning", action="store_true", help="Use kerning")
    parser.add_argument("--ligatures", action="store_true", help="Use ligatures")
    parser.add_argument("--monospace", action="store_true", help="Force monospace")
    parser.add_argument("--font-size", type=int, help="Font size", default=100)
    parser.add_argument("--char-count", type=int, help="Character count", required=True)
    parser.add_argument("--row-spacing", type=float, help="Row spacing", default=1.0)
    parser.add_argument(
        "--distance-metric",
        choices=["manhattan", "euclidean"],
        help="Distance metric",
        default="manhattan",
    )
    parser.add_argument("--frame-rate", type=int, help="Frame rate", default=30)
    parser.add_argument(
        "--chunk-length", type=int, help="Video chunk length", default=5
    )
    parser.add_argument(
        "--buffer-size", type=int, help="Video buffer size", default=100
    )
    parser.add_argument("-d", "--destination", help="Destination file")
    args = parser.parse_args()
    return args


def hex_to_rgb(hex_color):
    """Convert a hex color to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def main():
    """Main function of the CLI."""
    args = parse_args()
    if args.destination is None:
        args.destination = f"{args.media_source}.txt"
    match args.charset:
        case "ascii":
            args.charset = set(chr(i) for i in range(128))
        case "unicode":
            args.charset = set(chr(i) for i in range(0x110000))
        case _:
            args.charset = set(args.charset)
    args.text_color = hex_to_rgb(args.text_color)
    args.background_color = hex_to_rgb(args.background_color)
    font = ImageQueryFont(
        args.font_source,
        args.charset,
        args.text_color,
        args.background_color,
        args.color,
        args.kerning,
        args.ligatures,
        args.monospace,
        args.font_size,
    )
    is_image = True
    try:
        new_media = TextImage(
            font,
            args.media_source,
            args.char_count,
            args.row_spacing,
            args.distance_metric,
        )
    except UnidentifiedImageError:
        is_image = False
        new_media = TextVideo(
            font,
            args.media_source,
            args.frame_rate,
            args.char_count,
            args.row_spacing,
            args.distance_metric,
            args.chunk_length,
            args.buffer_size,
        )
    match args.mode:
        case "file":
            new_media.save(args.destination)
        case "terminal":
            if is_image:
                print(new_media.text)
                return
            while True:
                try:
                    print(new_media.next_frame())
                except StopIteration:
                    break


if __name__ == "__main__":
    main()
