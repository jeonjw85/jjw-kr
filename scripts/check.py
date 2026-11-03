#!/usr/bin/env python3
"""jjw.kr 허브의 구조와 마스킹, 의존성을 검증한다."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "index.html"
index = TARGET.read_text(encoding="utf-8")

PUBLIC_NAMES = {
    "Affiliate-Studio", "AIJ", "AutoShorts", "gitchess", "hermes-mail-notifier",
    "learn-elixir-with-algorithm", "rapid-photo-web", "refpin", "AgentDock",
    "CannyGit", "DockSnap", "kenfold", "MacSloth", "ytlr", "2FAC", "e2ee-kit",
    "hf2mlx", "homebrew-tap", "Ksecret", "profNote", "Radar",
    "2FA-Authenticator-Desktop", "arduino-smartFarm", "my", "PySniff",
    "SPP-link-app", "youtube-music-tunnel", "pro-neighbor", "grassMaker",
    "OpenRoom",
    "Paper", "ARTEX-ko",
}

FORKS = ["tokenspeed", "rea", "OpenDots", "askimo", "OpenBot", "java-calculator-8"]

MASK_SUFFIX = "..."
problems = []

def fail(msg):
    problems.append(msg)

for anchor, label in [
    ("projects", "Projects"),
    ("archive", "Archive"),
]:
    if f'id="{anchor}"' not in index:
        fail(f"{label} 섹션(#{anchor})이 없다")

rows = re.findall(r'<li class="proj(?: is-private)?"', index)
if len(rows) != 59:
    fail(f"프로젝트 행이 {len(rows)}개다. 59개여야 한다")

names = re.findall(r'class="proj-name"[^>]*>([^<]*)<', index)
if len(names) != 59:
    fail(f"프로젝트 이름이 {len(names)}개다. 59개여야 한다")

masked = [n for n in names if n.endswith(MASK_SUFFIX)]
if len(masked) != 27:
    fail(f"마스킹된 이름이 {len(masked)}개다. 27개여야 한다")

for name in names:
    if name.endswith(MASK_SUFFIX):
        if not re.fullmatch(r"[A-Za-z0-9]" + re.escape(MASK_SUFFIX), name):
            fail(f"마스킹 형식이 잘못됐다: {name!r}")
        continue
    if name not in PUBLIC_NAMES:
        fail(f"공개 목록에 없는 이름이 노출됐다: {name}")

for name in names:
    if not name.endswith(MASK_SUFFIX) and not name:
        fail("빈 프로젝트 이름이 있다")

for fork in FORKS:
    if re.search(r"github\.com/jeonjw85/" + re.escape(fork) + r"(?![\w-])", index):
        fail(f"포크 레포가 노출됐다: {fork}")

for fork in FORKS:
    for name in names:
        if name == fork:
            fail(f"포크 레포가 목록에 있다: {fork}")

for gone in ["three", "open-meteo", "importmap", "modulepreload"]:
    if gone in index.lower():
        fail(f"제거 대상이 남아 있다: {gone}")

visible = re.sub(r"<script[\s\S]*?</script>", " ", index)
visible = re.sub(r"<style[\s\S]*?</style>", " ", visible)
visible = re.sub(r"<[^>]+>", " ", visible)
ALLOWED = set(" .,?!:;()[]{}<>/\\-+_=@#$%&*'\"|~`^")
decorative = {
    ch
    for ch in visible
    if not ch.isalnum() and not ch.isspace() and ch not in ALLOWED
}
if decorative:
    fail(f"장식 기호를 쓰지 않는다: {sorted(decorative)}")

if index.count("data-ko=") < 8:
    fail("KO/EN 토글용 data-ko 속성이 부족하다")

if "<canvas" in index.lower():
    fail("캔버스 배경이 남아 있다")

if problems:
    for p in problems:
        print(f"FAIL: {p}")
    sys.exit(1)

print("OK: 구조, 마스킹, 의존성 검증 통과")
