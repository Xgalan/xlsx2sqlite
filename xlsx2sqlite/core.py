#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict

import tablib

from .utils import COMMA_DELIM, import_worksheets
from .query import DatabaseWrapper



class Tables:
    ''' Container class for tablib.Dataset instances. '''
    _tables = OrderedDict()

    def __iter__(self):
        return iter(self._tables)

    def get(self, table):
        return self._tables.get(table, None)

    def __contains__(self, key):
        return self._tables[key]

    def __getitem__(self, key):
        return self._tables[key]

    def import_tables(self, workbook=None, worksheets=None, subset_cols=None):
        tables = import_worksheets(workbook=workbook, worksheets=worksheets)
        for tbl_name,values in tables.items():
            headers = values.pop(0)
            self._tables[tbl_name] = tablib.Dataset(
                *values, headers=headers).subset(cols=subset_cols[tbl_name])

    def create_empty_table(self, tablename=None, headers=None):
        self._tables[tablename] = tablib.Dataset(headers=headers)
        return self._tables[tablename]

    def values_to_table(self, tablename=None, values=None):
        [self._tables[tablename].append(val) for val in values]


class Definitions:
    ''' Definitions generator for sqlite3 tables. '''
    COMMA_DELIM = ','

    def __init__(self, headers=None, row=None,
                 primary_key=None, unique_keys=None):
        self.headers = headers
        self.row = row
        if primary_key is None:
            self.primary_key = "'id'"
        else:
            self.primary_key = primary_key
        self.unique_keys = unique_keys

    def __str__(self):
        fields = self.get_fields()
        if self.unique_keys:
            unique_keys = ["'" + s + "'" for s in self.unique_keys['unique']]
            [fields.update({v: fields.get(v) + ' UNIQUE'}) for v in unique_keys]
        return COMMA_DELIM.join(
            [' '.join((k,v)) for k,v in fields.items()]
            )

    def get_primary_key(self):
        return (self.primary_key, 'INTEGER PRIMARY KEY')

    @staticmethod
    def prepare_name(s):
        ''' Return a suitable string for using in the database. '''
        s = s.strip()
        return "'" + s.capitalize() + "'"

    @staticmethod
    def test_type(value):
        '''
        Detect the type of an object and return a Sqlite3 type affinity.
        '''
        #TODO: add datetime parsing
        if isinstance(value, str):
            return 'TEXT'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'
        elif value is None:
            return 'BLOB'
        else:
            return 'TEXT'

    def get_columns_names(self):
        # prepare column names
        return [self.prepare_name(col) for col in self.headers]

    def get_columns_types(self):
        # detect SQLITE3 datatypes, check the first row of a table instance
        return [self.test_type(v) for v in self.row]

    def get_fields(self):
        # map types to column names
        pk = self.get_primary_key()
        d = OrderedDict(zip(self.get_columns_names(),
                            self.get_columns_types()))
        d[pk[0]] = pk[1]
        d.move_to_end(pk[0], last=False)
        return d


class Controller:
    def __init__(self):
        self._collection = Tables()
        self._db = None
        self._constraints = {}

    def __getattr__(self, name):
        attr = getattr(self._collection, name)

        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            return attr(*args, **kwargs)
        return wrapper

    def create_db(self, db_file):
        self._db = DatabaseWrapper(path=db_file)

    def set_constraints(self, constraints):
        '''
        structure of constraints dict:
        {
            'tablename1': {'unique': 'column_name1,column_name2'},
            ...
        }
        '''
        if isinstance(constraints, dict):
            d = {}
            [self._constraints.update({k.lower(): {}})
             for k in self._collection]
            for tablename in self._constraints.keys():
                d[tablename] = {}
                [d[tablename].update({k: constraints[k]})
                 for k in constraints.keys() if tablename in k]                
                unique_keys = [v for k,v in d[tablename].items()
                               if 'unique' in k]
                if unique_keys:
                    self._constraints[tablename].update(
                        {'unique': [s.strip()
                                    for s in unique_keys[0].split(COMMA_DELIM)]}
                        )
        else:
            raise TypeError

    def close_db(self):
        self._db.close_db()

    def create_tables(self):
        [self.create_table(tablename=k) for k in self._collection]

    def drop_tables(self, tables_list):
        [self.drop_table(tablename=k) for k in tables_list]

    def drop_table(self, tablename=None):
        with self._db as db:
            db.drop_table(tablename=tablename)

    def create_view(self, viewname=None, select=None):
        with self._db as db:
            db.create_view(viewname=viewname, select=select)

    def drop_view(self, viewname=None):
        with self._db as db:
            db.drop_view(viewname=viewname)

    def select_all(self, table_name=None, where_clause=None):
        with self._db as db:
            if where_clause is None:
                q = db.select(from_table=table_name)
            else:
                q = db.select(from_table=table_name, where=where_clause)
            return tablib.Dataset(*[tuple(row) for row in q],
                                  headers=q[0].keys())

    def list_tables(self):
        q = self.select_all(table_name='sqlite_master',
                            where_clause="type='table'")
        return q.subset(cols=['type', 'name'])

    def list_views(self):
        q = self.select_all(table_name='sqlite_master',
                            where_clause="type='view'")
        return q.subset(cols=['type', 'name'])

    def create_table(self, tablename=None):
        # retrieve constraints for the given table
        constraints = self._constraints[tablename.lower()]
        # create and populate the database table
        with self._db as db:
            # prepare definitions
            d = Definitions(headers=self.get(tablename).headers,
                            row=self.get(tablename)[0],
                            unique_keys=constraints)
            # create table in _db
            db.create_table(tablename=tablename, definitions=str(d))

            # insert data into table
            fields = d.get_fields()
            data = [tuple([v[0]]) + v[1]
                    for v in enumerate(self.get(tablename))]
            db.insert_into(tablename=tablename,
                           fields=COMMA_DELIM.join(fields.keys()),
                           args=COMMA_DELIM.join(len(fields) * '?'),
                           data=data)
