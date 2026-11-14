"""Wrapper: strips the site's YAML frontmatter, checks frontmatter values for dashes,
then runs the project lint on the body. Usage: python3 -I checkfile.py FILE.md"""
import sys, re, subprocess, tempfile, pathlib, os
p = pathlib.Path(sys.argv[1]); t = p.read_text(encoding="utf-8")
fm_issues = []
body = t
if t.startswith("---\n"):
    end = t.find("\n---\n", 4)
    if end == -1:
        print("FAILED: frontmatter not closed"); sys.exit(1)
    fm = t[4:end]; body = t[end+5:]
    DASH = "-‐‑‒–—―−﹘﹣－"
    for line in fm.splitlines():
        k, _, v = line.partition(":")
        if any(c in DASH for c in v):
            fm_issues.append(f"DASH in frontmatter value: {line[:100]}")
        if k.strip() == "title" and (":" in v or "?" in v and False):
            fm_issues.append(f"Title contains a colon; use a plain title or the subtitle key: {line[:100]}")
        if k.strip() == "title" and len(v.split()) > 10:
            fm_issues.append(f"Title longer than ten words: {line[:100]}")
else:
    print("NOTE: no frontmatter present")
here = os.path.dirname(os.path.abspath(__file__))
with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
    f.write(body); tmp = f.name
r = subprocess.run([sys.executable, "-I", os.path.join(here, "lint.py"), tmp], capture_output=True, text=True)
print(r.stdout, end=""); print(r.stderr, end="")
os.unlink(tmp)
if fm_issues:
    print("FRONTMATTER FAILED:"); print("\n".join(fm_issues)); sys.exit(1)
sys.exit(r.returncode)
