# -*- coding: utf-8 -*-
"""Core module. Contains the main controller class.
"""
from xlsx2sqlite.definitions_factory import Definitions
from xlsx2sqlite.dataset import Dataset
from xlsx2sqlite.db_wrapper import DatabaseWrapper



class Controller:

    COMMA_DELIM = ','

    def __init__(self, ini_config=None):
        self._collection = Dataset()
        self._db = None
        self._config = {}
        self._constraints = {}
        if ini_config is not None:
            self._ini = ini_config
            self._config = dict(
                workbook=self._ini.get('xlsx_file'), 
                worksheets=self._ini.get_tables_names, 
                subset_cols=self._ini.get_columns_to_import,
                headers=self._ini.get_options()['HEADERS'],
                constraints=self._ini.get_options()['CONSTRAINTS']
            )
            self.create_db(self._ini.get('db_file'))

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

    def close_db(self):
        """Close the connection to the database.
        """
        self._db.close_db()

    def set_constraints(self, constraints):
        """Set a representation of the constraints declared in the INI file.

        :param constraints: A dictionary containing table names as keys and
                            a list of column names as values.
        """
        if isinstance(constraints, dict):
            d = {}
            # create a key for every table in the collection
            [self._constraints.update({k.lower(): {}}) for k in self._collection]
            for tablename in self._constraints.keys():
                d[tablename] = {}
                [
                    d[tablename].update({k: constraints[k]}) for k in constraints.keys() if tablename in k
                ]
                unique_keys = [v for k,v in d[tablename].items() if 'unique' in k]
                primary_key = [v for k,v in d[tablename].items() if 'primarykey' in k]
                if unique_keys:
                    self._constraints[tablename].update(
                        {'unique': [s.strip() for s in unique_keys[0].split(self.COMMA_DELIM)]}
                    )
                if primary_key:
                    self._constraints[tablename].update(
                        {'pk': [s.strip() for s in primary_key[0].split(self.COMMA_DELIM)]}
                    )
        elif constraints is None:
            pass
        else:
            raise TypeError

    def initialize_db(self):
        """Creates the database tables and populates them with the data
        imported from the tables in the collection.

        The collection contains tablib.Dataset instances.
        """
        messages = []
        """
        self._config example:

        {'workbook': 'C:\\Users\\erikm\\Documents\\Projects\\xlsx2sqlite_api_test/test2.xlsx',
         'worksheets': {'TestSheet', 'TestNonIntegerPrimaryKey'},
         'subset_cols': {'TestSheet': [
             'Test_id', 'col1', 'col2', 'col3', 'col4', 'col5'
             ], 'TestNonIntegerPrimaryKey': [
             'col1', 'col2', 'col3', 'col4']}, 'headers': {'testsheet_header': '3'},
            'constraints': {'testsheet_primarykey': 'Test_id,col1', 'testsheet_unique': 'col1',
                            'testnonintegerprimarykey_primarykey': 'col1'}}
        """
        self.import_tables(
            workbook=self._config['workbook'],
            worksheets=self._config['worksheets'],
            subset_cols=self._config['subset_cols'],
            headers=self._config['headers']
        )
        self.set_constraints(self._config['constraints'])
        print(self._config)
        messages += [self.create_table(tablename=k) for k in self._collection]
        messages += [self.insert_into(tablename=k) for k in self._collection]
        return messages

    def insert_into(self, tablename=None):
        """Insert data into the declared table.

        :param tablename: Name of the table to insert into.
        """
        with self._db as db:
            pk = None if not self._constraints else self._constraints[tablename.lower()]['pk']
            table = self.get(tablename)
            d = Definitions(
                headers=table.headers,
                row=table[0],
                primary_key=pk
            )
            fields = d.get_fields()
            db.insert_into(
                tablename=tablename,
                fields=d.get_labels(),
                args=self.COMMA_DELIM.join(len(fields) * '?'),
                data=[v for v in table]
            )
            return 'Data inserted into table: {}'.format(tablename)

    def insert_or_replace(self, tablename=None):
        """Perform a REPLACE operation on the database.

        :param tablename: Name of the table on which to perform the REPLACE operation.
        """
        with self._db as db:
            tinfo = db.table_info(tablename=tablename)
            if tinfo == []:
                return ['Table {} not found.'.format(tablename)]
            db_pk = [dict(i) for i in tinfo if dict(i)['pk']==True][0]['name']
            if db_pk not in self._config['subset_cols'][tablename]:
                self._config['subset_cols'][tablename].insert(0, db_pk)
            self.import_tables(
                workbook=self._config['workbook'],
                worksheets=self._config['worksheets'],
                subset_cols=self._config['subset_cols'],
                headers=self._config['headers']
            )
            # set constraints
            self.set_constraints(self._config['constraints'])
            pk = None if not self._constraints else self._constraints[tablename.lower()]['pk']
            if pk is None:
                return ['Must declare a primary key in the [CONSTRAINTS] section.']
            table = self.get(tablename)
            # retrieve first row from new data
            first_row = dict(zip(table.headers, table[0]))
            d = Definitions(
                headers=table.headers,
                row=table[0],
                primary_key=pk
            )
            fields = d.get_fields()
            # check if the primary key is in new data
            if db_pk in first_row:
                db.insert_or_replace(
                    tablename=tablename,
                    fields=d.get_labels(),
                    args=self.COMMA_DELIM.join(len(fields) * '?'),
                    data=[v for v in table]
                )
                return ['Updated table: {}'.format(tablename)]
            else:
                return [
                    'Primary Key not found on {}, REPLACE operation aborted.'.format(tablename)
                ]

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
            constraints = self._constraints
        else:
            constraints = self._constraints[tablename.lower()]
        unique = constraints['unique'] if 'unique' in constraints else None
        pk = constraints['pk'] if 'pk' in constraints else None
        # create the database table
        with self._db as db:
            table = self.get(tablename)
            d = Definitions(
                name=tablename,
                headers=table.headers,
                row=table[0],
                unique_keys=unique,
                primary_key=pk
            )
            return db.create_table(tablename=d.tablename, definitions=d.prepare_sql())

    def drop_tables(self, tables_list):
        """Drop all the database tables with a name in the list.

        :param tables_list: List of tables names to drop from the database.
        """
        return [self.drop_table(tablename=k) for k in tables_list]

    def drop_table(self, tablename=None):
        """Drop the database table with the corresponding name.

        :key tablename: Name of the table to drop from the database.
        """
        with self._db as db:
            return db.drop_entity(entity_name=tablename, entity_type='TABLE')

    def create_view(self, viewname=None, select=None):
        """Create a database view.

        :key viewname: Name of the view.
        :key select: `SELECT` query statement.
        """
        with self._db as db:
            return db.create_view(viewname=viewname, select=select)

    def drop_view(self, viewname=None):
        """Drop the database view with the corresponding name.

        :key viewname: Name of the view to drop from the database.
        """
        with self._db as db:
            return db.drop_entity(entity_name=viewname, entity_type='VIEW')

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
                return self._dataset(
                    *[tuple(row) for row in q],
                    headers=q[0].keys()
                )
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
