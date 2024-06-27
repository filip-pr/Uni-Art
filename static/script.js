
document.addEventListener("DOMContentLoaded", function () {
    const fontSelect = document.getElementById("font-path"),
        fontCharset = document.getElementById("font-charset"),
        fontTextColor = document.getElementById("font-text-color"),
        fontBackgroundColor = document.getElementById("font-bg-color"),
        fontEmbeddedColor = document.getElementById("font-embedded-color"),
        fontKerning = document.getElementById("font-kerning"),
        fontLigatures = document.getElementById("font-ligatures"),
        fontForceMonospace = document.getElementById("font-force-monospace"),
        fontRenderSize = document.getElementById("font-render-size"),
        fontSetButton = document.getElementById("font-set-button"),
        selectedFont = document.getElementById("selected-font"),

        mediaSource = document.getElementById("media-source"),
        mediaCharacterCount = document.getElementById("media-character-count"),
        mediaRowSpacing = document.getElementById("media-row-spacing"),
        mediaDistanceMetric = document.getElementById("media-distance-metric"),
        mediaFrameRate = document.getElementById("media-frame-rate"),
        mediaChunkLength = document.getElementById("media-chunk-length"),
        mediaBufferSize = document.getElementById("media-buffer-size"),
        mediaSetButton = document.getElementById("media-set-button"),
        selectedMedia = document.getElementById("selected-media"),

        playerTextSize = document.getElementById("player-text-size"),
        playerCurrentTime = document.getElementById("player-current-time"),
        playerJumpTime = document.getElementById("player-jump-time"),
        playerJumpTimeButton = document.getElementById("player-jump-time-button"),

        optionsToggleButton = document.getElementById("options-toggle-button"),
        hintToggleButton = document.getElementById("hint-toggle-button"),

        infoConsole = document.getElementById("info-console"),
        display = document.getElementById("display");

    let fontSet = false;
    let mediaType = null;

    function optionsToggleHide() {
        document.querySelectorAll(".options").forEach(item => {
            item.classList.toggle("hide");
        })
    }

    function hintToggleHide() {
        document.querySelectorAll(".hint").forEach(item => {
            item.classList.toggle("hide");
        })
    }

    function hexToRgb(color) {
        color = Number(`0x1${color.substring(1)}`);
        let red = ((color >> 16) & 255);
        let green = ((color >> 8) & 255);
        let blue = (color & 255);
        return [red, green, blue];
    }

    function invertColor(color) {
        color = Number(`0x1${color.substring(1)}`);
        let red = ((color >> 16) & 255);
        let green = ((color >> 8) & 255);
        let blue = (color & 255);
        let average = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
        return average > 128 ? "#000000" : "#FFFFFF";
    }

    function changeBackground() {
        let selectedColor = fontBackgroundColor.value;
        let InverseColor = invertColor(selectedColor);
        document.querySelector("body").style.color = InverseColor;
        document.querySelector("body").style.background = selectedColor;
    }

    function changeDisplaySize() {
        let size = playerTextSize.value;
        display.style.fontSize = size + "px";
    }

    function loadFonts() {
        fetch("/get_fonts")
            .then(response => response.json())
            .then(data => {
                for (const font of data) {
                    fontSelect.insertAdjacentHTML("beforeend", `<option value="${font}">${font.split("/").at(-1).split(".").at(0)}</option>`);
                }
            });
    }

    function loadMedia() {
        fetch("/get_media")
            .then(response => response.json())
            .then(data => {
                for (const font of data) {
                    mediaSource.insertAdjacentHTML("beforeend", `<option value="${font}">${font.split("/").at(-1)}</option>`);
                }
            });
    }

    function changeFont() {
        let font = fontSelect.value;
        let charset = fontCharset.value;
        let textColor = hexToRgb(fontTextColor.value);
        let backgroundColor = hexToRgb(fontBackgroundColor.value);
        let embeddedColor = fontEmbeddedColor.checked;
        let kerning = fontKerning.checked;
        let ligatures = fontLigatures.checked;
        let forceMonospace = fontForceMonospace.checked;
        let renderSize = fontRenderSize.value;
        fontSetButton.disabled = true;
        infoConsole.textContent = "loading font...";
        fetch("/set_font", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                font: font,
                charset: charset,
                textColor: textColor,
                backgroundColor: backgroundColor,
                embeddedColor: embeddedColor,
                kerning: kerning,
                ligatures: ligatures,
                forceMonospace: forceMonospace,
                renderSize: renderSize
            })
        }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    infoConsole.textContent = "Font set successfully, loaded characters " + data.loadedChars;
                    selectedFont.textContent = `${font.split("/").at(-1).split(".").at(0)} (${charset}, (${textColor}), (${backgroundColor}), ${embeddedColor}, ${kerning}, ${ligatures}, ${forceMonospace}, ${renderSize})`;
                    fontSet = true;
                }
                else {
                    infoConsole.textContent = "Error setting font: " + data.error;
                }
                fontSetButton.disabled = false;
            });
    }

    function ChangeMedia() {
        if (!fontSet) {
            infoConsole.textContent = "Please select a font first";
            return;
        }
        let media = mediaSource.value;
        let characterCount = mediaCharacterCount.value;
        let rowSpacing = mediaRowSpacing.value;
        let distanceMetric = mediaDistanceMetric.value;
        let frameRate = mediaFrameRate.value;
        let chunkLength = mediaChunkLength.value;
        let bufferSize = mediaBufferSize.value;
        mediaSetButton.disabled = true;
        infoConsole.textContent = "loading media...";
        fetch("/set_media", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                media: media,
                characterCount: characterCount,
                rowSpacing: rowSpacing,
                distanceMetric: distanceMetric,
                frameRate: frameRate,
                chunkLength: chunkLength,
                bufferSize: bufferSize
            })
        }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    infoConsole.textContent = "Media set successfully, detected type " + data.detectedType;
                    mediaType = data.detectedType;
                    selectedMedia.textContent = `${media.split("/").at(-1).split(".").at(0)} (${mediaType}, ${characterCount}, ${rowSpacing}, ${distanceMetric}, ${frameRate}, ${chunkLength}, ${bufferSize})`;
                    changeBackground()
                    fetch("get_frame", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                    }).then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                display.textContent = data.frame;
                            }
                            else {
                                infoConsole.textContent = "Error getting frame: " + data.error;
                            }
                        });
                }
                else {
                    infoConsole.textContent = "Error setting media: " + data.error;
                }
                mediaSetButton.disabled = false;
            });
    }


    loadFonts();
    loadMedia();
    optionsToggleButton.addEventListener("click", optionsToggleHide);
    hintToggleButton.addEventListener("click", hintToggleHide);
    fontSetButton.addEventListener("click", changeFont);
    mediaSetButton.addEventListener("click", ChangeMedia);

    playerTextSize.addEventListener("input", changeDisplaySize);
});
