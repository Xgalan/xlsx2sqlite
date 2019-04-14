# -*- coding: utf-8 -*-
import sqlite3


class DatabaseWrapper:
    """Class that interface with sqlite3 standard library module.

    Creates a database connection.

    :key path: Full path of the database, if the full path isn't
                   specified the class will instantiate a sqlite3
                   in memory database.
    """
    SQL_QUERY = {
        'create_table': 'CREATE TABLE IF NOT EXISTS {name} ({definitions});',
        'create_view': 'CREATE VIEW IF NOT EXISTS {name} AS {select};',
        'drop_entity': 'DROP {entity} IF EXISTS {name};',
        'insert_into': 'INSERT INTO {tablename}({fields}) VALUES ({args});',
        'replace': """REPLACE INTO {tablename}({fields}) VALUES ({args});""",
        'select_from': 'SELECT {columns} FROM {from_table};',
        }

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
        """Closes the connection to the database."""
        self._db.close()

    def _execute(self, query, parameters, messages):
        try:
            self._db.execute(query.format(**parameters))
            print(messages['success'])                            
        except sqlite3.OperationalError as e:
            self._db.rollback()
            raise sqlite3.OperationalError(messages['error'] + str(e))

    def create_table(self, tablename=None, definitions=None):
        """Prepare and execute a CREATE TABLE sql query for a given table
        instance.

        The query executed is in this form:

        .. code-block:: sql

            CREATE TABLE IF NOT EXISTS tablename (definitions);

        :key tablename: Name of the table to be created.
        :key definitions: Definitions as accepted by the Sqlite3 SQL
                          query dialect.
        """
        parameters = {'name': tablename, 'definitions': definitions}
        messages = {'error': 'Error when creating table: ',
                    'success': 'Created table: ' + parameters['name']}
        self._execute(self.SQL_QUERY['create_table'], parameters, messages)

    def create_view(self, viewname=None, select=None):
        """The CREATE VIEW command assigns a name to a pre-packaged SELECT
        statement. Once the view is created, it can be used in the FROM clause
        of another SELECT in place of a table name.

        The query executed is in this form:

        .. code-block:: sql

            CREATE VIEW IF NOT EXISTS viewname AS select-query;

        :key viewname: Name of the view to be created.
        :key select: `SELECT` SQL query to use as argument in the
                     `CREATE VIEW IF NOT EXISTS` statement.
        """
        parameters = {'name': viewname, 'select':  select}
        messages = {'error': 'Error when creating view: ',
                    'success': 'Created view: ' + parameters['name']}
        self._execute(self.SQL_QUERY['create_view'], parameters, messages)

    def drop_entity(self, entity_name=None, entity_type=None):
        """Drop the specified entity from the database.

        If the entity type is `TABLE` the query is:

        .. code-block:: sql

            DROP TABLE IF EXISTS entity_name;

        If the entity type is `VIEW` the query is:

        .. code-block:: sql

            DROP VIEW IF EXISTS entity_name;

        :key entity_name: Name of the entity to drop.
        :key entity_type: Type of the entity to drop.
        """
        parameters = {'entity': entity_type, 'name': entity_name}
        messages = {'error': 'Error when deleting ' + entity_type + ' ' + entity_name,
                    'success': 'Deleted ' + entity_type + ' ' + entity_name}
        if entity_type in ['TABLE', 'VIEW']:
            self._execute(self.SQL_QUERY['drop_entity'], parameters, messages)

    def _executemany(self, query, parameters, data):
        try:
            self._db.executemany(query.format(**parameters), data)
        except sqlite3.OperationalError as e:
            self._db.rollback()
            raise sqlite3.OperationalError(str(e))

    def insert_into(self, tablename=None, fields=None, args=None, data=None):
        """Populate the given table with data from the collection.

        :key tablename: Name of the table to insert values into.
        :key fields: List of fields as accepted by the SQL language of Sqlite3.
        :key args: SQL arguments of the query.
        :key data: List of values to be passed as arguments
                   to the SQL statement.
        """
        parameters = {'tablename': tablename, 'fields': fields, 'args': args}
        self._executemany(self.SQL_QUERY['insert_into'], parameters, data)

    def insert_or_replace(self, tablename=None, fields=None, args=None,
                          data=None):
        """Perform a `REPLACE` operation on the database.

        :key tablename: Name of the table to insert values into.
        :key fields: List of fields as accepted by the SQL language of Sqlite3.
        :key args: SQL arguments of the query.
        :key data: List of values to be passed as arguments
                   to the SQL statement.
        """
        parameters = {'tablename': tablename, 'fields': fields, 'args': args}
        self._executemany(self.SQL_QUERY['replace'], parameters, data)

    def select(self, columns=None, from_table=None, where=None):
        """Executes a `SELECT` query on the database.

        The query executed is in this form:

        .. code-block:: sql

            SELECT result-column FROM table-or-subquery WHERE expr;

        :key columns: Names of the columns to include in the query.
        :key from_table: Name of the table to query.
        :key where: `WHERE` SQL clause.
        :returns: A sqlite3 cursor containing the results of the query, if any.
        :rtype: object
        """
        conditions = {'columns': columns, 'from_table': from_table}
        sql_query = self.SQL_QUERY['select_from']
        if columns is None:
            columns = '*'
        if where:
            sql_query.replace(';', ' WHERE {where};')
            conditions['where'] = where            
        self._db.row_factory = sqlite3.Row
        cur = self._db.execute(sql_query.format(**conditions))
        return cur.fetchall()
