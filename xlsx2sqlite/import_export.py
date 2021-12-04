# -*- coding: utf-8 -*-
"""Utilities for importing or exporting xlsx files.

The :func:`export_worksheet` function creates a xlsx file with a worksheet
containing table data, it uses the `openpyxl` package.

The :func:`import_worksheets` function is useful for importing specified
worksheets from a xlsx file, it uses the `openpyxl` package.
"""
from openpyxl import load_workbook, Workbook



def export_worksheet(filename=None, ws_name=None, rows=None):
    """Export data as a xlsx worksheet file.

    :key filename: Full path of the xlsx file to be saved.
    :key ws_name: Name of the worksheet.
    :key rows: Iterable containing rows data to append to the worksheet.
    """
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title=ws_name)
    ws.append(rows.headers)
    [ws.append(row) for row in rows]
    wb.save(filename)


def import_worksheets(workbook=None, worksheets=None):
    """Import worksheets from a workbook using openpyxl.

    :key workbook: Name of the xlsx file to open read only.
    :key worksheets: Names of the worksheets to import.

    :returns: A representation of a table with data from the
              imported worksheets.
    """
    def reset_dimensions(worksheets):
        """Necessary as to not import a huge amount of empty cells.
        Call appropriate methods from openpyxl to set the correct dimensions of 
        the worksheets.
        """
        [ws.reset_dimensions() for ws in worksheets]
        [ws.calculate_dimension(force=True) for ws in worksheets]

    # load a xlsx file.
    wb = load_workbook(filename=workbook, read_only=True, keep_vba=False)
    if worksheets is not None:
        imported_worksheets = [wb[ws] for ws in worksheets]
        reset_dimensions(imported_worksheets)
    else:
        imported_worksheets = [wb[ws] for ws in wb.sheetnames]
        reset_dimensions(imported_worksheets)
    # import tables from imported worksheets
    tables = {
        ws.title: [tuple([cell.value for cell in row]) for row in ws.rows] for ws in imported_worksheets
    }
    wb.close()
    return tables
