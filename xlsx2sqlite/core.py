# -*- coding: utf-8 -*-
"""Core module. Contains the main controller class.

"""
from collections import OrderedDict

import tablib

from .utils import import_worksheets
from .query import DatabaseWrapper


COMMA_DELIM = ','


class Tables:
    """Container class for tablib.Dataset instances."""
    _tables = OrderedDict()

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

    def import_tables(self, workbook=None, worksheets=None, subset_cols=None):
        """Import the specified worksheets into the tables collection.

        :key workbook: Path of the xlsx file to open for import.
        :key worksheets: List of the worksheets to be imported.
        :key subset: List of columns in the worksheet to consider for import.
        """
        tables = import_worksheets(workbook=workbook, worksheets=worksheets)
        for tbl_name,values in tables.items():
            headers = values.pop(0)
            self._tables[tbl_name] = tablib.Dataset(
                *values, headers=headers).subset(cols=subset_cols[tbl_name])

    def create_empty_table(self, tablename=None, headers=None):
        """Creates a tablib.Dataset instance in the collection.

        :key tablename: Name of the table to be created.
        :key headers: List of labels for the table header.
        :returns: An empty table.
        :rtype: tablib.Dataset
        """
        self._tables[tablename] = tablib.Dataset(headers=headers)
        return self._tables[tablename]

    def values_to_table(self, tablename=None, values=None):
        """Append values to a tablib.Dataset table in the collection.

        :key tablename: Name of the table.
        :key values: List of values to append.
        """
        [self._tables[tablename].append(val) for val in values]


class Definitions:
    """Definitions generator for Sqlite3 tables."""
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
        """Get the primary key to use in the database.

        :returns: The name of the primary key with the default Sqlite3
                  datatype for primary key (`INTEGER PRIMARY KEY`). 
        :rtype: tuple
        """
        return (self.primary_key, 'INTEGER PRIMARY KEY')

    @staticmethod
    def prepare_name(s):
        """Return a suitable string for using in the database.

        :param s: A string.
        :returns: A capitalized form of the string with the leading
                  and trailing characters removed.
        """
        s = s.strip()
        return "'" + s.capitalize() + "'"

    @staticmethod
    def test_type(value):
        """Detect the type of an object and return a Sqlite3 type affinity.

        :param value: An instance to check for affinity.
        :returns: The name of the Sqlite3 affinity type.
        :rtype: str
        """
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
        """Prepare column names."""
        return [self.prepare_name(col) for col in self.headers]

    def get_columns_types(self):
        """Detect Sqlite3 datatypes.

        Detect Sqlite3 type affinity checking the first row of a table instance.
        """
        return [self.test_type(v) for v in self.row]

    def get_fields(self):
        """Get the list of fields for using as columns definitions.

        :returns: A dictionary containing pairs of column names/column types
                  to be used to create a definition for the database. 
        :rtype: OrderedDict
        """
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
        """Creates a connection with the specified Sqlite3 database.

        :param db_file: Full path of the Sqlite3 database file, if no path is
                        given the DatabaseWrapper class will initialize an
                        in memory database.
        """
        self._db = DatabaseWrapper(path=db_file)

    def set_constraints(self, constraints):
        """Set a representation of the constraints declared in the INI file.

        :param constraints: A dictionary containing table names as keys and
                            a list of column names as values.
        """
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
        """Close the connection to the database."""
        self._db.close_db()

    def initialize_db(self, update_only=False):
        """Creates the database tables and populates them with the data
        imported from the tables in the collection.

        :key update_only: Insert or replace the values for all the tables
                          in the database.

        The collection contains tablib.Dataset instances.
        """
        if update_only is False:
            [self.create_table(tablename=k) for k in self._collection]
        [self.insert_or_replace(tablename=k) for k in self._collection]

    def drop_tables(self, tables_list):
        """Drop all the database tables with a name in the list.

        :param tables_list: List of tables names to drop from the database.
        """
        [self.drop_table(tablename=k) for k in tables_list]

    def drop_table(self, tablename=None):
        """Drop the database table with the corresponding name.

        :key tablename: Name of the table to drop from the database.
        """
        with self._db as db:
            db.drop_entity(entity_name=tablename,
                           entity_type='TABLE')

    def create_view(self, viewname=None, select=None):
        """Create a database view.

        :key viewname: Name of the view.
        :key select: `SELECT` query statement.
        """
        with self._db as db:
            db.create_view(viewname=viewname, select=select)

    def drop_view(self, viewname=None):
        """Drop the database view with the corresponding name.

        :key viewname: Name of the view to drop from the database.
        """
        with self._db as db:
            db.drop_entity(entity_name=viewname,
                           entity_type='VIEW')

    def select_all(self, table_name=None, where_clause=None):
        """Perform a `SELECT *` SQL query on the database.

        :key table_name: Name of the table or view to query.
        :key where_clause: Valid SQL `WHERE` clause.
        :returns: A table as a tablib.Dataset instance.
        :rtype: tablib.Dataset
        """
        parameters = {'from_table': table_name}
        with self._db as db:
            if where_clause:
                parameters['where'] = where_clause
            q = db.select(**parameters)
            if q:
                return tablib.Dataset(*[tuple(row) for row in q],
                                      headers=q[0].keys())
            else:
                return None

    def ls_entities(self, entity_type=None):
        """List all the entities in the database.

        :key entity_type: Type of the entity to list.
        :returns: A table as a tablib.Dataset instance.
        :rtype: tablib.Dataset
        """
        parameters = {'table_name': 'sqlite_master'}
        if entity_type in ['table', 'view']:
            parameters['where_clause'] = "type='{ent_type}'".format(
                ent_type=entity_type)
        q = self.select_all(**parameters)
        if q:
            return q.subset(cols=['type', 'name'])
        else:
            return None        

    def insert_or_replace(self, tablename=None):
        with self._db as db:
            # prepare definitions
            d = Definitions(headers=self.get(tablename).headers,
                            row=self.get(tablename)[0])

            # insert or replace data into table
            fields = d.get_fields()
            data = [tuple([v[0]]) + v[1]
                    for v in enumerate(self.get(tablename))]
            db.insert_or_replace(tablename=tablename,
                                 fields=COMMA_DELIM.join(fields.keys()),
                                 args=COMMA_DELIM.join(len(fields) * '?'),
                                 data=data)

    def create_table(self, tablename=None):
        """Create a new table in the database.

        Retrieve the constraints if they exists, then generates the
        definitions for the SQL query, finally creates the table
        in the database.
        The table name must exists in the tables collection.

        :key tablename: Name of the table to be created.
        """
        # retrieve constraints for the given table
        if any(self._constraints) is False:
            print('No constraints specified.')
            constraints = self._constraints
        else:
            constraints = self._constraints[tablename.lower()]
        # create and populate the database table
        with self._db as db:
            # prepare definitions
            d = Definitions(headers=self.get(tablename).headers,
                            row=self.get(tablename)[0],
                            unique_keys=constraints)
            # create table in _db
            db.create_table(tablename=tablename, definitions=str(d))
