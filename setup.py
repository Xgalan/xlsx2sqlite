# -*- coding: utf-8 -*-
__license__ = """
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
"""
# pylint: disable=bad-whitespace

import setuptools

from xlsx2sqlite.__version__ import __version__

setuptools.setup(
    name="xlsx2sqlite",
    version=__version__,
    url="https://github.com/Xgalan/xlsx2sqlite",
    author="Erik Mascheri",
    author_email="erik.mascheri@gmail.com",
    license="GPLv3",
    keywords="xlsx2sqlite, sqlite3",
    description="Generate a Sqlite3 database from a Office Open XML file.",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    packages=setuptools.find_packages(),
    install_requires=[
        "openpyxl>=3,<3.1",
        "tablib>=3.0.0,<=3.1.0",
        "Click>=7.1,<8.1",
        "colorama",
        "cached-property;python_version<'3.8'",
    ],
    extras_require={
        "docs": ["Sphinx", "sphinx-click>=2.7,<3.1", "sphinx-rtd-theme==1.0.0"],
        "tests": ["pytest>=6,<7", "coverage", "pytest-cov", "pytest-random-order"],
        "code_audit": ["black", "isort"],
        "compile": ["wheel", "nuitka", "zstandard", "build", "twine"],
    },
    include_package_data=True,
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "xlsx2sqlite = xlsx2sqlite.scripts.console:console",
        ]
    },
)
