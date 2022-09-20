import os
from pathlib import Path


BIN_PATH = Path("{{ cookiecutter.formal_name }}.app/Contents/MacOS")

# Move the stub for the Python version into the final location
os.rename(BIN_PATH / 'Stub-{{ cookiecutter.python_version|py_tag }}', BIN_PATH / '{{ cookiecutter.formal_name }}')

# Delete all remaining stubs
for stub in BIN_PATH.glob("Stub-*"):
    os.unlink(stub)
