#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser

from openpyxl import load_workbook



COMMA_DELIM = ','


def import_worksheets(workbook=None, worksheets=None):
    # load a xlsx file.
    wb = load_workbook(filename=workbook,
                       read_only=True)
    # import specified worksheets
    worksheets = [wb[ws] for ws in worksheets]
    # import tables from imported worksheets
    tables = {ws.title: [tuple([cell.value for cell in row])
                         for row in ws.rows] for ws in worksheets}
    wb.close()
    return tables


class ConfigModel:
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
                return [v[option] for k,v in self.options.items() if option in v][0]
        except KeyError as e:
            raise KeyError((str(e) + " not in the options list."))

    def import_config(self, ini):
        self._parser.read(ini)
        self.options = {k:dict(self._parser[k]) for k in self._parser.sections()}
