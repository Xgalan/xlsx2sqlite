xlsx2sqlite
===========

.. image:: https://img.shields.io/pypi/v/xlsx2sqlite.svg
    :target: https://pypi.python.org/pypi/xlsx2sqlite
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/license/Xgalan/xlsx2sqlite
    :alt: GitHub license   
    :target: https://github.com/Xgalan/xlsx2sqlite/blob/master/LICENSE


.. image:: https://codecov.io/gh/Xgalan/xlsx2sqlite/branch/compat_py3.6-3.7/graph/badge.svg?token=R22KYIQ2UO
    :target: https://codecov.io/gh/Xgalan/xlsx2sqlite
    

Generate a Sqlite3 database from a Office Open XML file.
Read the
`xlsx2sqlite documentation <https://xlsx2sqlite.readthedocs.io/>`_.

Usage
-----

First create a .INI config file that you will pass as an argument to the
`xlsx2sqlite` command line tool. This will serve as a model to import data 
from the .xlsx file.

The INI file must contains this section:

- PATHS

Optional sections, see below:

- EXCLUDE

Example of a configuration:

.. code-block:: ini

    [PATHS]
    ; declare the paths of the files to be read.
    root_path = baserootpath/
    xlsx_file = %(root_path)s/exampletoimport.xlsx
    db_file = %(root_path)s/databasename.db
    db_url = sqlite:///%(db_file)s
    sql_views = %(root_path)s/views

    ; declare to import a worksheet like this :

    ; name of the worksheet to import
    [SheetName1]
    ; comma-separated list of the columns to import
    columns = Col1,Col2,Col3
    ; composite primary key is supported:
    primary_key = Col1,Col2

    [SheetName2]
        ; valid model keywords are:
        columns = Col1,Col2
        primary_key = id
        unique = Col2
        not_null = Col2
        ; add if the row with the header is not the first row of the worksheet
        header = 2

Optional "exclude" section, use if you don't want to import some section of the ini file, 
this is useful in example for co-exist with some other configuration file.

.. code-block:: ini

    [EXCLUDE]
        sections = SECTION1,section2,etc. ; use a list of comma-separated values.

Installation
------------

Install the release from PyPI:

.. code-block:: bash

    $ pip install xlsx2sqlite

Installing from source, a virtualenv is recommended:

.. code-block:: bash

    $ pip install --editable .

Requirements
^^^^^^^^^^^^

`xlsx2sqlite` is powered by `Click <https://click.palletsprojects.com/en/7.x/>`_
and `Tablib <http://docs.python-tablib.org/en/latest/>`_.

Compatibility
-------------

`xlsx2sqlite` is compatible with Python 3.7+.

Licence
-------

GPLv3

Authors
-------

`xlsx2sqlite` was written by `Erik Mascheri <erik.mascheri@gmail.com>`_.
