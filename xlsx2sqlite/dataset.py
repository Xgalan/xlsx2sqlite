# -*- coding: utf-8 -*-
""" Module for using tablib instances.
"""
import tablib

import xlsx2sqlite.import_export as im_ex


class Dataset:
    """Container class for tablib.Dataset instances."""

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
        if key not in self._tables:
            return False
        return self._tables[key]

    def __getitem__(self, key):
        return self._tables[key]

    def create_dataset(
        self, workbook=None, worksheet=None, subset_cols=None, header=None
    ):
        """Import the specified worksheet into the collection.

        :key workbook: Path of the xlsx file to open for import.
        :key worksheets: Name of the worksheet to be imported.
        :key subset: List of columns in the worksheet to consider for import.
        """
        table = im_ex.import_worksheet(workbook=workbook, worksheet=worksheet)
        for tbl_name, values in table.items():
            try:
                if header is not None:
                    row_nr = int(header[0]) - 1
                    if row_nr > 0:
                        values = values[row_nr:]
                    else:
                        print("Header row must be 1 or greater.")
                headers = values.pop(0)
                self._tables[tbl_name] = self._dataset(*values, headers=headers).subset(
                    cols=subset_cols[tbl_name]
                )
            except TypeError:
                print("Perhaps haven't you defined the header field on a model?")
