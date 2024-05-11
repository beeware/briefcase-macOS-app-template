from pathlib import Path


BIN_PATH = Path("{{ cookiecutter.formal_name }}.app/Contents/MacOS")

# Rename the stub binary we want to "Stub""
STUB_PATH = (
    BIN_PATH
    / "{% if cookiecutter.console_app %}Console{% else %}GUI{% endif %}-Stub-{{ cookiecutter.python_version|py_tag }}"
)
STUB_PATH.rename(BIN_PATH / "Stub")

# Delete all stubs that aren't for the Python version and app type
# that we are targeting
for stub in BIN_PATH.glob("*-Stub-*"):
    stub.unlink()
