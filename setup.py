import os
from setuptools import setup

APP = ['rumps_app.py']
DATA_FILES = ['icon.icns', 'iconbw.icns', 'api_show.json']
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icon.icns',
    'plist': {
    'CFBundleName': 'MackingJAI',
    'CFBundleDisplayName': 'MackingJAI',
    'CFBundleIdentifier': 'io.github.0ssamaak0.MackingJAI',
        'CFBundleVersion': '0.1.0',
        'LSUIElement': True,
    },
    # Basic packages needed
    'packages': ['flask', 'rumps'],
    # Explicit includes
    'includes': ['re', 'threading', 'signal', 'subprocess', 'json', 'jsonify', 'werkzeug'],
    # Add this to create a more verbose output
    'verbose': True,
    # Don't strip debug symbols
    'strip': False,
    'frameworks': [os.path.join(os.environ.get('CONDA_PREFIX', ''), 'lib', 'libffi.8.dylib')],
}

setup(
    app=APP,
    name='MackingJAI',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    py_modules=['server'],
)