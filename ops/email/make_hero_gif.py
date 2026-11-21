# make_hero_gif.py (21 Nov 2026): animated hero picture for SNYPD emails, one per language.
# A sample alert slides in on a dark panel, then a second line (the price rating) appears.
# Frame 0 is the finished picture: mail apps that show only the first frame (Outlook on Windows) get the whole image.
# Wording = the push wording and the homepage sample, nothing new. Output: ../hero/alert-<lang>.gif (+ .png still).
# Usage: python make_hero_gif.py <path to icon-192.png>
import os, sys
from PIL import Image, ImageDraw, ImageFont

ICON = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'hero')
os.makedirs(OUT, exist_ok=True)
W, H = 1120, 380            # shown at 560 x 190
INK = (10, 10, 11)
CARD = (22, 24, 27)
EDGE = (42, 61, 54)
GREEN = (0, 229, 160)
WHITE = (255, 255, 255)
GREY = (141, 150, 155)
F = 'C:/Windows/Fonts/'
f_small = ImageFont.truetype(F + 'segoeui.ttf', 26)
f_bold = ImageFont.truetype(F + 'segoeuib.ttf', 34)
f_line = ImageFont.truetype(F + 'seguisb.ttf', 29)
f_tag = ImageFont.truetype(F + 'segoeuib.ttf', 22)
TEXT = {
    'en': ('SNYPD \u00b7 now', 'SAMPLE', 'New find', 'Jordan 1 Low Travis Scott \u2014 \u20ac180',
           'Cheaper than 76% of this week\u2019s finds'),
    'fr': ('SNYPD \u00b7 maintenant', 'EXEMPLE', 'Nouvelle trouvaille', 'Jordan 1 Low Travis Scott \u2014 180 \u20ac',
           'Moins cher que 76 % des trouvailles de la semaine'),
}
icon = Image.open(ICON).convert('RGBA').resize((92, 92), Image.LANCZOS)
mask = Image.new('L', (92, 92), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, 91, 91), 22, fill=255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def frame(lang, show, slide, rating, dot):
    """show 0..1 card opacity, slide px offset down, rating 0..1 opacity of the rating line, dot 0..1 brightness."""
    app, tag, title, item, rate = TEXT[lang]
    im = Image.new('RGB', (W, H), INK)
    d = ImageDraw.Draw(im)
    # faint grid, like the site's hero wall
    for x in range(0, W, 140):
        d.line((x, 0, x, H), fill=(18, 19, 21), width=2)
    for y in range(0, H, 95):
        d.line((0, y, W, y), fill=(18, 19, 21), width=2)
    if show <= 0:
        return im
    x0, y0, x1, y1 = 70, 70 + slide, W - 70, 310 + slide
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=mix(INK, CARD, show), outline=mix(INK, EDGE, show), width=3)
    ic = Image.new('RGBA', (92, 92), (0, 0, 0, 0))
    ic.paste(icon, (0, 0), mask)
    if show < 1:
        ic.putalpha(ic.getchannel('A').point(lambda a: int(a * show)))
    im.paste(ic, (x0 + 36, y0 + 40), ic)
    tx = x0 + 160
    d.ellipse((tx, y0 + 50, tx + 16, y0 + 66), fill=mix(CARD, GREEN, show * dot))
    d.text((tx + 28, y0 + 38), app, font=f_small, fill=mix(CARD, GREY, show))
    tw = d.textlength(tag, font=f_tag)
    d.text((x1 - 36 - tw, y0 + 42), tag, font=f_tag, fill=mix(CARD, (255, 176, 32), show))
    d.text((tx, y0 + 78), title, font=f_bold, fill=mix(CARD, WHITE, show))
    d.text((tx, y0 + 128), item, font=f_line, fill=mix(CARD, WHITE, show))
    d.text((tx, y0 + 172), rate, font=f_line, fill=mix(CARD, GREEN, show * rating))
    return im


def ease(t):
    return 1 - (1 - t) ** 3


for lang in TEXT:
    final = frame(lang, 1, 0, 1, 1)
    frames, durs = [final], [60]                       # first frame = the finished picture
    frames.append(frame(lang, 0, 0, 0, 1)); durs.append(500)
    for i in range(1, 9):                              # card slides up and fades in
        t = ease(i / 8)
        frames.append(frame(lang, t, int(36 * (1 - t)), 0, 1)); durs.append(55)
    frames.append(frame(lang, 1, 0, 0, 1)); durs.append(450)
    for i in range(1, 6):                              # the price rating line appears
        frames.append(frame(lang, 1, 0, i / 5, 1)); durs.append(70)
    for dot in (0.35, 1, 0.35, 1):                     # the dot blinks twice
        frames.append(frame(lang, 1, 0, 1, dot)); durs.append(320)
    frames.append(final); durs.append(4200)
    pal = final.quantize(colors=64, method=Image.MEDIANCUT, dither=Image.NONE)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    path = os.path.join(OUT, 'alert-%s.gif' % lang)
    q[0].save(path, save_all=True, append_images=q[1:], duration=durs, loop=3, optimize=True, disposal=1)
    final.save(os.path.join(OUT, 'alert-%s.png' % lang), optimize=True)
    print(path, os.path.getsize(path), 'bytes,', len(frames), 'frames')
