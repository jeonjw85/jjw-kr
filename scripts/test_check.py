#!/usr/bin/env python3
"""scripts/check.py 자체를 검증한다."""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check.py"
SUFFIX = "..."

PUBLIC = [
    "Affiliate-Studio", "AIJ", "AutoShorts", "gitchess", "hermes-mail-notifier",
    "learn-elixir-with-algorithm", "rapid-photo-web", "refpin", "AgentDock",
    "CannyGit", "DockSnap", "kenfold", "MacSloth", "ytlr", "2FAC", "e2ee-kit",
    "hf2mlx", "homebrew-tap", "Ksecret", "profNote", "Radar",
    "2FA-Authenticator-Desktop", "arduino-smartFarm", "my", "PySniff",
    "SPP-link-app", "youtube-music-tunnel", "pro-neighbor", "grassMaker",
    "OpenRoom",
]
MASKED = ["S" + SUFFIX, "G" + SUFFIX, "n" + SUFFIX] + [
    chr(ord("a") + i) + SUFFIX for i in range(24)
]

def build(public=PUBLIC, masked=MASKED, extra=""):
    rows = "".join(
        f'<li class="proj"><a class="proj-name" href="https://github.com/jeonjw85/{n}">{n}</a></li>\n'
        for n in public
    )
    rows += "".join(
        f'<li class="proj is-private"><span class="proj-name">{m}</span></li>\n'
        for m in masked
    )
    return (
        "<!DOCTYPE html><html lang=\"ko\"><body>"
        '<section id="projects"></section>'
        '<section id="archive"></section>'
        + "".join(f'<span data-ko="{i}" data-en="{i}"></span>' for i in range(8))
        + extra
        + "<ul>"
        + rows
        + "</ul></body></html>"
    )

def full_fixture():
    return build(PUBLIC + ["Paper", "ARTEX-ko"], MASKED)

def run(target):
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "index.html").write_text(target, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CHECK), str(tmp / "index.html")],
            capture_output=True,
            text=True,
        )
    finally:
        shutil.rmtree(tmp)

def test_good_fixture_passes():
    r = run(full_fixture())
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK:" in r.stdout

def test_missing_section_fails():
    r = run(full_fixture().replace('id="projects"', 'id="nope"'))
    assert r.returncode == 1
    assert "#projects" in r.stdout

def test_wrong_row_count_fails():
    r = run(full_fixture().replace('<li class="proj">', '<li class="projX">', 1))
    assert r.returncode == 1
    assert "59" in r.stdout

def test_unlisted_name_is_a_leak():
    r = run(full_fixture().replace("S" + SUFFIX, "SecretRepo"))
    assert r.returncode == 1
    assert "SecretRepo" in r.stdout

def test_partial_mask_is_rejected():
    r = run(full_fixture().replace("G" + SUFFIX, "GyZ..."))
    assert r.returncode == 1
    assert "마스킹 형식" in r.stdout

def test_leaked_fork_fails():
    r = run(full_fixture().replace("<body>", '<body><a href="https://github.com/jeonjw85/askimo">x</a>'))
    assert r.returncode == 1, r.stdout
    assert "askimo" in r.stdout

def test_fork_name_in_prose_is_fine():
    r = run(full_fixture().replace("<body>", "<body><p>askimo is a fork</p>"))
    assert r.returncode == 0, r.stdout

def test_removed_dependency_leftover_fails():
    r = run(full_fixture().replace("<body>", "<body><script>three</script>"))
    assert r.returncode == 1
    assert "three" in r.stdout

def test_canvas_leftover_fails():
    r = run(full_fixture().replace("<body>", '<body><canvas id="bg"></canvas>'))
    assert r.returncode == 1
    assert "캔버스" in r.stdout

def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
