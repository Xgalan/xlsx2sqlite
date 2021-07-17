.. xlsx2sqlite documentation master file, created by
   sphinx-quickstart on Wed Oct 31 13:06:59 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to xlsx2sqlite's documentation!
=======================================

xlsx2sqlite generates a Sqlite3 database from a Office Open XML file.

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


API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   cli.rst
   controller.rst
   db_wrapper.rst
   field_factory.rst
   utils.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
