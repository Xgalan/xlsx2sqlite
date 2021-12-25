# -*- coding: utf-8 -*-
""" Module for using tablib instances.
"""
import tablib

from xlsx2sqlite.import_export import import_worksheets


class Dataset:
    """Container class for tablib.Dataset instances.
    """

    _tables = dict()
    _dataset = tablib.Dataset

    def __iter__(self):
        return iter(self._tables)

    def get(self, table):
        """Get a table by name.

        :param table: Name of the table.
        """
        return self._tables.get(table, None)

    def __contains__(self, key):
        return self._tables[key]

    def __getitem__(self, key):
        return self._tables[key]

    def import_tables(self, workbook=None, worksheets=None, subset_cols=None, headers=None):
        """Import the specified worksheets into the tables collection.

        :key workbook: Path of the xlsx file to open for import.
        :key worksheets: List of the worksheets to be imported.
        :key subset: List of columns in the worksheet to consider for import.
        """
        tables = import_worksheets(workbook=workbook, worksheets=worksheets)
        for tbl_name,values in tables.items():
            if headers:
                tablename = tbl_name.lower() + '_header'
                if tablename in headers:
                    row_nr = int(headers[tablename]) - 1
                    if row_nr > 0:
                        values = values[row_nr:]
                    else:
                        print('Header row must be 1 or greater.')
            header = values.pop(0)
            self._tables[tbl_name] = self._dataset(
                *values, headers=header
            ).subset(
                cols=subset_cols[tbl_name]
            )

    def create_empty_table(self, tablename=None, headers=None):
        """Creates a tablib.Dataset instance in the collection.

        :key tablename: Name of the table to be created.
        :key headers: List of labels for the table header.
        :returns: An empty table.
        :rtype: tablib.Dataset
        """
        self._tables[tablename] = self._dataset(headers=headers)
        return self._tables[tablename]

    def values_to_table(self, tablename=None, values=None):
        """Append values to a tablib.Dataset table in the collection.

        :key tablename: Name of the table.
        :key values: List of values to append.
        """
        [self._tables[tablename].append(val) for val in values]
