"""Resolve CSS color tokens and color-mix() for design-system sync."""

from __future__ import annotations

import re
from typing import Callable

HEX8_RE = re.compile(r"^#([0-9a-f]{6})([0-9a-f]{2})?$", re.I)
RGB_SPACE_RE = re.compile(
    r"^rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*/\s*([\d.]+)%\s*\)$",
    re.I,
)
RGB_COMMA_RE = re.compile(
    r"^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$",
    re.I,
)
RGBA_COMMA_RE = re.compile(
    r"^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)$",
    re.I,
)
COLOR_MIX_RE = re.compile(
    r"^color-mix\(\s*in\s+srgb\s*,\s*(.+?)\s+([\d.]+)%\s*,\s*(.+?)\s*\)$",
    re.I,
)

NAMED = {
    "transparent": (0, 0, 0, 0.0),
    "black": (0, 0, 0, 1.0),
    "white": (255, 255, 255, 1.0),
}


def _hex_channels(hex_color: str) -> tuple[int, int, int, float]:
    value = hex_color.lstrip("#").lower()
    if len(value) == 6:
        value += "ff"
    if len(value) != 8:
        raise ValueError(hex_color)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    a = int(value[6:8], 16) / 255.0
    return r, g, b, a


def rgba_to_hex8(r: int, g: int, b: int, a: float) -> str:
    alpha = max(0, min(255, round(a * 255)))
    return f"#{r:02x}{g:02x}{b:02x}{alpha:02x}"


def parse_css_color(value: str) -> tuple[int, int, int, float]:
    raw = value.strip().lower()
    if raw in NAMED:
        return NAMED[raw]
    if raw.startswith("#"):
        return _hex_channels(raw)
    m = RGB_SPACE_RE.match(raw)
    if m:
        return (
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            float(m.group(4)) / 100.0,
        )
    m = RGB_COMMA_RE.match(raw)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)), 1.0)
    m = RGBA_COMMA_RE.match(raw)
    if m:
        return (
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            float(m.group(4)),
        )
    raise ValueError(f"unsupported color {value!r}")


def srgb_mix(
    c1: tuple[int, int, int, float],
    c2: tuple[int, int, int, float],
    pct_first: float,
) -> tuple[int, int, int, float]:
    p = pct_first / 100.0
    # Opaque foreground + transparent: keep sRGB, alpha = mix percentage (CSS color-mix).
    if c2[3] == 0.0 and c1[3] == 1.0:
        return (c1[0], c1[1], c1[2], p)
    if c1[3] == 0.0 and c2[3] == 1.0:
        return (c2[0], c2[1], c2[2], 1.0 - p)
    # Premultiplied alpha blend for semi-transparent partners.
    a_out = c1[3] * p + c2[3] * (1.0 - p)
    if a_out <= 0:
        return (0, 0, 0, 0.0)
    out = []
    for i in range(3):
        premix = c1[i] * c1[3] * p + c2[i] * c2[3] * (1.0 - p)
        out.append(round(premix / a_out))
    return (out[0], out[1], out[2], a_out)


def resolve_color_expr(
    expr: str,
    resolver: Callable[[str], str | None],
) -> tuple[int, int, int, float]:
    expr = expr.strip()
    if expr.startswith("var("):
        inner = expr[4:-1].strip()
        resolved = resolver(inner)
        if resolved is None:
            raise ValueError(f"unresolved {expr}")
        return resolve_color_expr(resolved, resolver)
    mix = COLOR_MIX_RE.match(expr)
    if mix:
        left = resolve_color_expr(mix.group(1), resolver)
        right = resolve_color_expr(mix.group(3), resolver)
        return srgb_mix(left, right, float(mix.group(2)))
    return parse_css_color(expr)


def resolve_token_color(
    token: str,
    theme_block: dict[str, str],
    resolver: Callable[[str], str | None],
) -> tuple[int, int, int, float]:
    raw = theme_block.get(token)
    if raw is None:
        raise ValueError(f"missing token {token}")
    if raw.startswith("var("):
        return resolve_color_expr(raw, resolver)
    if "color-mix" in raw:
        return resolve_color_expr(raw, resolver)
    return parse_css_color(raw)


def colors_equivalent(figma: str, css_value: str) -> bool:
    fig = figma.strip().lower()
    try:
        fr, fg, fb, fa = parse_css_color(fig if fig.startswith("#") else fig)
    except ValueError:
        if not fig.startswith("#"):
            return False
        fr, fg, fb, fa = _hex_channels(fig)
    try:
        cr, cg, cb, ca = parse_css_color(css_value)
    except ValueError:
        return False
    return (fr, fg, fb) == (cr, cg, cb) and abs(fa - ca) < 1e-6


def computed_color_hex8(
    css_value: str,
    resolver: Callable[[str], str | None],
) -> str:
    rgba = resolve_color_expr(css_value, resolver)
    return rgba_to_hex8(*rgba)
