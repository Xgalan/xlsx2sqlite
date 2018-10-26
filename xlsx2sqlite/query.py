#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3


class DatabaseWrapper:
    ''' Class that interface with sqlite3 standard library module. '''
    def __init__(self, path=None):
        if path is None:
            self._db = sqlite3.connect(':memory:')
        else:
            self._db = sqlite3.connect(path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_traceb):
        if exc_type:
            print(exc_val)
        try:
            self._db.commit()
        except:
            print('Error while committing changes to database.')
        return True

    def close_db(self):
        self._db.close()

    def create_table(self, tablename=None, definitions=None):
        ''' Prepare and execute a CREATE TABLE sql query for a given table
        instance. '''
        sql_create_table = 'CREATE TABLE IF NOT EXISTS {tablename} ({definitions});'
        try:
            self._db.execute(sql_create_table.format(tablename=tablename,
                                                     definitions=definitions))
            print('Created table: ' + tablename)
        except sqlite3.OperationalError as e:
            self._db.rollback()
            raise sqlite3.OperationalError('Error when creating table: ' + str(e))

    def create_view(self, viewname=None, select=None):
        ''' The CREATE VIEW command assigns a name to a pre-packaged SELECT
        statement. Once the view is created, it can be used in the FROM clause
        of another SELECT in place of a table name. '''
        sql_create_view = 'CREATE VIEW IF NOT EXISTS {viewname} AS {select};'
        try:
            self._db.execute(sql_create_view.format(viewname=viewname,
                                                    select=select))
            print('Created view: ' + viewname)
        except sqlite3.OperationalError as e:
            self._db.rollback()
            raise sqlite3.OperationalError('Error when creating view: ' + str(e))

    def insert_into(self, tablename=None, fields=None, args=None, data=None):
        ''' Populate the given table with data from the collection. '''
        sql_insert_into = 'INSERT INTO {tablename} ({fields}) VALUES ({args});'
        self._db.executemany(sql_insert_into.format(tablename=tablename,
                                                    fields=fields,
                                                    args=args),
                             data)

    def select(self, columns=None, from_table=None, where=None):
        ''' SELECT result-column FROM table-or-subquery WHERE expr; '''
        if columns is None:
            columns = '*'
        if where is None:
            sql_select = 'SELECT {columns} FROM {from_table};'
            self._db.row_factory = sqlite3.Row
            cur = self._db.execute(sql_select.format(columns=columns,
                                                     from_table=from_table)
                                   )
        else:
            sql_select = 'SELECT {columns} FROM {from_table} WHERE {where};'
            self._db.row_factory = sqlite3.Row
            cur = self._db.execute(sql_select.format(columns=columns,
                                                     from_table=from_table,
                                                     where=where)
                                   )
        return cur.fetchall()

    def drop_view(self, viewname=None):
        sql_drop_table = 'DROP VIEW IF EXISTS {viewname};'
        self._db.execute(sql_drop_view.format(viewname=viewname))
        print('Removed view: ' + viewname)

    def drop_table(self, tablename=None):
        sql_drop_table = 'DROP TABLE IF EXISTS {tablename};'
        self._db.execute(sql_drop_table.format(tablename=tablename))
        print('Deleted table: ' + tablename)
