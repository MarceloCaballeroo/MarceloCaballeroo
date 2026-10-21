"""Convierte la foto de perfil en arte ASCII (una sola vez; el resultado queda en ascii_dark.txt y ascii_light.txt)."""
import colorsys
import sys
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

COLS, ROWS = 72, 36
RAMP = " .'`,:;-~+*=#%@"


def build(src, invert):
    im = Image.open(src).convert("RGBA").crop((85, 20, 345, 280)).resize((COLS * 4, ROWS * 8), Image.LANCZOS)
    px = im.load()
    gray = Image.new("L", im.size, 0)
    mask = Image.new("L", im.size, 0)
    gp, mp = gray.load(), mask.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            # el fondo azul del avatar (saturado) y lo transparente quedan vacios
            if a >= 128 and s <= 0.35:
                gp[x, y] = int(v * 255)
                mp[x, y] = 255
    # el histograma se calcula solo sobre la figura, para no aplanar el rostro
    gray = ImageOps.equalize(gray, mask=mask)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=5, percent=260, threshold=2))
    gray = ImageEnhance.Contrast(gray).enhance(1.2)
    sp = gray.resize((COLS, ROWS), Image.LANCZOS).load()
    msmall = mask.resize((COLS, ROWS), Image.LANCZOS).load()
    lines = []
    for y in range(ROWS):
        row = ""
        for x in range(COLS):
            if msmall[x, y] < 110:
                row += " "
                continue
            v = sp[x, y] / 255
            if invert:
                v = 1 - v
            row += RAMP[min(len(RAMP) - 1, int(v * (len(RAMP) - 1)))]
        lines.append(row)
    return chr(10).join(lines)


if __name__ == "__main__":
    src = sys.argv[1]
    open("ascii_dark.txt", "w", encoding="utf-8", newline="\n").write(build(src, False) + "\n")
    open("ascii_light.txt", "w", encoding="utf-8", newline="\n").write(build(src, True) + "\n")
