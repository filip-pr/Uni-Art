# Uni-Art Documentation

## About
This document contains the programming documentation for the Uni-Art project. It will hopefully help to clarify how the things work in the background, but for the more specific 'documentation' it is always better to look at the code.

## Python Modules

### gui.py
Flask server app which serves as an interface between the 'browser application' image2text package used for image to text conversion.

### console.py
Python script made as a console interface for the image2text package.

### image2text/ 

- ### \_\_init\_\_.py
    Standard python module defining a package and simplifying imports

- ### constants.py
    Module containing constants used in the project.

- ### helpers.py
    Module containing some helper functions, only even semi-interesting part is the estimate new size function, which.. well estimates new size. That is done by taking the passed font aspect ratio (average character width/character height) and calculates the new size trying to preserve the aspect ratio after conversion (by doing fairly simple calculations). 

- ### image_query_font
    This is the hearth of the project although the main function is fairly simple.. analyze font and then given an image use the font's characters to match the original image as much as possible (this is quite a big simplification). To be more detailed:
    - It extracts font's units per em and calculates pixel unit ratio later used for rendering
    - Creates cmaps base on given charset and font's supported character, adding ligatures if supported and not disabled.
    - Extracts width of each character in the cmap and a kerning width adjustments if supported and not disabled.
    - Renders all cmap glyphs and calculates and normalizes their color average (average pixel rgb values) and stores those inside a kd-tree for fast query. 

    #### Query
    Mechanism of query largely depends on whether or not the font is monospace or not. If it is then the query is done by simply matching each pixel of the original to a single glyph. If the font is not monospace, characters are matched from left to right on each row, when a character is added it's true width (width + kerning) is calculated and the point from where the color is matched shifts that distance to the right. Repeating this process until all rows have reached the rightmost side of the image. Due to the fact that only each row can be calculated independently (instead of all pixels) parallelization is limited and querying non monospace fonts is couple times slower.

    Also it is good to note that it is not the average glyph color which the pixel is being matched to, but the normalized average color (meaning all fonts have completely 'black' and 'white' characters) this is to increase the range of colors displayed but sometimes making the colors distorted.


- ### image_convert.py
    Module defining the TextImage class. TextImage itself is pretty simple, it just resizes the source image and then call the query method of the given font to convert image to text.

- ### video_convert.py
    Module defining the TextVideo class. The conversion part is basically the same as the one of TextImage. The main difference is the handling of long videos and simultaneously preprocessing video chunks using ffmpeg and actually converting them to text.

    There are 2 background threads that take take of the conversion process, the first one is taking care of processing the video into small chunks with reduced resolution that can be quickly converted. The other one iterates through frames of those converted chunks and converts the individual frames to text which is then stored inside a buffer. Any call for a converted video image then simply takes the image on top of the buffer.

## Non-python code

### script.js
Fairly simple javascript application used as the backend of the GUI.

### index.html
Just a simple html file defining the GUI layout.