#!/usr/bin/env python3
"""Point theme.json at your GitHub repo and write zen-mod-import.json.

Zen's Settings > Mods > "Import mod" reads a JSON object {id: theme.json entry}
and downloads style/readme/preferences from the entry's HTTPS URLs, so the repo
must be public.

Usage: python3 scripts/make-import.py GITHUB_USER [REPO] [BRANCH]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
user = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else "zen-classic-mac-cursors"
branch = sys.argv[3] if len(sys.argv) > 3 else "main"
raw = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}"

theme = json.loads((ROOT / "theme.json").read_text())
theme.update(
    homepage=f"https://github.com/{user}/{repo}",
    style=f"{raw}/chrome.css",
    readme=f"{raw}/readme.md",
    image=f"{raw}/image.png",
    preferences=f"{raw}/preferences.json",
    author=user,
)
(ROOT / "theme.json").write_text(json.dumps(theme, indent=4) + "\n")
(ROOT / "zen-mod-import.json").write_text(json.dumps({theme["id"]: theme}, indent=2) + "\n")
print(f"theme.json updated, wrote zen-mod-import.json ({raw})")
