#!/usr/bin/env bash
# Removes the program. The school's data (~/.local/share/TechmiarySchoolResultManager) is NOT deleted.
rm -rf "$HOME/.local/opt/techmiary-school-result-manager"
rm -f "$HOME/.local/share/applications/techmiary-school-result-manager.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/techmiary-school-result-manager.png"
rm -f "$HOME/.local/bin/techmiary-school-result-manager"
DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
rm -f "$DESK/techmiary-school-result-manager.desktop"
echo "Techmiary School Result Manager removed. Your data folder was kept."
