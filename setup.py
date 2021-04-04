__license__ = '''
This file is part of xlsx2sqlite.
xlsx2sqlite is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of
the License, or (at your option) any later version.
xlsx2sqlite is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General
Public License along with xlsx2sqlite.  If not, see
<http://www.gnu.org/licenses/>.
'''
# pylint: disable=bad-whitespace

import setuptools
from xlsx2sqlite.__version__ import __version__


setuptools.setup(
    name="xlsx2sqlite",
    version=__version__,
    url="https://github.com/Xgalan/xlsx2sqlite",
    author="Erik Mascheri",
    author_email="erik.mascheri@gmail.com",
    license='GPLv3',
    description="Generate a Sqlite3 database from a Office Open XML file.",
    long_description=open('README.rst').read(),
    packages=setuptools.find_packages(),
    install_requires=[
        "openpyxl>=3,<3.1",
        "tablib==3.0.0",
        "Click>=7,<8",
        "colorama"
    ],
    include_package_data=True,
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    entry_points='''
        [console_scripts]
        xlsx2sqlite=xlsx2sqlite.cli:cli
    ''',
)
