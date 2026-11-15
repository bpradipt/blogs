#!/usr/bin/env python3
"""Render a Markdown table to a styled PNG with Pillow.

Usage:
  render-table.py <table.md> [output.png]   # render a table file
  render-table.py --selftest                # assert the renderer works

Deterministic: fixed fonts, fixed palette, fixed layout math. The input is
a plain Markdown table (lines of | a | b | c | plus a |---|---| separator).
Output defaults to <table>.png next to the input, rendered at 2x for crispness.
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCALE = 2
FONT_SIZE = 15          # logical px
PAD_X, PAD_Y = 11, 7    # logical cell padding
BORDER = 1              # logical grid line
MAX_WIDTH = 820         # logical table width; longer text wraps
LINE_HEIGHT = 1.5

BG = (255, 255, 255)
HEADER_BG = (242, 242, 242)
BORDER_C = (205, 205, 205)
TEXT = (85, 85, 85)
HEADER_TEXT = (51, 51, 51)

FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def clean(cell):
    """Strip inline markdown; return (text, whole_cell_is_bold)."""
    cell = cell.strip()
    bold = False
    m = re.match(r"^\*\*(.+?)\*\*$", cell, re.S) or re.match(r"^\*(.+?)\*$", cell, re.S)
    if m:
        cell = m.group(1)
        bold = True
    cell = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cell)  # links -> text
    cell = cell.replace("`", "")                          # inline code
    cell = cell.replace("**", "").replace("*", "")        # leftover emphasis
    return cell.strip(), bold


def parse(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.match(r"^:?-{3,}:?$", c) for c in cells):
            continue  # separator row
        rows.append(cells)
    return rows  # rows[0] is the header


def wrap(text, font, draw, max_w):
    """Greedy word wrap; hard-breaks any word longer than max_w."""
    if not text:
        return [""]
    out = []
    for word in text.split():
        while draw.textlength(word, font=font) > max_w and len(word) > 1:
            lo, hi = 1, len(word)
            while lo < hi:
                mid = (lo + hi) // 2
                if draw.textlength(word[:mid], font=font) <= max_w:
                    lo = mid + 1
                else:
                    hi = mid
            cut = max(1, lo - 1)
            out.append(word[:cut])
            word = word[cut:]
        if out and draw.textlength(out[-1] + " " + word, font=font) <= max_w:
            out[-1] += " " + word
        else:
            out.append(word)
    return out


def render(rows, out_path):
    ncols = len(rows[0])
    border = BORDER * SCALE
    pad_x, pad_y = PAD_X * SCALE, PAD_Y * SCALE
    total_w = MAX_WIDTH * SCALE
    fs = FONT_SIZE * SCALE

    font = load_font(FONT_REGULAR, fs)
    font_bold = load_font(FONT_BOLD, fs)

    # equal-width columns
    cell_full = (total_w - (ncols + 1) * border) // ncols
    col_w = cell_full - 2 * pad_x

    probe = Image.new("RGB", (1, 1), BG)
    draw = ImageDraw.Draw(probe)

    # wrap every cell
    grid = []
    for r, row in enumerate(rows):
        grid_row = []
        for c in range(ncols):
            cell = row[c] if c < len(row) else ""
            txt, bold = clean(cell)
            f = font_bold if (r == 0 or bold) else font
            grid_row.append((wrap(txt, f, draw, col_w), r == 0 or bold))
        grid.append(grid_row)

    line_h = int(fs * LINE_HEIGHT)
    row_h = []
    for r in range(len(grid)):
        n = max(len(grid[r][c][0]) for c in range(ncols))
        row_h.append(n * line_h + 2 * pad_y)

    height = sum(row_h) + (len(grid) + 1) * border
    img = Image.new("RGB", (total_w, height), BG)
    draw = ImageDraw.Draw(img)

    # header background
    draw.rectangle([0, 0, total_w, row_h[0] + border], fill=HEADER_BG)

    # vertical grid lines
    x = 0
    for _ in range(ncols + 1):
        draw.rectangle([x, 0, x + border, height], fill=BORDER_C)
        x += border + cell_full

    # horizontal grid lines
    y = 0
    for rh in row_h:
        draw.rectangle([0, y, total_w, y + border], fill=BORDER_C)
        y += border + rh
    draw.rectangle([0, y, total_w, y + border], fill=BORDER_C)

    # text
    y = border
    for r in range(len(grid)):
        x = border
        for c in range(ncols):
            lines, bold = grid[r][c]
            f = font_bold if bold else font
            color = HEADER_TEXT if r == 0 else TEXT
            ty = y + pad_y
            for ln in lines:
                draw.text((x + pad_x, ty), ln, font=f, fill=color)
                ty += line_h
            x += cell_full + border
        y += row_h[r] + border

    img.save(out_path)
    return img.size


def selftest():
    src = "| Name | Qty |\n|---|---|\n| **apple** | `3` |\n| banana | 12 |\n"
    rows = parse(src)
    assert len(rows) == 3 and rows[0] == ["Name", "Qty"], rows
    assert clean("**apple**") == ("apple", True)
    assert clean("[link](http://x) `code`") == ("link code", False)

    out = Path("/tmp/table-selftest.png")
    w, h = render(rows, str(out))
    assert out.exists() and w > 0 and h > 0
    Image.open(out).verify()
    out.unlink()
    print(f"selftest OK ({w}x{h})")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    if len(sys.argv) < 2:
        sys.exit("usage: render-table.py <table.md> [output.png]")
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".png")
    rows = parse(src.read_text())
    if not rows:
        sys.exit(f"no table found in {src}")
    w, h = render(rows, str(out))
    print(f"Wrote {out} ({w}x{h})")


if __name__ == "__main__":
    main()
