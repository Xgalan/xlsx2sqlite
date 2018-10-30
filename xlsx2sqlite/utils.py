# -*- coding: utf-8 -*-
"""Utilities for the command line interface.

The :func:`export_worksheet` function creates a xlsx file with a worksheet
containing table data, it uses the `openpyxl` package.

The :func:`import_worksheets` function is useful for importing specified
worksheets from a xlsx file, it uses the 'openpyxl' package.

"""
import configparser

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
    # load a xlsx file.
    wb = load_workbook(filename=workbook,
                       read_only=True)
    worksheets = [wb[ws] for ws in worksheets]
    # import tables from imported worksheets
    tables = {ws.title: [tuple([cell.value for cell in row])
                         for row in ws.rows] for ws in worksheets}
    wb.close()
    return tables


class ConfigModel:
    COMMA_DELIM = ','
    
    def __init__(self, options=None):
        self.options = options
        self._parser = configparser.ConfigParser()

    def __iter__(self):
        for option in self.options:
            yield option

    def sections(self):
        return [section for section in self.options]

    def get(self, option):
        try:
            if option in self.options:
                return self.options[option]
            else:
                return [v[option]
                        for k,v in self.options.items() if option in v][0]
        except KeyError as e:
            raise KeyError((str(e) + " not in the options list."))

    def get_imports(self):
        names = list(self.get('names').split(self.COMMA_DELIM))
        return {'worksheets': names,
                'subset_cols': dict([(name, list(
                    self.get(str(name + '_columns').lower()).split(
                        self.COMMA_DELIM))) for name in names])
                }

    def import_config(self, ini):
        self._parser.read(ini)
        self.options = {k:dict(self._parser[k])
                        for k in self._parser.sections()}
