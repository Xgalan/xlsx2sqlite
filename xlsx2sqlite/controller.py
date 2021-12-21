# -*- coding: utf-8 -*-
"""Core module. Contains the main controller class.
"""
from xlsx2sqlite.definitions_factory import Definitions
from xlsx2sqlite.dataset import Dataset
from xlsx2sqlite.db_wrapper import DatabaseWrapper
from xlsx2sqlite.config import Xlsx2sqliteConfig
from xlsx2sqlite.import_export import export_worksheet



__all__ = ["new_controller"]


def new_controller(config: object) -> object:
    """Controller class factory

    :returns: An instance of Controller
    :rtype: object
    """
    ini = Xlsx2sqliteConfig(config)
    return Controller(ini_config=ini)


class Controller:

    COMMA_DELIM = ','

    def __init__(self, ini_config=None):
        self._collection = Dataset()
        self._db = None
        self._config = {}
        self._constraints = {}
        if ini_config is not None:
            self._ini = ini_config
            self._workbook = self._ini.get('xlsx_file')
            self._worksheets = self._ini.get_tables_names
            self._models = self._ini.get_models
            self._config = dict(
                headers=self._ini.get_options()['HEADERS']
            )
            self.create_db(self._ini.get('db_file'))

    def __getattr__(self, name):
        attr = getattr(self._collection, name)

        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            return attr(*args, **kwargs)
        return wrapper
    
    def update(self, subject):
        print(subject.log[-1])

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

    def set_constraints(self):
        """Set a representation of the constraints declared in the INI file.
        """
        keywords = self._ini.get_model_keywords()

        if self._models is not None:
            # create a key for every table in the collection
            [self._constraints.update({k: {}}) for k in self._collection]
            for tablename in self._constraints.keys():
                for keyword in keywords:
                    self._constraints[tablename].update(
                        {keyword: self._models[tablename][keyword]}
                    )
        else:
            raise TypeError

    def get_db_table_name(self, tablename):
        """Return the name to give to the database table.

        :param tablename: Name of the table to check if it is declared a 'db_table' attribute 
                          in the INI file.
        :returns: A string representing the name of the database table as declared 
                  in the INI file.
        :rtype: string
        """
        db_table = self._ini.get_db_tables_names[tablename]
        if isinstance(db_table, list):
                db_table = db_table[0]
        else:
            db_table = tablename
        return db_table

    def initialize_db(self):
        """Creates the database tables and populates them with the data
        imported from the tables in the collection.

        The collection contains tablib.Dataset instances.
        """
        self.import_tables(
            workbook=self._workbook,
            worksheets=self._worksheets,
            subset_cols=self._ini.get_columns_to_import,
            headers=self._config['headers']
        )
        self.set_constraints()
        [self.create_table(tablename=k) for k in self._collection]
        [self.insert_into(tablename=k) for k in self._collection]

    def insert_into(self, tablename=None):
        """Insert data into the declared table.

        :param tablename: Name of the table to insert into.
        """
        with self._db as db:
            self.set_constraints()
            pk = None if not self._constraints else self._constraints[tablename]['primary_key']
            table = self.get(tablename)
            d = Definitions(
                headers=table.headers,
                row=table[0],
                primary_key=pk
            )
            fields = d.get_fields()
            db.insert_into(
                tablename=self.get_db_table_name(tablename),
                fields=d.get_labels(),
                args=self.COMMA_DELIM.join(len(fields) * '?'),
                data=[v for v in table]
            )

    def insert_or_replace(self, tablename=None):
        """Perform a REPLACE operation on the database.

        :param tablename: Name of the table on which to perform the REPLACE operation.
        """
        with self._db as db:
            db_table = self.get_db_table_name(tablename)
            tinfo = db.table_info(tablename=db_table)
            if tinfo == []:
                raise RuntimeError('Table {} not found.'.format(tablename))
            db_pk = [dict(i) for i in tinfo if dict(i)['pk']==True][0]['name']
            columns = self._ini.get_columns_to_import[tablename]
            if db_pk not in columns:
                columns.insert(0, db_pk)
            self.import_tables(
                workbook=self._workbook,
                worksheets=self._worksheets,
                subset_cols=columns,
                headers=self._config['headers']
            )
            self.set_constraints()
            pk = None if not self._constraints else self._constraints[tablename]['primary_key']
            if pk is None:
                print('Must declare a primary key.')
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
                    tablename=db_table,
                    fields=d.get_labels(),
                    args=self.COMMA_DELIM.join(len(fields) * '?'),
                    data=[v for v in table]
                )
            else:
                raise RuntimeError('Primary Key not found on {}, REPLACE operation aborted.'.format(tablename))

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
            constraints = self._constraints[tablename]
        unique = constraints['unique'] if 'unique' in constraints else None
        pk = constraints['primary_key'] if 'primary_key' in constraints else None
        # create the database table
        with self._db as db:
            table = self.get(tablename)
            d = Definitions(
                name=self.get_db_table_name(tablename),
                headers=table.headers,
                row=table[0],
                unique_keys=unique,
                primary_key=pk
            )
            db.create_table(tablename=d.tablename, definitions=d.prepare_sql())

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
            db.drop_entity(entity_name=tablename, entity_type='TABLE')

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
            db.drop_entity(entity_name=viewname, entity_type='VIEW')

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
    
    def export_worksheet(self, filename=None, viewname=None, rows=None):
        """Relay function to export_worksheet
        """
        export_worksheet(filename=filename, ws_name=viewname, rows=rows)
