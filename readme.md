# Uni-Art

A program I created as a semester project at a university.

Allows for conversion of almost any image/video type to a corresponding data type made only out of Unicode characters and of course their playback.

Uni-Art allows for a great deal of customization, you can:

- Specify the set of characters to be used for conversion
- Set font in which the image or video will be rendered (and made to match the best)
- Toggle font features like ligatures and kerning
- Change the text and background colors
- Specifying number of characters an image or a video frame should have
- And more..

Uni-Art player is also able to render and play videos in real time. The performance largely depends on what hardware you're running it on, but even with couple years old mid-range system one can render 5000+ character per frame video in 30fps in without lag with monospace font and about 1000 character per frame video in 30fps in without lag with non-monospace (querying for non-monospace fonts can't be parallelized that well).

Please note that only operating system this was tested on is Windows 10 (with python 3.11.3) and there is no guarantee of it running anywhere else. Although in theory there shouldn't be a reason for it not to (at least not one that I'm aware of).

## Installation

To run Uni-Art one needs some non-standard libraries. To install those simply use:
- pip install -r requirements.txt

You might also need to install ffmpeg:
- https://ffmpeg.org/

## User guide

### Running of the program
Simply clone the repository, setup a python virtual environment and install the dependencies.

#### Running with GUI
Run app.py. That should one you browser with the GUI which itself is pretty self-explanatory.

#### Running in console
- TODO

### Possible issues
- TODO

## Datatypes
- TODO
