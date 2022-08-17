# -*- coding: utf-8 -*-
import sqlite3
import sqlite3.dump
from contextlib import suppress


class Subject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        with suppress(ValueError):
            self._observers.remove(observer)

    def notify(self, modifier=None):
        for observer in self._observers:
            if modifier != observer:
                observer.update(self)


class DatabaseWrapper(Subject):
    """Class that interface with sqlite3 standard library module.

    Creates a database connection.

    :key path: Full path of the database, if the full path isn't
               specified the class will instantiate a sqlite3
               in memory database.
    """

    SQL_QUERY = {
        "create_table": "CREATE TABLE IF NOT EXISTS `{name}` ({definitions});",
        "create_view": "CREATE VIEW IF NOT EXISTS `{name}` AS {select};",
        "drop_entity": "DROP {entity} IF EXISTS `{name}`;",
        "insert_into": "INSERT INTO `{tablename}` ({fields}) VALUES ({args});",
        "replace": """REPLACE INTO `{tablename}` ({fields}) VALUES ({args});""",
        "select_from": "SELECT {columns} FROM `{from_table}`;",
        "table_info": "PRAGMA table_info(`{tablename}`);",
        "database_list": "PRAGMA database_list;",
    }

    def __init__(self, path=None):
        super().__init__()
        if path is None:
            self._conn = sqlite3.connect(
                ":memory:", detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.__in_memory = True
        else:
            self._conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
            self.__in_memory = False
        self._log = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_traceb):
        if exc_type is None:
            try:
                self._conn.commit()
            except:
                self.log = "Error while committing changes to the database."
        elif exc_type is sqlite3.IntegrityError:
            self.log = exc_val
            # silence exceptions by returning some True value.
            return True
        elif exc_type is sqlite3.OperationalError:
            self.log = exc_val
            self._conn.rollback()
            raise exc_type
        else:
            self.log = (exc_type, exc_val)
            if exc_traceb:
                self.log = exc_traceb
            raise exc_type

    @property
    def log(self):
        return self._log

    @property
    def is_in_memory(self):
        return self.__in_memory

    @log.setter
    def log(self, message):
        self._log.append(message)
        self.notify()

    def close(self):
        """Closes the connection to the database."""
        self._conn.close()

    def iterdump(self):
        """Returns the iterdump method."""
        return self._conn.iterdump()

    def _execute(self, query, parameters, messages, data=None, many=False):
        try:
            if many is True:
                self._conn.executemany(query.format(**parameters), data)
            else:
                q = query.format(**parameters)
                if q.endswith(";;"):
                    q = q[:-1]
                self._conn.execute(q)
            # observer pattern
            self.log = messages["success"]
        except:
            print("Error from execute")

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
        parameters = {"name": tablename, "definitions": definitions}
        messages = {
            "error": "Error when creating table: ",
            "success": "Created table: " + parameters["name"],
        }
        self._execute(self.SQL_QUERY["create_table"], parameters, messages)

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
        parameters = {"name": viewname, "select": select}
        messages = {
            "error": "Error when creating view: ",
            "success": "Created view: " + parameters["name"],
        }
        self._execute(self.SQL_QUERY["create_view"], parameters, messages)

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
        parameters = {"entity": entity_type, "name": entity_name}
        messages = {
            "error": "Error when deleting " + entity_type + " " + entity_name,
            "success": "Deleted " + entity_type + " " + entity_name,
        }
        if entity_type in ["TABLE", "VIEW"]:
            self._execute(self.SQL_QUERY["drop_entity"], parameters, messages)

    def insert_into(self, tablename=None, fields=None, args=None, data=None):
        """Populate the given table with data from the collection.

        :key tablename: Name of the table to insert values into.
        :key fields: List of fields as accepted by the SQL language of Sqlite3.
        :key args: SQL arguments of the query.
        :key data: List of values to be passed as arguments
                   to the SQL statement.
        """
        parameters = {"tablename": tablename, "fields": fields, "args": args}
        messages = {"success": "Data inserted into table: {}".format(tablename)}
        self._execute(
            self.SQL_QUERY["insert_into"], parameters, messages, data=data, many=True
        )

    def insert_or_replace(self, tablename=None, fields=None, args=None, data=None):
        """Perform a `REPLACE` operation on the database.

        :key tablename: Name of the table to insert values into.
        :key fields: List of fields as accepted by the SQL language of Sqlite3.
        :key args: SQL arguments of the query.
        :key data: List of values to be passed as arguments
                   to the SQL statement.
        """
        parameters = {"tablename": tablename, "fields": fields, "args": args}
        messages = {"success": "Updated table: {}".format(tablename)}
        self._execute(
            self.SQL_QUERY["replace"], parameters, messages, data=data, many=True
        )

    def table_info(self, tablename=None):
        """Executes a `PRAGMA` query on the database.

        The query executed is in this form:

        .. code-block:: sql

            PRAGMA table_info(tablename);

        :key tablename: Name of the table.
        :returns: A sqlite3 cursor containing the results of the query, if any.
        :rtype: object
        """
        conditions = {"tablename": tablename}
        sql_query = self.SQL_QUERY["table_info"]
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(sql_query.format(**conditions))
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
        conditions = {"columns": columns, "from_table": from_table}
        sql_query = self.SQL_QUERY["select_from"]
        if columns is None:
            conditions["columns"] = "*"
        if where:
            conditions["where"] = where
            sql_query = sql_query.replace(";", " WHERE {where};")
        self._conn.row_factory = sqlite3.Row
        cur = self._conn.execute(sql_query.format(**conditions))
        return cur.fetchall()
