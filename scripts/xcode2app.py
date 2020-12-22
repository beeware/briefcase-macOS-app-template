#!/usr/bin/env python3

import os
import json
import argparse
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode

from cookiecutter.main import cookiecutter


parser = argparse.ArgumentParser(description='Create app template from Xcode template')
parser.add_argument('--python-version', help='Python version to build')
parser.add_argument('--xcode-template-path', help='Path to Xcode template')

args = parser.parse_args()

# ---- setup build paths ---------------------------------------------------------------

with open(args.xcode_template_path + '/cookiecutter.json') as f:
    cookiecutter_json = json.load(f)

project_path = Path('project')
support_path = project_path / cookiecutter_json['formal_name'] / 'Support'
project_file_path = project_path / cookiecutter_json['formal_name'] / (cookiecutter_json['formal_name'] + '.xcodeproj')
app_path = project_path / cookiecutter_json['formal_name'] / 'build'/ 'Release' / (cookiecutter_json['formal_name'] + '.app')

contents_dir = app_path / 'Contents'
executable_dir = app_path / 'Contents' / 'MacOS'
resource_dir = app_path / 'Contents' / 'Resources'

# ---- create Xcode project from cookiecutter ------------------------------------------

cookiecutter(args.xcode_template_path, output_dir=project_path, no_input=True)

# download support package
support_package_url_query = [
    ('platform', 'macos'),
    ('version', args.python_version),
]
support_package_url = 'https://briefcase-support.org/python?{query}'.format(query=urlencode(support_package_url_query))
tmpfile = project_path / os.path.basename(support_package_url)
subprocess.run(['curl', '-L', support_package_url, '--output', str(tmpfile)], check=True)
shutil.unpack_archive(tmpfile, extract_dir=support_path)

# build project locally
subprocess.run(
    [
        'xcodebuild',
        '-project', str(project_file_path),
        '-quiet',
        '-configuration', 'Release',
        'build'
    ],
    check=True,
)

# ---- create app template from Xcode build --------------------------------------------

app_template_path = Path('app-template-build')

# replace Info.plist
shutil.copy(args.xcode_template_path + '/{{ cookiecutter.formal_name }}/{{ cookiecutter.formal_name }}/Info.plist', contents_dir / 'Info.plist')

# rename files
shutil.move(executable_dir / cookiecutter_json['formal_name'], executable_dir / '{{ cookiecutter.formal_name }}')
shutil.move(resource_dir / (cookiecutter_json['formal_name'] + '.icns'), resource_dir / '{{ cookiecutter.formal_name }}.icns')

# remove Python lib
shutil.rmtree(resource_dir / 'Python')

# put everything together
shutil.copytree('app-template', app_template_path)
shutil.move(app_path, app_template_path / '{{ cookiecutter.formal_name }}' / '{{ cookiecutter.formal_name }}.app')

