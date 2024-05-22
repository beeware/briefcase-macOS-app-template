import os
from pathlib import Path


BIN_PATH = Path("{{ cookiecutter.formal_name }}.app/Contents/MacOS")

# Move the stub for the Python version into the final location
os.rename(BIN_PATH / 'Stub-{{ cookiecutter.python_version|py_tag }}', BIN_PATH / '{{ cookiecutter.formal_name }}')

# Delete all remaining stubs
for stub in BIN_PATH.glob("Stub-*"):
    os.unlink(stub)

# The codesign utility in recent macOS fails with obscure errors when presented with
# CRLF line endings, but in some configurations (e.g. global `core.autocrlf=true`)
# git may have checked out this repo in a way that put CRLF line endings in Entitlements.plist.
# The following is thus a no-op most of the time, but it's a simple rewrite of a small file.
ENTITLEMENTS_PATH = Path("Entitlements.plist")
# This implicitly uses "universal" newlines mode.
xml_content = ENTITLEMENTS_PATH.read_text()
ENTITLEMENTS_PATH.open('w', newline='\n').write(xml_content)

INFO_PATH = BIN_PATH.parent / 'Info.plist'
info_content = INFO_PATH.read_text()
INFO_PATH.open('w', newline='\n').write(info_content)
