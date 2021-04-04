# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime



COMMA_DELIM = ','
SPACE_DELIM = ' '


class Field:
    """Represents a database field.
    """
    def __init__(self, field_name=None, field_type=None):
        self.field_name = field_name
        self.field_type = field_type

    def __repr__(self):
        return f'<Field {self.field_name}, type={self.field_type}>'
    
    def label(self):
        """A form of the string with the leading and trailing characters removed.

        :returns: A form of the string with the leading and trailing characters removed.
        :rtype: str
        """
        return "'" + self.field_name.strip() + "'"
    
    def to_sql(self):
        """Return a suitable string for using in the database.

        :returns: A capitalized form of the string with the leading
                  and trailing characters removed.
        :rtype: str
        """
        return SPACE_DELIM.join((self.label(), self.field_type))


class AddDefinitionMixin:
    """Render the definition field added in the subclass.

    Main class must contain a label method that returns a string.
    """
    def __repr__(self):
        return f'<Field {self.field_name}, type={self.field_type} definition={self.definition}>'

    def to_sql(self):
        """Return a suitable string for using in the database.

        :returns: A capitalized form of the string with the leading
                  and trailing characters removed.
        :rtype: str
        """
        return SPACE_DELIM.join((self.label(), self.field_type, self.definition)) 


class PrimaryKey(AddDefinitionMixin, Field):
    """Represents the primary key for a database table.
    """
    def __init__(self, field_name, field_type):
        super().__init__(field_name, field_type)
        self.definition = "NOT NULL PRIMARY KEY"


class UniqueField(AddDefinitionMixin, Field):
    """Represents a field with a UNIQUE clause.
    """
    def __init__(self, field_name, field_type):
        super().__init__(field_name, field_type)
        self.definition = "UNIQUE"


class NotNullField(AddDefinitionMixin, Field):
    """A field with the NOT NULL clause.
    """
    def __init__(self, field_name, field_type):
        super().__init__(field_name, field_type)
        self.definition = "NOT NULL"


def get_field(type_of: str, field_name: str, field_type: str) -> object:
    """Factory
    """
    fields = {
        "Field": Field,
        "Unique": UniqueField,
        "PrimaryKey": PrimaryKey,
        "NotNullField": NotNullField
    }
    return fields[type_of](field_name, field_type)


class Definitions:
    """Definitions generator for Sqlite3 tables.
    """
    def __init__(self, headers=None, row=None, primary_key=None, unique_keys=None):
        try:
            if headers is None or row is None:
                raise TypeError
            self.headers = headers
            self.row = row
            self.unique_keys = unique_keys
            # map types to column names
            self._fields = dict(
                zip(self.headers,
                    [{"type": self.test_type(v), "cls": 'Field'} for v in self.row]
                )
            )
            if primary_key is None:
                # default primary key
                self.primary_key = get_field('PrimaryKey', 'id', 'INTEGER')
            elif isinstance(primary_key, list):
                key = primary_key[0]
                if key in set(headers):
                    self._fields[key]['cls'] = 'PrimaryKey'
                else:
                    self.primary_key = get_field('PrimaryKey', key, 'INTEGER')
                    #self._fields.pop(key)
            if unique_keys and isinstance(unique_keys, list):
                for key in unique_keys:
                    if key in self._fields:
                        self._fields[key]['cls'] = 'Unique'
        except TypeError:
            print('Must declare headers and row.')
            return

    @staticmethod
    def test_type(value):
        """Detect the type of an object and return a Sqlite3 type affinity.

        :param value: An instance to check for affinity.
        :returns: The name of the Sqlite3 affinity type.
        :rtype: str
        """
        if isinstance(value, str):
            return 'TEXT'
        elif isinstance(value, int):
            return 'INTEGER'
        elif isinstance(value, float):
            return 'REAL'
        elif isinstance(value, datetime):
            return 'TIMESTAMP'
        elif value is None:
            return 'BLOB'
        else:
            return 'TEXT'

    def prepare_sql(self):
        """Returns the complete sql definition as a string.

        :returns: A string representing the SQL definitions for the CREATE TABLE statement.
        :rtype: str
        """
        fields = self.get_fields()
        if hasattr(self, 'primary_key'):
            fields.insert(0, self.primary_key)
        sql_strings = [field.to_sql() for field in fields]
        return COMMA_DELIM.join(sql_strings)

    def get_fields(self):
        """Get the list of fields for using as columns definitions.
        This method doesn't return the primary key in the list of fields.

        :returns: A list of Field instances describing the columns of the database.
        :rtype: list
        """
        fields = [get_field(v['cls'], k, v['type']) for k,v in self._fields.items()]
        return fields

    def get_labels(self):
        labels = [field.label() for field in self.get_fields()]
        return COMMA_DELIM.join(labels)


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
        'table_info': 'PRAGMA table_info({tablename});',
        }

    def __init__(self, path=None):
        if path is None:
            self._db = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
        else:
            self._db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

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
            q = query.format(**parameters)
            if q.endswith(';;'):
                q = q[:-1]
            self._db.execute(q)
            return messages['success']
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
        return self._execute(self.SQL_QUERY['create_table'], parameters, messages)

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

    def insert_or_replace(self, tablename=None, fields=None, args=None, data=None):
        """Perform a `REPLACE` operation on the database.

        :key tablename: Name of the table to insert values into.
        :key fields: List of fields as accepted by the SQL language of Sqlite3.
        :key args: SQL arguments of the query.
        :key data: List of values to be passed as arguments
                   to the SQL statement.
        """
        parameters = {'tablename': tablename, 'fields': fields, 'args': args}
        self._executemany(self.SQL_QUERY['replace'], parameters, data)

    def table_info(self, tablename=None):
        """Executes a `PRAGMA` query on the database.

        The query executed is in this form:

        .. code-block:: sql

            PRAGMA table_info(tablename);

        :key tablename: Name of the table.
        :returns: A sqlite3 cursor containing the results of the query, if any.
        :rtype: object
        """
        conditions = {'tablename': tablename}
        sql_query = self.SQL_QUERY['table_info']
        self._db.row_factory = sqlite3.Row
        cur = self._db.execute(sql_query.format(**conditions))
        return cur.fetchall()

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
            conditions['columns'] = '*'
        if where:
            conditions['where'] = where
            sql_query = sql_query.replace(';', ' WHERE {where};')
        self._db.row_factory = sqlite3.Row
        cur = self._db.execute(sql_query.format(**conditions))
        return cur.fetchall()
