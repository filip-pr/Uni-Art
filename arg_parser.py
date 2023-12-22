"""Module for parsing command line arguments."""
import argparse


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--mode", choices=["gui", "file", "terminal"], help="Mode"
    )
    parser.add_argument("-cc", "--charcount", type=int, help="Character count")
    parser.add_argument("-s", "--source", help="Source file")
    parser.add_argument("-d", "--destination", help="Destination file")
    parser.add_argument("-fn", "--fontname", help="Font name")
    parser.add_argument("-fs", "--fontsize", type=int, help="Font size")
    parser.add_argument("-b", "--bold", action="store_true", help="Bold")
    parser.add_argument("-i", "--italic", action="store_true", help="Italic")
    parser.add_argument("-c", "--charset", nargs="+", help="Charset")
    args = parser.parse_args()
    if args.charset is not None:
        args.charset = parse_charset(args.charset)
    return args


def parse_charset(charset):
    """Parse charset argument."""
    char_set = set()
    for char_range in charset:
        try:
            start, end = char_range.split("-")
            char_set.update(
                i for i in range(int(start, base=16), int(end, base=16) + 1)
            )
        except ValueError as e:
            raise ValueError("Invalid charset") from e
    return char_set
