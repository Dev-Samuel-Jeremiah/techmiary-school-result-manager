"""
Writes build/version_info.txt (the "Details" tab of the Windows .exe:
company name, product name, version) from app/branding.py.
Also prints values the build scripts need:  python tools/make_version_info.py get VERSION
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "app"))
import branding  # noqa: E402

if len(sys.argv) == 3 and sys.argv[1] == "get":
    print({"VERSION": branding.APP_VERSION,
           "EXE": branding.EXE_NAME,
           "PRODUCT": branding.PRODUCT_NAME,
           "COMPANY": branding.COMPANY_NAME,
           "URL": branding.COMPANY_URL}[sys.argv[2]])
    sys.exit(0)

parts = [int(p) for p in (branding.APP_VERSION.split(".") + ["0", "0", "0"])[:4]]
v = tuple(parts)
text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{branding.COMPANY_NAME}'),
      StringStruct('FileDescription', '{branding.PRODUCT_NAME}'),
      StringStruct('FileVersion', '{branding.APP_VERSION}'),
      StringStruct('InternalName', '{branding.EXE_NAME}'),
      StringStruct('LegalCopyright', '(c) {branding.COMPANY_NAME} - {branding.COMPANY_WEBSITE}'),
      StringStruct('OriginalFilename', '{branding.EXE_NAME}.exe'),
      StringStruct('ProductName', '{branding.PRODUCT_NAME}'),
      StringStruct('ProductVersion', '{branding.APP_VERSION}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
out_dir = os.path.join(HERE, "..", "build")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "version_info.txt"), "w", encoding="utf-8") as f:
    f.write(text)
print("version_info.txt written")
