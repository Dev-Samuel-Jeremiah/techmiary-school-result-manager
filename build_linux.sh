#!/usr/bin/env bash
# =========================================================================
#  Techmiary School Result Manager - Linux build
#  Run ON A LINUX PC (needs internet the first time):   ./build_linux.sh
#
#  It produces, in the "Installers/Linux" folder:
#    1. techmiary-school-result-manager_<version>_amd64.deb
#         double-click to install (Ubuntu, Debian, Mint, Zorin, ...)
#    2. TechmiarySchoolResultManager-<version>-x86_64
#         single standalone file - make it executable and double-click
#    3. TechmiarySchoolResultManager-<version>-linux-x64.tar.gz
#         for any distro: extract, then run ./install.sh (no admin needed)
#
#  Needs: python3 with venv   (Ubuntu/Debian:  sudo apt install python3-venv)
# =========================================================================
set -e
cd "$(dirname "$0")"
SRC="$(pwd)"
OUTDIR="${OUTPUT_DIR:-$SRC/../Installers/Linux}"
mkdir -p "$OUTDIR"
OUTDIR="$(cd "$OUTDIR" && pwd)"

# ---- 1. Private build environment ---------------------------------------
if [ ! -x .venv-build/bin/python ]; then
  python3 -m venv .venv-build
fi
VPY="$SRC/.venv-build/bin/python"
"$VPY" -m pip install --upgrade pip
"$VPY" -m pip install -r requirements.txt pyinstaller

# ---- 2. Name and version from app/branding.py -----------------------------
VER="$("$VPY" tools/make_version_info.py get VERSION)"
EXE="$("$VPY" tools/make_version_info.py get EXE)"
PRODUCT="$("$VPY" tools/make_version_info.py get PRODUCT)"
COMPANY="$("$VPY" tools/make_version_info.py get COMPANY)"
URL="$("$VPY" tools/make_version_info.py get URL)"
echo "Building $EXE version $VER ..."

# ---- 3. Program folder ----------------------------------------------------
"$VPY" -m PyInstaller --noconfirm --clean --windowed \
  --name "$EXE" \
  --add-data "app/icon.png:." \
  --paths app \
  app/main.py

# ---- 4. Single standalone file --------------------------------------------
"$VPY" -m PyInstaller --noconfirm --onefile --windowed \
  --name "$EXE-$VER-x86_64" \
  --add-data "app/icon.png:." \
  --paths app \
  --distpath build/onefile --workpath build/onefile-work \
  app/main.py
cp "build/onefile/$EXE-$VER-x86_64" "$OUTDIR/"
chmod +x "$OUTDIR/$EXE-$VER-x86_64"

# ---- 5. tar.gz with install.sh (any distro, no admin) ---------------------
PKG="build/$EXE-$VER-linux-x64"
rm -rf "$PKG" && mkdir -p "$PKG"
cp -r "dist/$EXE" "$PKG/program"
cp app/icon.png "$PKG/icon.png"
cp installer/linux/install.sh installer/linux/uninstall.sh "$PKG/"
chmod +x "$PKG/install.sh" "$PKG/uninstall.sh"
tar -C build -czf "$OUTDIR/$EXE-$VER-linux-x64.tar.gz" "$EXE-$VER-linux-x64"

# ---- 6. .deb package ------------------------------------------------------
if command -v dpkg-deb >/dev/null 2>&1; then
  DEB="build/deb"
  rm -rf "$DEB"
  mkdir -p "$DEB/DEBIAN" "$DEB/opt/techmiary-school-result-manager" \
           "$DEB/usr/bin" "$DEB/usr/share/applications" \
           "$DEB/usr/share/icons/hicolor/256x256/apps"
  cp -r "dist/$EXE/." "$DEB/opt/techmiary-school-result-manager/"
  ln -s "/opt/techmiary-school-result-manager/$EXE" "$DEB/usr/bin/techmiary-school-result-manager"
  cp app/icon.png "$DEB/usr/share/icons/hicolor/256x256/apps/techmiary-school-result-manager.png"
  cat > "$DEB/usr/share/applications/techmiary-school-result-manager.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$PRODUCT
Comment=Student results for primary and secondary schools - $COMPANY
Exec=/opt/techmiary-school-result-manager/$EXE
Icon=techmiary-school-result-manager
Terminal=false
Categories=Education;Office;
EOF
  SIZE="$(du -sk "$DEB" | cut -f1)"
  cat > "$DEB/DEBIAN/control" <<EOF
Package: techmiary-school-result-manager
Version: $VER
Section: education
Priority: optional
Architecture: amd64
Installed-Size: $SIZE
Depends: libxcb-cursor0, libxkbcommon-x11-0, libegl1
Maintainer: $COMPANY <info@techmiary.tech>
Homepage: $URL
Description: $PRODUCT
 Register students, enter CA and exam scores and print term results
 for primary and secondary schools. By $COMPANY - www.techmiary.tech
EOF
  find "$DEB" -type d -exec chmod 755 {} +
  dpkg-deb --root-owner-group --build "$DEB" \
    "$OUTDIR/techmiary-school-result-manager_${VER}_amd64.deb"
else
  echo "dpkg-deb not found - skipping the .deb package."
fi

echo
echo "====================================================================="
echo " Done. Your Linux files are in: $OUTDIR"
ls -1 "$OUTDIR"
echo "====================================================================="
