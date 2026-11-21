#!/usr/bin/env bash
# Install the web-page cursors (dist/userContent.css) into a Zen profile.
# Zen mods only style the browser UI; page content needs userContent.css.
# Usage: scripts/install-content.sh [1|2|3] [profile-dir]
set -euo pipefail
cd "$(dirname "$0")/.."
size="${1:-2}"
profiles="$HOME/Library/Application Support/zen/Profiles"
profile="${2:-}"
if [ -z "$profile" ]; then
  profile="$(ls -dt "$profiles"/*/ | head -1)"   # most recently used profile
  profile="${profile%/}"
fi
python3 -I scripts/build.py --content-size "$size"
mkdir -p "$profile/chrome"
dest="$profile/chrome/userContent.css"
[ -e "$dest" ] && [ ! -e "$dest.bak" ] && cp "$dest" "$dest.bak"
cp dist/userContent.css "$dest"
echo "Installed to: $dest"
echo "Restart Zen. Needs toolkit.legacyUserProfileCustomizations.stylesheets = true in about:config."
