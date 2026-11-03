#!/usr/bin/env python3
"""index.html의 색 토큰 대비율이 WCAG AA를 만족하는지 검사한다."""
import re
import sys
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")

root = re.search(r":root\s*\{([\s\S]*?)\}", HTML).group(1)
TOKENS = dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{3,8})", root))

def rgb(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

def luminance(hex_color):
    def channel(v):
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = rgb(hex_color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def ratio(fg, bg):
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)

REQUIRED = {
    "--text": 7.0,
    "--dim": 4.5,
    "--faint": 4.5,
}
BACKGROUNDS = ["--bg"]

problems = []
for token, minimum in REQUIRED.items():
    if token not in TOKENS:
        problems.append(f"{token} 토큰이 없다")
        continue
    for bg_token in BACKGROUNDS:
        r = ratio(TOKENS[token], TOKENS[bg_token])
        if r < minimum:
            problems.append(f"{token} on {bg_token}: {r:.2f}:1 (최소 {minimum}:1)")
        else:
            print(f"OK {token} on {bg_token}: {r:.2f}:1")

if problems:
    for p in problems:
        print(f"FAIL {p}")
    sys.exit(1)

for m in re.finditer(r"([^{}]+)\{([^}]*opacity:\s*(\.\d+|0\.\d+)[^}]*)\}", HTML):
    selector, block, value = m.group(1).strip(), m.group(2), float(m.group(3))
    if value < 1 and "color" in block:
        problems.append(
            f"텍스트 요소에 opacity {value} 사용 (실효 대비 미달 위험): {selector}"
        )

if problems:
    for p in problems:
        print(f"FAIL {p}")
    sys.exit(1)

print("OK: 모든 색 토큰이 대비 기준을 만족")
