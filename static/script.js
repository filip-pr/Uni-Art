document.addEventListener('DOMContentLoaded', function () {
    const fontSource = document.getElementById('font-source'),
        fontOtherLabel = document.getElementById('font-other-label'),
        fontOtherInput = document.getElementById('font-other-input'),
        fontCharset = document.getElementById('font-charset'),
        fontTextColor = document.getElementById('font-text-color'),
        fontBackgroundColor = document.getElementById('font-bg-color'),
        fontEmbeddedColor = document.getElementById('font-embedded-color'),
        fontKerning = document.getElementById('font-kerning'),
        fontLigatures = document.getElementById('font-ligatures'),
        fontForceMonospace = document.getElementById('font-force-monospace'),
        fontRenderSize = document.getElementById('font-render-size'),
        fontSetButton = document.getElementById('font-set-button'),
        fontInfo = document.getElementById('selected-font'),
        mediaSource = document.getElementById('media-source'),
        mediaOtherLabel = document.getElementById('media-other-label'),
        mediaOtherInput = document.getElementById('media-other-input'),
        mediaCharacterCount = document.getElementById('media-character-count'),
        mediaRowSpacing = document.getElementById('media-row-spacing'),
        mediaDistanceMetric = document.getElementById('media-distance-metric'),
        mediaFrameRate = document.getElementById('media-frame-rate'),
        mediaChunkLength = document.getElementById('media-chunk-length'),
        mediaBufferSize = document.getElementById('media-buffer-size'),
        mediaSetButton = document.getElementById('media-set-button'),
        mediaInfo = document.getElementById('selected-media'),
        playerTextSize = document.getElementById('player-text-size'),
        playerCurrentTime = document.getElementById('player-current-time'),
        playerJumpTime = document.getElementById('player-jump-time'),
        playerJumpTimeButton = document.getElementById('player-jump-time-button'),
        optionsToggleButton = document.getElementById('options-toggle-button'),
        hintToggleButton = document.getElementById('hint-toggle-button'),
        infoConsole = document.getElementById('info-console'),
        display = document.getElementById('display');

    let selectedFont = fontSource.value,
        selectedCharset = fontCharset.value,
        selectedTextColor = hexToRgb(fontTextColor.value),
        selectedBackgroundColor = hexToRgb(fontBackgroundColor.value),
        selectedEmbeddedColor = fontEmbeddedColor.checked,
        selectedKerning = fontKerning.checked,
        selectedLigatures = fontLigatures.checked,
        selectedForceMonospace = fontForceMonospace.checked,
        selectedRenderSize = fontRenderSize.value,
        selectedCharacterCount = mediaCharacterCount.value,
        selectedRowSpacing = mediaRowSpacing.value,
        selectedDistanceMetric = mediaDistanceMetric.value,
        selectedFrameRate = mediaFrameRate.value,
        selectedChunkLength = mediaChunkLength.value,
        selectedBufferSize = mediaBufferSize.value,
        fontSet = false,
        mediaType = null,
        playerFrame = 0,
        playerIsPlaying = false,
        playerIntervalId = null,
        displayFontFace = null;


    function optionsToggleHide() {
        document.querySelectorAll('.options').forEach(item => {
            item.classList.toggle('hide');
        })
    }

    function hintToggleHide() {
        document.querySelectorAll('.hint').forEach(item => {
            item.classList.toggle('hide');
        })
    }

    function hexToRgb(color) {
        color = Number(`0x1${color.substring(1)}`);
        let red = (color >> 16) & 255;
        let green = (color >> 8) & 255;
        let blue = color & 255;
        return [red, green, blue];
    }

    function invertColor(color) {
        color = Number(`0x1${color.substring(1)}`);
        let red = (color >> 16) & 255;
        let green = (color >> 8) & 255;
        let blue = color & 255;
        let average = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
        return average > 128 ? '#000000' : '#FFFFFF';
    }

    function changeBackground() {
        let selectedColor = selectedBackgroundColor;
        let InverseColor = invertColor(selectedColor);
        document.querySelector('body').style.color = InverseColor;
        document.querySelector('body').style.background = selectedColor;
    }

    function changeDisplaySize() {
        let size = playerTextSize.value;
        display.style.fontSize = size + 'px';
        display.style.lineHeight = size + 'px';
    }

    function loadFonts() {
        fetch('/get_fonts')
            .then(response => response.json())
            .then(data => {
                for (const font of data) {
                    fontSource.insertAdjacentHTML(
                        'beforeend',
                        `<option value="${font}">${font
                            .split('/')
                            .at(-1)
                            .split('.')
                            .at(0)}</option>`
                    );
                }
            });
    }

    function otherFontInput() {
        if (fontSource.value === '<other-font>') {
            fontOtherLabel.classList.remove('hide');
            fontOtherInput.classList.remove('hide');
        } else {
            fontOtherLabel.classList.add('hide');
            fontOtherInput.classList.add('hide');
        }
    }

    function loadMedia() {
        fetch('/get_media')
            .then(response => response.json())
            .then(data => {
                for (const font of data) {
                    mediaSource.insertAdjacentHTML(
                        'beforeend',
                        `<option value="${font}">${font.split('/').at(-1)}</option>`
                    );
                }
            });
    }

    function otherMediaInput() {
        if (mediaSource.value === '<other-media>') {
            mediaOtherLabel.classList.remove('hide');
            mediaOtherInput.classList.remove('hide');
        } else {
            mediaOtherLabel.classList.add('hide');
            mediaOtherInput.classList.add('hide');
        }
    }

    function changeFont() {
        if (playerIsPlaying) {
            togglePlay();
        }
        selectedFont = fontSource.value;
        if (selectedFont === '<other-font>') {
            selectedFont = fontOtherInput.value;
        }
        selectedCharset = fontCharset.value;
        selectedTextColor = fontTextColor.value;
        selectedBackgroundColor = fontBackgroundColor.value;
        selectedEmbeddedColor = fontEmbeddedColor.checked;
        selectedKerning = fontKerning.checked;
        selectedLigatures = fontLigatures.checked;
        selectedForceMonospace = fontForceMonospace.checked;
        selectedRenderSize = fontRenderSize.value;
        fontSetButton.disabled = true;

        infoConsole.textContent = 'loading font...'
        fetch('/set_font', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                font: selectedFont,
                charset: selectedCharset,
                textColor: hexToRgb(selectedTextColor),
                backgroundColor: hexToRgb(selectedBackgroundColor),
                embeddedColor: selectedEmbeddedColor,
                kerning: selectedKerning,
                ligatures: selectedLigatures,
                forceMonospace: selectedForceMonospace,
                renderSize: selectedRenderSize
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    infoConsole.textContent =
                        'Font set successfully, loaded characters ' + data.loadedChars
                    fontInfo.textContent = `${selectedFont
                        .split('/')
                        .at(-1)
                        .split('.')
                        .at(0)} (${selectedCharset}, (${hexToRgb(
                            selectedTextColor
                        )}), (${hexToRgb(
                            selectedBackgroundColor
                        )}), ${selectedEmbeddedColor}, ${selectedKerning}, ${selectedLigatures}, ${selectedForceMonospace}, ${selectedRenderSize})`;
                    display.style.color = `${selectedTextColor}`;
                    const fontBytes = atob(data.fontData);
                    const fontArray = new Uint8Array(fontBytes.length);
                    for (let i = 0; i < fontBytes.length; i++) {
                        fontArray[i] = fontBytes.charCodeAt(i);
                    }
                    displayFontFace = new FontFace('displayFont', fontArray.buffer);
                    displayFontFace.load().then(function (loadedFont) {
                        document.fonts.add(loadedFont);
                        display.style.fontFamily = 'displayFont'
                    })
                    changeBackground();
                    fontSet = true;
                } else {
                    infoConsole.textContent = 'Error setting font: ' + data.error;
                }
                fontSetButton.disabled = false;
            })
    }

    function ChangeMedia() {
        if (playerIsPlaying) {
            togglePlay();
        }
        if (!fontSet) {
            infoConsole.textContent = 'Please select a font first';
            return;
        }
        playerFrame = 0;
        let selectedMedia = mediaSource.value;
        if (selectedMedia === '<other-media>') {
            selectedMedia = mediaOtherInput.value;
        }
        selectedCharacterCount = mediaCharacterCount.value;
        selectedRowSpacing = mediaRowSpacing.value;
        selectedDistanceMetric = mediaDistanceMetric.value;
        selectedFrameRate = mediaFrameRate.value;
        selectedChunkLength = mediaChunkLength.value;
        selectedBufferSize = mediaBufferSize.value;
        mediaSetButton.disabled = true;
        infoConsole.textContent = 'loading media...';
        fetch('/set_media', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                media: selectedMedia,
                characterCount: selectedCharacterCount,
                rowSpacing: selectedRowSpacing,
                distanceMetric: selectedDistanceMetric,
                frameRate: selectedFrameRate,
                chunkLength: selectedChunkLength,
                bufferSize: selectedBufferSize
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    infoConsole.textContent =
                        'Media set successfully, detected type ' + data.detectedType;
                    mediaType = data.detectedType;
                    mediaInfo.textContent = `${selectedMedia
                        .split('/')
                        .at(-1)
                        .split('.')
                        .at(
                            0
                        )} (${mediaType}, ${selectedCharacterCount}, ${selectedRowSpacing}, ${selectedDistanceMetric}, ${selectedFrameRate}, ${selectedChunkLength}, ${selectedBufferSize})`;
                    fetch('get_frame', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                display.textContent = data.frame;
                            } else {
                                infoConsole.textContent = 'Error getting frame: ' + data.error;
                            }
                        })
                } else {
                    infoConsole.textContent = 'Error setting media: ' + data.error;
                }
                mediaSetButton.disabled = false;
            })
    }

    function updateFrame() {
        fetch('get_frame', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    display.textContent = data.frame;
                    playerFrame += 1;
                    playerCurrentTime.textContent = Math.round(playerFrame / selectedFrameRate);
                } else {
                    infoConsole.textContent = 'Error getting frame: ' + data.error;
                }
            })
    }

    function togglePlay() {
        playerIsPlaying = !playerIsPlaying;
        if (playerIsPlaying && mediaType === 'video') {
            playerIntervalId = setInterval(updateFrame, 1000 / selectedFrameRate);
        } else {
            clearInterval(playerIntervalId);
        }
    }

    function setTime() {
        if (playerIsPlaying) {
            togglePlay();
        }
        let time = parseInt(playerJumpTime.value);
        if (time < 0) {
            time = 0;
        }
        playerCurrentTime.textContent = time;
        playerCurrentTime.textContent = time;
        playerFrame = time * selectedFrameRate;
        playerJumpTimeButton.disabled = true;

        fetch('set_time', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                time: time
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateFrame();
                } else {
                    infoConsole.textContent = 'Error setting time: ' + data.error
                }
                playerJumpTimeButton.disabled = false;
            })
    }

    loadFonts();
    loadMedia();
    fontSource.addEventListener('change', otherFontInput);
    mediaSource.addEventListener('change', otherMediaInput);
    optionsToggleButton.addEventListener('click', optionsToggleHide);
    hintToggleButton.addEventListener('click', hintToggleHide);
    fontSetButton.addEventListener('click', changeFont);
    mediaSetButton.addEventListener('click', ChangeMedia);
    playerTextSize.addEventListener('input', changeDisplaySize);
    playerJumpTimeButton.addEventListener('click', setTime);
    document.addEventListener('keydown', event => {
        if (event.code === 'Space' && document.activeElement.tagName != 'INPUT') {
            event.preventDefault();
            togglePlay();
        }
    });
});
