"""Render shared Whop artwork without confusing one-time and monthly billing."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'whop-one-search.png'
image = Image.new('RGB', (1600, 900), '#090A0B')
draw = ImageDraw.Draw(image)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def text(x, y, value, size=26, color='#F4F5F6', bold=False):
    draw.text((x, y), value, fill=color,
              font=ImageFont.truetype(BOLD if bold else FONT, size))

text(85, 54, 'SNYPD_  /  VINTED ALERTS', 23, '#00E5A0')
text(80, 110, 'ONE SEARCH.', 72, bold=True)
text(80, 195, 'TWO WAYS TO HUNT.', 72, bold=True)
text(85, 300, 'Runs 24/7, even with your dashboard closed.', 28, '#ACB2B7')

for x, label, amount, billing, lines, accent in [
    (85, 'HUNT PASS', '€3.99', 'ONCE',
     ['30 days of access', 'No automatic renewal'], '#00E5A0'),
    (825, 'SOLO', '€5.99', '/ MONTH',
     ['Ongoing access', 'Renews monthly; cancel any time'], '#BD78FF')
]:
    draw.rectangle((x, 385, x+690, 708), fill='#111315', outline='#2B2E33', width=2)
    draw.rectangle((x, 385, x+690, 389), fill=accent)
    text(x+30, 418, label, 26, accent)
    text(x+26, 464, amount, 69, bold=True)
    text(x+306, 503, billing, 23, '#ACB2B7')
    text(x+30, 590, lines[0], 24)
    text(x+30, 640, lines[1], 23, '#ACB2B7')

text(85, 763, 'Push alerts on phone or computer; alert setup required.', 25)
text(85, 814, 'VAT included. Use your SNYPD account email at checkout.', 23, '#ACB2B7')
OUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUT, optimize=True)
print(OUT)
