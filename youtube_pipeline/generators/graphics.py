"""
Generación de IMÁGENES DE APOYO diseñadas con Pillow (sin red).

Crea tarjetas con diseño real (no solo gradiente): degradado diagonal,
motivo de "red neuronal" (nodos + líneas), badge numérico, nombre de la IA,
tagline y la marca del canal MZSHARD. También una pantalla de bienvenida.

Las imágenes luego se animan con Ken Burns (zoom/pan) en FFmpeg para dar vida.
"""

import math
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ..config import cfg

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Paleta por índice: (color base oscuro, color de acento)
PALETTES = [
    ((26, 26, 46), (255, 107, 53)),     # azul noche / naranja
    ((15, 52, 96), (233, 69, 96)),      # azul / rojo coral
    ((22, 33, 62), (83, 168, 182)),     # azul / cyan
    ((45, 19, 44), (199, 44, 65)),      # vino / rojo
    ((11, 12, 16), (102, 252, 241)),    # negro / cyan neón
    ((27, 27, 47), (157, 78, 221)),     # oscuro / morado
    ((34, 40, 49), (255, 211, 105)),    # gris / dorado
    ((20, 33, 61), (252, 163, 17)),     # azul / ámbar
]


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


def _font(path, size):
    return ImageFont.truetype(path, size)


def _gradient(size, c1, c2, angle=45):
    """Degradado diagonal entre c1 y c2."""
    w, h = size
    base = Image.new("RGB", size, c1)
    top = Image.new("RGB", size, c2)
    mask = Image.new("L", size)
    md = mask.load()
    # dirección del degradado
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    maxproj = abs(dx) * w + abs(dy) * h
    for y in range(h):
        for x in range(0, w, 2):  # paso 2px para velocidad
            proj = (x * dx + y * dy) / maxproj
            v = int(max(0, min(255, proj * 255)))
            md[x, y] = v
            if x + 1 < w:
                md[x + 1, y] = v
    return Image.composite(top, base, mask)


def _draw_network_motif(draw, size, accent, seed=0, n=14):
    """Dibuja nodos conectados (estética de red neuronal) semi-transparentes."""
    w, h = size
    rnd = random.Random(seed)
    pts = [(rnd.randint(0, w), rnd.randint(0, h)) for _ in range(n)]
    # líneas entre nodos cercanos
    for i, p in enumerate(pts):
        for q in pts[i + 1:]:
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if d < w * 0.28:
                draw.line([p, q], fill=accent + (40,), width=2)
    # nodos
    for p in pts:
        r = rnd.randint(4, 10)
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=accent + (110,))


def _text_centered(draw, cx, y, text, font, fill, anchor="mm"):
    draw.text((cx, y), text, font=font, fill=fill, anchor=anchor)


def _channel_mark(img, accent, text="MZSHARD"):
    """Marca del canal arriba a la izquierda."""
    draw = ImageDraw.Draw(img)
    f = _font(FONT_BOLD, 34)
    pad = 50
    # punto de acento + wordmark
    draw.ellipse([pad, pad + 6, pad + 22, pad + 28], fill=accent)
    draw.text((pad + 34, pad), text, font=f, fill=(255, 255, 255))


def make_support_image(
    number: str,
    name: str,
    tagline: str,
    out_path: Path,
    index: int = 0,
    width: int = None,
    height: int = None,
) -> Path:
    """Tarjeta de apoyo diseñada para una IA del ranking."""
    width = width or cfg.video_width
    height = height or cfg.video_height
    base_c, accent = PALETTES[index % len(PALETTES)]

    img = _gradient((width, height), base_c, tuple(int(c * 0.45) for c in base_c), angle=55)
    # capa de motivo de red
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    _draw_network_motif(od, (width, height), accent, seed=index + 1, n=16)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    cx = width // 2

    # barra de acento central
    bar_w = int(width * 0.16)
    draw.rectangle([cx - bar_w // 2, int(height * 0.30), cx + bar_w // 2, int(height * 0.30) + 8],
                   fill=accent)

    # badge numérico grande, tenue, de fondo
    f_badge = _font(FONT_BOLD, int(height * 0.42))
    draw.text((cx, int(height * 0.50)), number, font=f_badge,
              fill=tuple(min(255, c + 18) for c in base_c), anchor="mm")

    # nombre de la IA
    f_name = _font(FONT_BOLD, int(height * 0.11))
    _text_centered(draw, cx, int(height * 0.40), name, f_name, (255, 255, 255))

    # tagline
    f_tag = _font(FONT_REG, int(height * 0.042))
    _text_centered(draw, cx, int(height * 0.62), tagline, f_tag, accent)

    # marca del canal
    _channel_mark(img, accent)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def make_welcome_image(
    out_path: Path,
    channel: str = "MZSHARD",
    tagline: str = "Tu dosis de IA y tecnología",
    width: int = None,
    height: int = None,
) -> Path:
    """Pantalla de bienvenida / branding del canal."""
    width = width or cfg.video_width
    height = height or cfg.video_height
    base_c, accent = PALETTES[0]

    img = _gradient((width, height), (10, 10, 22), base_c, angle=60)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    _draw_network_motif(od, (width, height), accent, seed=99, n=22)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    cx = width // 2

    # "BIENVENIDO A"
    f_small = _font(FONT_REG, int(height * 0.05))
    _text_centered(draw, cx, int(height * 0.34), "BIENVENIDO AL CANAL", f_small, (210, 210, 220))

    # logo grande del canal
    f_logo = _font(FONT_BOLD, int(height * 0.16))
    _text_centered(draw, cx, int(height * 0.49), channel, f_logo, (255, 255, 255))

    # línea de acento bajo el logo
    lw = int(width * 0.22)
    draw.rectangle([cx - lw // 2, int(height * 0.60), cx + lw // 2, int(height * 0.60) + 9], fill=accent)

    # tagline
    f_tag = _font(FONT_REG, int(height * 0.045))
    _text_centered(draw, cx, int(height * 0.68), tagline, f_tag, accent)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def make_outro_image(
    out_path: Path,
    channel: str = "MZSHARD",
    width: int = None,
    height: int = None,
) -> Path:
    """Pantalla final de suscripción."""
    width = width or cfg.video_width
    height = height or cfg.video_height
    base_c, accent = PALETTES[3]

    img = _gradient((width, height), (12, 10, 20), base_c, angle=60)
    draw = ImageDraw.Draw(img)
    cx = width // 2

    f_big = _font(FONT_BOLD, int(height * 0.12))
    _text_centered(draw, cx, int(height * 0.40), "SUSCRÍBETE", f_big, (255, 255, 255))

    # botón rojo estilo YouTube
    bw, bh = int(width * 0.26), int(height * 0.11)
    bx, by = cx - bw // 2, int(height * 0.55)
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=18, fill=(230, 33, 45))
    f_btn = _font(FONT_BOLD, int(height * 0.05))
    _text_centered(draw, cx, by + bh // 2, "▶  SUSCRIBIRSE", f_btn, (255, 255, 255))

    f_tag = _font(FONT_REG, int(height * 0.04))
    _text_centered(draw, cx, int(height * 0.74), f"@mzcshard  ·  nuevos videos cada semana",
                   f_tag, accent)

    _channel_mark(img, accent)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path
