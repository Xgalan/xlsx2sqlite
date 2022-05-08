.. xlsx2sqlite documentation master file, created by
   sphinx-quickstart on Wed Oct 31 13:06:59 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to xlsx2sqlite's documentation!
=======================================

xlsx2sqlite generates a Sqlite3 database from a Office Open XML file.

Installation
------------

xlsx2sqlite is available on PYPI, so using pip:

.. code-block:: bash

    pip install xlsx2sqlite

Or clone the repository on github (Xgalan/xlsx2sqlite) and then install using pip:

.. code-block:: bash

    pip install --editable .

Launch the command above in the same directory as "setup.py".

Usage
-----

First create a .INI config file that you will pass as an argument to the
`xlsx2sqlite` command line tool. `xlsx2sqlite` uses the `configparser`
module from the Python Standard Library.

The INI file must contains this section:

- PATHS

and a section for every worksheet you wish to import, i.e.:

[SheetName1]

[SheetName2]


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

    [SheetName1]
    ; every section name must be equal to the name of the worksheet as in the workbook.
    ; use comma-separated values for defining the values of the keywords.
    ; valid keywords are: columns, primary_key, unique, not_null.
    columns = Col1,Col2,Col3 ; declare the columns to import
    primary_key = id         ; declare the name of the primary key
    unique = Col1            ; declare the columns which will be created with a UNIQUE clause
    not_null = Col1          ; declare the columns which will be created with a NOT NULL clause
    header = 1               ; declare if the row containing the header of the table is not the first



Optional "exclude" section, use if you don't want to import some section of the ini file, 
this is useful in example for co-exist with some other configuration file.

.. code-block:: ini

    [EXCLUDE]
        sections = SECTION1,section2,etc. ; use a list of comma-separated values.


API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation.rst
   cli.rst
   controller.rst
   db_wrapper.rst
   constraint_factory.rst
   field_factory.rst
   import_export.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
