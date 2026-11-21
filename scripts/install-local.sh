#!/usr/bin/env bash
# Install the mod (browser UI + web pages) straight into a Zen profile, no store needed.
# Zen must be closed: it rewrites zen-themes.json on exit and would drop the mod.
# Usage: scripts/install-local.sh [size 1|2|3] [profile-dir]
set -euo pipefail
cd "$(dirname "$0")/.."
size="${1:-2}"
profiles="$HOME/Library/Application Support/zen/Profiles"
profile="${2:-$(ls -dt "$profiles"/*/prefs.js | head -1 | xargs dirname)}"   # most recently used profile

if pgrep -f "Zen.app/Contents/MacOS/zen" >/dev/null; then
  echo "Zen is running. Quit it (Cmd+Q) and re-run." >&2; exit 1
fi

python3 -I scripts/build.py --content-size "$size"
id="$(python3 -I -c 'import json;print(json.load(open("theme.json"))["id"])')"
dir="$profile/chrome/zen-themes/$id"
mkdir -p "$dir"
cp chrome.css preferences.json readme.md theme.json "$dir/"

json="$profile/zen-themes.json"; [ -e "$json" ] && cp "$json" "$json.bak"
python3 -I - "$json" <<'PY'
import json, sys, os
path = sys.argv[1]
mods = json.load(open(path)) if os.path.exists(path) else {}
mod = json.load(open("theme.json"))
mod["enabled"] = True
mods[mod["id"]] = mod
json.dump(mods, open(path, "w"), indent=2)
PY

dest="$profile/chrome/userContent.css"
[ -e "$dest" ] && [ ! -e "$dest.bak" ] && cp "$dest" "$dest.bak"
cp dist/userContent.css "$dest"
echo "Installed in: $profile"
echo "Start Zen, then pick size/loader in Settings > Mods > ClassicMacCursors."
