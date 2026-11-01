"""Oro's Notion art: Dominican blue and red screentone on blue-black ink, with film grain.

Run from the repo root:  python3 tools/make_art.py
Writes covers/*.jpg (1500x600) and tiles/*.png (360x480 arch tiles with transparent corners).
Everything is drawn from code, so any piece can be regenerated or restyled here.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COVERS = os.path.join(ROOT, 'covers')
TILES = os.path.join(ROOT, 'tiles')
os.makedirs(COVERS, exist_ok=True)
os.makedirs(TILES, exist_ok=True)

# Palette
INK = (11, 15, 23)          # #0B0F17 blue-black ground
BLUE = (0, 45, 98)          # #002D62 Dominican blue
LIFT = (38, 86, 150)        # #265696 the same blue, lifted so dots read on ink
RED = (206, 17, 38)         # #CE1126 Dominican red
WHITE = (236, 240, 246)     # #ECF0F6


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def grain(img, amt, seed):
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.float32)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


def screentone(w, h, density, cell=14, color=LIFT, ground=INK, angle=30, shape='dot', ss=3):
    """density(x, y) with x, y in 0..1 returns ink coverage 0..1. Drawn supersampled for clean edges."""
    W, H = w * ss, h * ss
    im = Image.new('RGB', (W, H), ground)
    d = ImageDraw.Draw(im)
    c = cell * ss
    th = math.radians(angle)
    ca, sa = math.cos(th), math.sin(th)
    R = int(math.hypot(W, H))
    for gy in range(-R, R, c):
        for gx in range(-R, R, c):
            x = W / 2 + gx * ca - gy * sa
            y = H / 2 + gx * sa + gy * ca
            if x < -c or y < -c or x > W + c or y > H + c:
                continue
            v = max(0.0, min(1.0, density(x / W, y / H)))
            if v < 0.02:
                continue
            if shape == 'dot':
                r = c * 0.5 * math.sqrt(v) * 1.1
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)
            else:  # line
                t = c * v * 0.9
                dx, dy = -sa * c / 2, ca * c / 2
                d.line([x - dx, y - dy, x + dx, y + dy], fill=color, width=max(1, int(t)))
    return im.resize((w, h), Image.LANCZOS)


def layered(w, h, layers):
    """Several screentone passes on one ground, e.g. a crosshatch."""
    base = None
    for kw in layers:
        im = screentone(w, h, **kw)
        if base is None:
            base = im
        else:
            a = np.asarray(base).astype(np.int16)
            b = np.asarray(im).astype(np.int16)
            ground = np.array(INK, dtype=np.int16)
            mask = np.any(b != ground, axis=2, keepdims=True)
            base = Image.fromarray(np.where(mask, b, a).astype(np.uint8))
    return base


def cover(name, layers, cross=(0.66, 0.55), red=None, seed=1):
    """A 1500x600 cover. cross = where the hairline white cross meets (None for none).
    red = (x0, y0, x1, y1) in 0..1 for the one red block, or None."""
    w, h = 1500, 600
    im = layered(w, h, layers)
    d = ImageDraw.Draw(im)
    if red:
        x0, y0, x1, y1 = red
        d.rectangle([int(w * x0), int(h * y0), int(w * x1), int(h * y1)], fill=RED)
    if cross:
        cx, cy = int(w * cross[0]), int(h * cross[1])
        d.rectangle([cx - 2, 0, cx + 2, h], fill=WHITE)
        d.rectangle([0, cy - 2, w, cy + 2], fill=WHITE)
    im = grain(im, 9, seed)
    im.save(os.path.join(COVERS, name + '.jpg'), quality=86, optimize=True, progressive=True)


def tile(name, layers, seed=1):
    w, h = 360, 480
    im = grain(layered(w, h, layers), 8, seed)
    m = Image.new('L', (w * 3, h * 3), 0)
    d = ImageDraw.Draw(m)
    r = w * 3 // 2
    d.ellipse([0, 0, w * 3, 2 * r], fill=255)
    d.rectangle([0, r, w * 3, h * 3], fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste(im.convert('RGBA'), (0, 0), m)
    out.save(os.path.join(TILES, name + '.png'), optimize=True)


def dots(f, cell=14, angle=30, color=LIFT):
    return dict(density=f, cell=cell, angle=angle, color=color, shape='dot')


def lines(f, cell=12, angle=0, color=LIFT):
    return dict(density=f, cell=cell, angle=angle, color=color, shape='line')


# Shapes of ink, shared between a hub's cover and its tile
SHAPE = {
    'present':  [dots(lambda x, y: smooth(1.15 - (x * 0.9 + (1 - y) * 0.6)), 16)],
    'future':   [dots(lambda x, y: smooth((y - 0.12) * 1.3) * (0.55 + 0.45 * math.cos((x - 0.66) * 3)), 16, 15)],
    'claude':   [dots(lambda x, y: 0.04 + 0.75 * smooth(1 - abs(x - 0.3) * 2.2) * smooth(1 - abs(y - 0.5) * 1.8), 18, 0)],
    'tomo':     [dots(lambda x, y: smooth(1 - math.hypot(x - 0.8, y - 0.45) * 1.5), 16, 45)],
    'deadlines': [dots(lambda x, y: smooth(1.2 - y * 1.1), 13, 30, RED)],
    'school':   [lines(lambda x, y: 0.15 + 0.6 * smooth(y), 12, 0)],
    'jobs':     [lines(lambda x, y: 0.2 + 0.7 * smooth(1 - abs(x - 0.5) * 2), 12, 60)],
    'money':    [dots(lambda x, y: smooth(1 - math.hypot(x - 0.5, y - 0.62) * 1.7), 13, 45)],
    'life':     [dots(lambda x, y: 0.06 + 0.5 * smooth(1.1 - y), 16, 75)],
    'personal': [dots(lambda x, y: smooth((x + y) * 0.7 - 0.2), 13, 30)],
    'inbox':    [dots(lambda x, y: 0.05 + 0.5 * smooth(1 - abs(y - 0.5) * 2.5), 12, 0)],
    'career':   [lines(lambda x, y: smooth(1.1 - y), 12, 90), lines(lambda x, y: smooth(1.1 - y) * 0.5, 12, 0)],
    'goals':    [dots(lambda x, y: smooth(1 - abs(math.hypot(x - 0.5, y - 0.55) - 0.28) * 6), 12, 30)],
    'f-life':   [dots(lambda x, y: 0.06 + 0.5 * smooth(y * 1.2 - 0.1), 16, 70)],
    'f-personal': [lines(lambda x, y: smooth((x + (1 - y)) * 0.75 - 0.25), 12, 30)],
    'projects': [dots(lambda x, y: 0.1 + 0.55 * smooth(1 - y), 18, 0), dots(lambda x, y: 0.35 * smooth(y - 0.3), 18, 0, BLUE)],
    'school-career': [lines(lambda x, y: 0.1 + 0.5 * smooth(1 - abs(y - 0.5) * 2), 12, 0)],
    'c-personal': [dots(lambda x, y: smooth(1 - math.hypot(x - 0.35, y - 0.5) * 1.6), 14, 20)],
    'accounts': [lines(lambda x, y: 0.08 + 0.4 * smooth(x), 14, 90)],
    'swing-desk': [lines(lambda x, y: 0.05 + 0.85 * smooth(1 - abs(y - (0.75 - 0.5 * x - 0.08 * math.sin(x * 20))) * 5), 10, 90)],
    'homework': [lines(lambda x, y: 0.1 + 0.6 * smooth(1 - y * 0.9), 11, 0), dots(lambda x, y: 0.0, 11)],
    'vision':   [dots(lambda x, y: smooth(1 - abs(math.hypot(x - 0.5, (y - 0.5) * 0.5) - 0.22) * 7), 12, 0)],
    'legacy':   [dots(lambda x, y: smooth(1.3 - abs(x - 0.5) * 3.5 - y * 0.2) * smooth(y * 1.5), 12, 0), lines(lambda x, y: 0.0, 12)],
    'swancast': [dots(lambda x, y: smooth(1 - abs(math.hypot(x - 0.3, y - 0.5) % 0.12 - 0.06) * 18) * smooth(1.2 - math.hypot(x - 0.3, y - 0.5) * 1.6), 10, 0)],
    'other-builds': [dots(lambda x, y: 0.08 + 0.55 * smooth(0.5 + 0.5 * math.sin((x * 2.5 + y) * math.pi * 2)), 13, 0)],
    'tomo-desk': [lines(lambda x, y: 0.1 + 0.45 * smooth(1 - math.hypot(x - 0.8, y - 0.45) * 1.5), 12, 45)],
}

# Section covers: the white cross plus the one red block
cover('section-present', SHAPE['present'], cross=(0.66, 0.55), red=(0.66, 0.55, 0.74, 0.69), seed=11)
cover('section-future', SHAPE['future'], cross=(0.66, 0.45), red=(0.66, 0.33, 0.72, 0.45), seed=12)
cover('section-claude', SHAPE['claude'], cross=(0.3, 0.5), red=(0.24, 0.5, 0.3, 0.62), seed=13)
cover('section-tomo', SHAPE['tomo'], cross=(0.8, 0.45), red=(0.8, 0.45, 0.86, 0.6), seed=14)

# Hub and page covers: the cross only (Deadlines is the red one)
for i, key in enumerate(['deadlines', 'school', 'jobs', 'money', 'life', 'personal', 'inbox',
                         'career', 'goals', 'f-life', 'f-personal',
                         'projects', 'school-career', 'c-personal', 'accounts',
                         'swing-desk', 'homework', 'vision', 'legacy', 'swancast', 'other-builds', 'tomo-desk']):
    cover('page-' + key, SHAPE[key], cross=(0.5, 0.5), seed=20 + i)

# Arch tiles for the home-page navigation
for i, key in enumerate(['deadlines', 'school', 'jobs', 'money', 'life', 'personal',
                         'career', 'goals', 'f-life', 'f-personal']):
    tile(key, SHAPE[key], seed=60 + i)

print('covers:', len(os.listdir(COVERS)), 'tiles:', len(os.listdir(TILES)))
