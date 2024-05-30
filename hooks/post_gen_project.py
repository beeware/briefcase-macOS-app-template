from pathlib import Path

# The codesign utility in recent macOS fails with obscure errors when presented with
# CRLF line endings, but in some configurations (e.g. global `core.autocrlf=true`)
# git may have checked out this repo in a way that put CRLF line endings in Entitlements.plist.
# The following is thus a no-op most of the time, but it's a simple rewrite of a small file.
ENTITLEMENTS_PATH = Path("Entitlements.plist")
# This implicitly uses "universal" newlines mode.
xml_content = ENTITLEMENTS_PATH.read_text()
ENTITLEMENTS_PATH.open('w', newline='\n').write(xml_content)

INFO_PATH = Path("{{ cookiecutter.formal_name }}.app/Contents/Info.plist")
info_content = INFO_PATH.read_text()
INFO_PATH.open('w', newline='\n').write(info_content)
