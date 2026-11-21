#!/usr/bin/env python3
"""Build chrome.css (browser UI), dist/userContent.css (web pages) and image.png.

Static cursors are drawn from the ASCII art in src/cursors/*.txt, the two
loaders (wristwatch, spinning ball) are generated procedurally. Everything is
embedded as base64 PNG data URIs so the mod is a single self-contained CSS file.

Stdlib only:  python3 scripts/build.py [--content-size N]
"""
import argparse
import base64
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_ID = "theme-ClassicMacCursors"
PREF = "theme-classicmaccursors"
SIZES = (1, 2, 3)
FRAMES = 8

BLACK, WHITE, CLEAR = (0, 0, 0, 255), (255, 255, 255, 255), (0, 0, 0, 0)


# --- bitmap helpers ---------------------------------------------------------

class Bitmap:
    def __init__(self, w, h, hotspot):
        self.w, self.h, self.hotspot = w, h, hotspot
        self.px = [[CLEAR] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def line(self, x0, y0, x1, y1, c=BLACK):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def with_halo(self):
        """Add the 1px white border classic Mac cursors get from their mask."""
        out = Bitmap(self.w + 2, self.h + 2, (self.hotspot[0] + 1, self.hotspot[1] + 1))
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] == BLACK:
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if out.px[y + 1 + dy][x + 1 + dx] == CLEAR:
                                out.px[y + 1 + dy][x + 1 + dx] = WHITE
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] != CLEAR:
                    out.px[y + 1][x + 1] = self.px[y][x]
        return out

    def scaled(self, n):
        out = Bitmap(self.w * n, self.h * n, (self.hotspot[0] * n, self.hotspot[1] * n))
        out.px = [[self.px[y // n][x // n] for x in range(out.w)] for y in range(out.h)]
        return out

    def png(self):
        raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in self.px)

        def chunk(tag, data):
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))

    def css(self, size):
        """CSS <cursor-image> value: url(...) hx hy, scaled by `size`."""
        b = self.scaled(size)
        data = base64.b64encode(b.png()).decode()
        return f"url(data:image/png;base64,{data}) {b.hotspot[0]} {b.hotspot[1]}"


def load_ascii(path):
    lines = path.read_text().splitlines()
    meta = dict(l.split(": ", 1) for l in lines if ": " in l)
    art = [l for l in lines if l and ": " not in l]
    w = max(map(len, art))
    hx, hy = map(int, meta["hotspot"].split())
    bm = Bitmap(w, len(art), (hx, hy))
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            bm.px[y][x] = BLACK if ch == "X" else WHITE if ch in "o." else CLEAR
    return bm.with_halo() if meta.get("halo") == "yes" else bm


# --- procedural loaders -----------------------------------------------------

def watch(frame):
    """System 7 wristwatch: strap, round face, minute hand sweeping."""
    bm = Bitmap(16, 22, (8, 11))
    cx, cy, r = 7.5, 10.5, 5.6
    for y in range(bm.h):
        for x in range(bm.w):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                bm.px[y][x] = WHITE
            if r - 1.1 < d <= r:
                bm.px[y][x] = BLACK
    for y in list(range(1, 4)) + list(range(18, 21)):  # straps
        for x in (5, 6, 7, 8, 9, 10):
            bm.px[y][x] = WHITE
        bm.px[y][4] = bm.px[y][11] = BLACK
    for x in range(5, 11):
        bm.px[0][x] = bm.px[21][x] = BLACK
    bm.px[10][12] = bm.px[11][12] = bm.px[10][13] = bm.px[11][13] = BLACK  # crown
    ang = 2 * math.pi * frame / FRAMES
    bm.line(8, 11, round(8 + 4 * math.sin(ang)), round(11 - 4 * math.cos(ang)))
    bm.line(8, 11, 8, 8)  # hour hand
    return bm.with_halo()


def ball(frame):
    """Classic black & white spinning ball (System 7 'acur' style)."""
    bm = Bitmap(16, 16, (8, 8))
    cx = cy = 7.5
    spin = (frame / FRAMES) * (math.pi / 4)  # 8 sectors -> period of 45 deg
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - cx, y - cy)
            if d > 7.6:
                continue
            if d > 6.5:
                bm.px[y][x] = BLACK
                continue
            a = (math.atan2(y - cy, x - cx) + spin) % (2 * math.pi)
            bm.px[y][x] = BLACK if int(a // (math.pi / 4)) % 2 else WHITE
    return bm.with_halo()


# --- CSS --------------------------------------------------------------------

STATIC = ("arrow", "ibeam", "crosshair", "hand")


def load_cursors():
    return {n: load_ascii(ROOT / "src" / "cursors" / f"{n}.txt") for n in STATIC}


def vars_for(size, cursors):
    """Custom properties holding every cursor image at one scale."""
    v = {f"--cmc-{n}": bm.css(size) for n, bm in cursors.items()}
    for i in range(FRAMES):
        v[f"--cmc-watch-{i}"] = watch(i).css(size)
        v[f"--cmc-ball-{i}"] = ball(i).css(size)
    return v


def fmt_vars(v, indent="    "):
    return "\n".join(f"{indent}{k}: {val};" for k, val in v.items())


TEXT_TAGS = ("p, h1, h2, h3, h4, h5, h6, li, dd, dt, td, th, pre, code, blockquote, "
             "figcaption, label, em, strong, b, i, u, small, abbr, cite, q")
LINK = ("a[href], area[href], button, summary, select, label[for], [role=button], "
        "[role=link], [role=tab], [role=menuitem], [role=option], "
        "input:is([type=button], [type=submit], [type=reset], [type=image], "
        "[type=checkbox], [type=radio], [type=file], [type=color], [type=range])")
TEXT_FIELD = ("input:not([type=button], [type=submit], [type=reset], [type=image], "
              "[type=checkbox], [type=radio], [type=file], [type=color], [type=range]), "
              "textarea, [contenteditable=true], [contenteditable=\"\"]")
BUSY_ATTR = ('[style*="cursor: wait"], [style*="cursor:wait"], '
             '[style*="cursor: progress"], [style*="cursor:progress"]')


BUSY_SEL = f"[busy], [wait-cursor], {BUSY_ATTR}"


def keyframes(prefix):
    steps = "\n".join(
        f"  {round(i * 100 / FRAMES, 3)}% {{ cursor: var({prefix}{i}), wait; animation-timing-function: step-end; }}"
        for i in range(FRAMES))
    return f"@keyframes cmc-spin {{\n{steps}\n  100% {{ cursor: var({prefix}0), wait; }}\n}}"


def chrome_css(cursors):
    out = ["/* Classic Mac Cursors - generated by scripts/build.py, do not edit by hand. */",
           '@-moz-document url-prefix("chrome:") {']
    for size in SIZES:
        sel = f':root:has(#{MOD_ID}[{PREF}-size="{size}"])'
        out.append(f"  {sel} {{\n{fmt_vars(vars_for(size, cursors))}\n  }}\n")
    out.append("  /* Pick the loader (default: watch) and whether it animates. */")
    for loader in ("watch", "ball"):
        sel = (f':root:has(#{MOD_ID}[{PREF}-loader="{loader}"])' if loader == "ball"
               else f':root:not(:has(#{MOD_ID}[{PREF}-loader="ball"]))')
        props = "\n".join(f"    --cmc-wait-{i}: var(--cmc-{loader}-{i});" for i in range(FRAMES))
        out.append(f"  {sel} {{\n{props}\n  }}")
    out.append(f"""
  :root {{
    --cmc-anim: cmc-spin 0.8s step-end infinite;
  }}
  :root:has(#{MOD_ID}[{PREF}-animate="static"]) {{
    --cmc-anim: none;
    --cmc-wait-fixed: var(--cmc-wait-0);
  }}

  {keyframes("--cmc-wait-").replace(chr(10), chr(10) + "  ")}

  /* Everything defaults to the classic arrow ... */
  :root:has(#{MOD_ID}) *:not(:is({BUSY_SEL}), :is({BUSY_SEL}) *) {{
    cursor: var(--cmc-arrow), default !important;
  }}
  /* ... clickable things get the pointing hand ... */
  :root:has(#{MOD_ID}) :is(button, toolbarbutton, menuitem, menu, tab, .tabbrowser-tab,
      .urlbarView-row, .bookmark-item, .zen-workspace-tab-icon, [role=button], [role=tab],
      [role=menuitem], [role=link], a[href], .text-link, .toolbarbutton-1, .zen-current-workspace-indicator,
      #zen-sidebar-top-buttons *, #zen-essentials *, .tab-content, .tab-icon-image, .tab-close-button),
  :root:has(#{MOD_ID}) :is({LINK}) {{
    cursor: var(--cmc-hand), pointer !important;
  }}
  /* ... text fields get the I-beam ... */
  :root:has(#{MOD_ID}) :is(input:not([type=button], [type=checkbox], [type=radio]), textarea,
      #urlbar-input, .urlbar-input, search-textbox, html|input, html|textarea, [contenteditable=true]) {{
    cursor: var(--cmc-ibeam), text !important;
  }}
  /* ... and anything busy gets the animated loader. */
  :root:has(#{MOD_ID}) :is({BUSY_SEL}),
  :root:has(#{MOD_ID}) :is({BUSY_SEL}) * {{
    cursor: var(--cmc-wait-fixed, var(--cmc-wait-0)), wait;
    animation: var(--cmc-anim);
  }}
}}
""")
    return "\n".join(out)


def content_css(cursors, size):
    v = vars_for(size, cursors)
    wait_frames = "\n".join(
        f"  {round(i * 100 / FRAMES, 3)}% {{ cursor: var(--cmc-watch-{i}), wait; animation-timing-function: step-end; }}"
        for i in range(FRAMES))
    return f"""/* Classic Mac Cursors (web content) - generated by scripts/build.py. */
@-moz-document url-prefix(http), url-prefix(https), url-prefix(file), url-prefix(about:), url-prefix(moz-extension) {{
  :root {{
{fmt_vars(v)}
  }}
  @keyframes cmc-spin {{
{wait_frames}
    100% {{ cursor: var(--cmc-watch-0), wait; }}
  }}
  html, body, * {{ cursor: var(--cmc-arrow), default; }}
  :is({TEXT_TAGS}) {{ cursor: var(--cmc-ibeam), text; }}
  :is({LINK}),
  :is({LINK}) * {{ cursor: var(--cmc-hand), pointer !important; }}
  :is({TEXT_FIELD}) {{ cursor: var(--cmc-ibeam), text !important; }}
  :is(:disabled, [aria-disabled=true]) {{ cursor: var(--cmc-arrow), not-allowed !important; }}
  :is({BUSY_ATTR}), :is({BUSY_ATTR}) * {{
    cursor: var(--cmc-watch-0), wait;
    animation: cmc-spin 0.8s step-end infinite;
  }}
}}
"""


def preview_png(cursors):
    """Contact sheet used as the mod's store image."""
    items = [cursors[n].scaled(3) for n in STATIC] + [watch(i).scaled(3) for i in (0, 2, 4)] \
            + [ball(i).scaled(3) for i in (0, 2, 4)]
    pad = 24
    cell = max(max(b.w, b.h) for b in items) + pad
    cols = 5
    rows = -(-len(items) // cols)
    sheet = Bitmap(cols * cell + pad, rows * cell + pad, (0, 0))
    bg = (214, 214, 214, 255)
    sheet.px = [[bg] * sheet.w for _ in range(sheet.h)]
    for i, b in enumerate(items):
        ox = pad + (i % cols) * cell + (cell - pad - b.w) // 2
        oy = pad + (i // cols) * cell + (cell - pad - b.h) // 2
        for y in range(b.h):
            for x in range(b.w):
                if b.px[y][x][3]:
                    sheet.px[oy + y][ox + x] = b.px[y][x]
    return sheet.png()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content-size", type=int, choices=SIZES, default=2,
                    help="cursor scale for dist/userContent.css (default 2)")
    args = ap.parse_args()
    cursors = load_cursors()
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "chrome.css").write_text(chrome_css(cursors))
    (ROOT / "dist" / "userContent.css").write_text(content_css(cursors, args.content_size))
    (ROOT / "image.png").write_bytes(preview_png(cursors))
    print("wrote chrome.css, dist/userContent.css, image.png")


if __name__ == "__main__":
    main()
