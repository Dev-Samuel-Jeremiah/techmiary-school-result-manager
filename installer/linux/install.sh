#!/usr/bin/env bash
# Installs Techmiary School Result Manager for the current user (no admin needed).
# Run it again with a newer version to upgrade - the school's data is kept.
set -e
cd "$(dirname "$0")"
NAME="Techmiary School Result Manager"
EXE="TechmiarySchoolResultManager"
DEST="$HOME/.local/opt/techmiary-school-result-manager"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/256x256/apps"

rm -rf "$DEST"
mkdir -p "$DEST" "$APPS" "$ICONS" "$HOME/.local/bin"
cp -r program/. "$DEST/"
chmod +x "$DEST/$EXE"
cp icon.png "$ICONS/techmiary-school-result-manager.png"
ln -sf "$DEST/$EXE" "$HOME/.local/bin/techmiary-school-result-manager"

DESKTOP_FILE="$APPS/techmiary-school-result-manager.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$NAME
Comment=Student results for primary and secondary schools - Techmiary Technology Concept
Exec=$DEST/$EXE
Icon=$ICONS/techmiary-school-result-manager.png
Terminal=false
Categories=Education;Office;
EOF
chmod +x "$DESKTOP_FILE"

# Desktop shortcut, if there is a Desktop folder
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
if [ -d "$DESK" ]; then
  cp "$DESKTOP_FILE" "$DESK/"
  chmod +x "$DESK/techmiary-school-result-manager.desktop"
  gio set "$DESK/techmiary-school-result-manager.desktop" metadata::trusted true 2>/dev/null || true
fi
update-desktop-database "$APPS" 2>/dev/null || true

echo "$NAME installed. Find it in your applications menu."
