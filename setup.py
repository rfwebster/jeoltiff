from cx_Freeze import setup, Executable

import os
import sys

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')


base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

addtional_mods = ['numpy.core._methods', 'numpy.lib.format', 'tifffile']


executables = [Executable("jeoltiff.py", base=base)]

packages = ["idna"]
options = {
    'build_exe': {
        'includes': addtional_mods,
        'packages': packages,
    },

}

setup(
    name = "jeoltiff",
    options = options,
    version = "1.19.11",
    description = 'Extracts and saves JEOL Tiffs ad Gatan readable tiffs',
    executables = executables
)