#!/usr/bin/env python3
"""법적 문서의 문구가 git에 커밋된 직전 버전과 같은지 확인한다.

사용:
    python3 scripts/check_legal_copy.py [BASE_COMMIT]

인자를 주지 않으면 HEAD와 작업 트리를 비교한다.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["policy.html", "terms.html", "policy/paper.html"]
SCOPE = re.compile(r"본 (?:방침|약관)은 .*?적용됩니다\.")


def body_of(html):
    m = re.search(r"<body[^>]*>([\s\S]*?)</body>", html, re.I)
    return m.group(1) if m else html


def strip(html):
    t = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    t = re.sub(r"<script[\s\S]*?</script>", " ", t, flags=re.I)
    t = re.sub(r"<head[\s\S]*?</head>", " ", t, flags=re.I)
    t = re.sub(r'<a class="back"[\s\S]*?</a>', " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = " ".join(t.split())
    return SCOPE.sub(" ", t).strip()


def committed(src, ref):
    html = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{ref}:{src}"], text=True
    )
    return strip(re.split(r"<hr\s*/?>", body_of(html))[0])


def working(src):
    html = (ROOT / src).read_text(encoding="utf-8")
    b = body_of(html)
    b = re.sub(r'<a class="back"[\s\S]*?</a>', " ", b)
    b = re.sub(r'<p class="scope"[\s\S]*?</p>', " ", b)
    b = re.sub(r"<hr[\s\S]*", " ", b)
    return strip(b)


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    ok = True
    for src in FILES:
        a, b = committed(src, ref).split(), working(src).split()
        if a != b:
            ok = False
            print(f"FAIL {src}: 문구가 {ref}와 다르다")
            for line in list(difflib.unified_diff(a, b, n=2, lineterm=""))[:40]:
                print(line)
        else:
            print(f"OK {src} ({len(b)} tokens)")
    if not ok:
        sys.exit(1)
    print(f"OK: 세 문서의 문구가 {ref}와 동일")


if __name__ == "__main__":
    main()
