xlsx2sqlite
===========

.. image:: https://img.shields.io/pypi/v/xlsx2sqlite.svg
    :target: https://pypi.python.org/pypi/xlsx2sqlite
    :alt: Latest PyPI version


Generate a Sqlite3 database from a Office Open XML file.
Read the
`xlsx2sqlite documentation <https://xlsx2sqlite.readthedocs.io/>`_.

Usage
-----

First create a .INI config file that you will pass as an argument to the
`xlsx2sqlite` command line tool. `xlsx2sqlite` uses the `configparser`
module from the Python Standard Library.

The INI file must contains this sections:

- PATHS
- WORKSHEETS

Optional section for defining database constraints:

- CONSTRAINTS

Example of a configuration:

.. code-block:: ini

    [PATHS]
    ; declare the paths of the files to be read.
    root_path = baserootpath/
    xlsx_file = %(root_path)s/exampletoimport.xlsx
    db_file = %(root_path)s/databasename.db
    db_url = sqlite:///%(db_file)s
    sql_views = %(root_path)s/views

    [WORKSHEETS]
    ; list the worksheets to import from the xlsx file.
    ; use comma-separated values.
    names = SheetName1,SheetName2
    ; specify the columns to import from the worksheets, declare as:
    ; WorksheetName_columns equal to comma-separated values
    SheetName1_columns = Col1,Col2,Col3
    SheetName2_columns = Col1,Col2,Col3


Optional constraints section, add if necessary:

.. code-block:: ini

    [CONSTRAINTS]
    ; As of now, supported constraints are UNIQUE and "custom" PRIMARY KEY.
    ; In example:
    ; worksheetname_UNIQUE equal to list of columns to be created
    ; with a UNIQUE constraint in the database.
    SheetName1_unique = Col1
    SheetName1_primarykey = custom_id
    ; Can define a primary key on an existing column, of course even
    ; a non integer primary key, if supported by Sqlite.
    SheetName2_primarykey = Col1


Installation
------------

Install the release from PyPI:

..code-block:: bash

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

`xlsx2sqlite` is compatible with Python 3.6+.

Licence
-------

GPLv3

Authors
-------

`xlsx2sqlite` was written by `Erik Mascheri <erik.mascheri@gmail.com>`_.
