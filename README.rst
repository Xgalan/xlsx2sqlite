xlsx2sqlite
===========

.. image:: https://img.shields.io/pypi/v/xlsx2sqlite.svg
    :target: https://pypi.python.org/pypi/xlsx2sqlite
    :alt: Latest PyPI version

.. image:: .png
   :target:
   :alt: Latest Travis CI build status

Generate a Sqlite3 database from a Office Open XML file.

Usage
-----

First create a .INI config file that you will pass as an argument to the
`xlsx2sqlite` command line interface.

`xlsx2sqlite` uses the `configparser` module from the Python Standard Library.

This is an example of a configuration file:

``
[PATHS]
; declare the paths of the files to be read.
root_path = /home/erik/Documenti/movpac
xlsx_file = %(root_path)s/MOVPAC.xlsx
db_file = %(root_path)s/test.db
db_url = sqlite:///%(db_file)s
sql_views = %(root_path)s/views

[WORKSHEETS]
; list the worksheets to import from the xlsx file.
; use comma-separated values.
names = MOVPAC,Test
; specify the columns to import from the worksheets, declare as:
; WorksheetName_columns equal to comma-separated values
MOVPAC_columns = Descrizione pacco,Codice articolo,Descrizione,U.M.,Quantità,Data ult. agg.,Anno Doc.
Test_columns = Codice articolo,U.M.,Quantità

[CONSTRAINTS]
; declare the relationships, if any, between tables
; this definitions will be translated as foreign keys
; on the database tables.
; it's possible to define uniqueness of value on a column.
Test_UNIQUE = Codice articolo
``

Installation
------------

Installing from source:

.. code-block:: bash

    $ python setup.py install

Requirements
^^^^^^^^^^^^

Compatibility
-------------

`xlsx2sqlite` is compatible with Python 3.4+.

Licence
-------

GPLv3

Authors
-------

`xlsx2sqlite` was written by `Erik Mascheri <erik_mascheri@fastmail.com>`_.
