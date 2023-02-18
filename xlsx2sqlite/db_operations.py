# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
import sqlite3.dump
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Dict, Protocol

from xlsx2sqlite.definitions_factory import Definitions


class Observer(Protocol):
    def update(self, subject: Subject) -> None:
        pass


class Subject:
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer) -> None:
        with suppress(ValueError):
            self._observers.remove(observer)

    def notify(self, modifier: Observer | None = None) -> None:
        for observer in self._observers:
            if modifier != observer:
                observer.update(self)


def best_fts_version():
    """Discovers the most advanced supported SQlite FTS version."""
    conn = sqlite3.connect(":memory:")
    for fts in ("FTS5", "FTS4", "FTS3"):
        try:
            conn.execute()
            return fts
        except sqlite3.OperationalError:
            continue
    return None


class SqlOperation(ABC):

    COMMA_DELIM = ","

    def __init__(self, db, **kwargs) -> None:
        self._conn = db._conn
        self.kwargs = dict(**kwargs)

    def __str__(self) -> str:
        return self._prepare()

    def _prepare_sql(self, parameters) -> str:
        q = self._get_sql_string().format(**parameters)
        if q.endswith(";;"):
            q = q[:-1]
        return q

    def run(self, data=None) -> sqlite3.Cursor:
        """Execute operation on the database.

        :key data: List of values to be passed as arguments
                   to the SQL statement.
        :returns: a ``sqlite3.Cursor``
        :rtype: sqlite3.Cursor
        """
        sql_query = str(self)
        return (
            self._conn.execute(sql_query)
            if data is None
            else self._conn.executemany(sql_query, data)
        )

    @abstractmethod
    def _get_sql_string(self) -> str:
        raise NotImplementedError("Define a SQL query to use.")

    @abstractmethod
    def _prepare(self) -> str:
        raise NotImplementedError("You should implement this!")


class Transaction(Subject):
    """Class that interface with sqlite3 standard library module.

    Creates a database connection.

    :key path: Full path of the database, if the full path isn't
               specified the class will instantiate a sqlite3
               in memory database.
    """

    __shared_state: Dict[str, str] = {}  # Borg design pattern, shared state

    def __init__(self, path=None) -> None:
        self.__dict__ = self.__shared_state
        super().__init__()
        self.path = path
        self._log = []
        self.__in_memory = False if path else True

    def __enter__(
        self,
    ):  # TODO: if returns self._conn it return the connection object directly, move other methods to SqlOperation class
        self._conn = sqlite3.connect(
            ":memory:" if self.__in_memory else self.path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
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

    @log.setter
    def log(self, message):
        self._log.append(message)
        self.notify()

    @property
    def is_in_memory(self):
        return self.__in_memory

    def close(self):
        """Closes the connection to the database."""
        self._conn.close()

    def iterdump(self):
        """Returns the iterdump method."""
        return self._conn.iterdump()

    def executescript(self, sql: str) -> sqlite3.Cursor:
        """
        Execute multiple SQL statements separated by ; and return the ``sqlite3.Cursor``.
        Useful for restoring database after iterdump.

        :param: sql: SQL to execute
        """
        return self._conn.executescript(sql)


class CreateTable(SqlOperation):
    """Prepare and execute a CREATE TABLE sql query for a given table
    instance.

    The query executed is in this form:

    .. code-block:: sql

        CREATE TABLE IF NOT EXISTS tablename (definitions);

    :key model: model of the data to be replaced.
    """

    def _get_sql_string(self) -> str:
        return "CREATE TABLE IF NOT EXISTS `{name}` ({definitions});"

    def _prepare(self) -> str:
        # create definitions
        definitions = Definitions(
            model=self.kwargs["model"],
        )
        parameters = {
            "name": definitions.tablename,
            "definitions": definitions.prepare_sql(),
        }
        return self._prepare_sql(parameters)


class CreateView(SqlOperation):
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

    def _get_sql_string(self) -> str:
        return "CREATE VIEW IF NOT EXISTS `{name}` AS {select};"

    def _prepare(self) -> str:
        parameters = {"name": self.kwargs["viewname"], "select": self.kwargs["select"]}
        return self._prepare_sql(parameters)


class DropEntity(SqlOperation):
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

    def _get_sql_string(self) -> str:
        return "DROP {entity} IF EXISTS `{name}`;"

    def _prepare(self) -> str:
        parameters = {
            "entity": self.kwargs["entity_type"],
            "name": self.kwargs["entity_name"],
        }
        if self.kwargs["entity_type"] in ["TABLE", "VIEW"]:
            return self._prepare_sql(parameters)
        else:
            raise ValueError


class InsertInto(SqlOperation):
    """Populate the given table with data from the collection.

    :key model: model of the data to be replaced.
    """

    def _get_sql_string(self) -> str:
        return "INSERT INTO `{tablename}` ({fields}) VALUES ({args});"

    def _prepare(self) -> str:
        # create definitions
        definitions = Definitions(
            model=self.kwargs["model"],
        )
        parameters = {
            "tablename": definitions.tablename,
            "fields": definitions.get_labels(),
            "args": self.COMMA_DELIM.join(len(definitions.get_fields()) * "?"),
        }
        return self._prepare_sql(parameters)


class Replace(SqlOperation):
    """Perform a `REPLACE` operation on the database.

    :key model: model of the data to be replaced.
    """

    def _get_sql_string(self) -> str:
        return """REPLACE INTO `{tablename}` ({fields}) VALUES ({args});"""

    def _prepare(self) -> str:
        # create definitions
        definitions = Definitions(
            model=self.kwargs["model"],
        )
        if definitions.table_constraints is None:
            raise ValueError
        parameters = {
            "tablename": definitions.tablename,
            "fields": definitions.get_labels(),
            "args": self.COMMA_DELIM.join(len(definitions.get_fields()) * "?"),
        }
        return self._prepare_sql(parameters)


class Pragma(SqlOperation):
    """Executes a `PRAGMA` query on the database.

    The query executed is in this form:

    .. code-block:: sql

        PRAGMA table_info(tablename);
        PRAGMA database_list;

    :key pragma: pragma operation to execute, can be "table_info" or "database_list"
    :key tablename: Name of the table.
    :returns: A sqlite3 cursor containing the results of the query, if any.
    :rtype: object
    """

    def _get_sql_string(self) -> str:
        SQL_STRING = {
            "table_info": "PRAGMA table_info(`{tablename}`);",
            "database_list": "PRAGMA database_list;",
        }
        if self.kwargs["pragma"]:
            return SQL_STRING[self.kwargs["pragma"]]
        else:
            raise KeyError

    def _prepare(self) -> str:
        return self._prepare_sql({"tablename": self.kwargs["tablename"]})


class Select(SqlOperation):
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

    def _get_sql_string(self) -> str:
        if "where" in self.kwargs.keys():
            return "SELECT {columns} FROM `{from_table}` WHERE {where};"
        else:
            return "SELECT {columns} FROM `{from_table}`;"

    def _prepare(self) -> str:
        conditions = {
            "columns": self.kwargs["columns"]
            if "columns" in self.kwargs.keys()
            else "*",
            "from_table": self.kwargs["from_table"],
            "where": self.kwargs["where"] if "where" in self.kwargs.keys() else None,
        }
        return self._prepare_sql(conditions)
