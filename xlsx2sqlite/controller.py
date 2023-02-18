# -*- coding: utf-8 -*-
"""Core module. Contains the main controller class.
"""
from __future__ import annotations

from contextlib import closing
from io import StringIO
from pathlib import Path
from pprint import pformat

try:
    from typing import Any, Callable
except ImportError:
    from collections.abc import Callable

from xlsx2sqlite.config import Xlsx2sqliteConfig
from xlsx2sqlite.dataset import Dataset
from xlsx2sqlite.db_operations import (
    CreateTable,
    CreateView,
    DropEntity,
    InsertInto,
    Pragma,
    Replace,
    Select,
    Transaction,
)
from xlsx2sqlite.import_export import export_worksheet

__all__ = ["new_controller"]


def new_controller(config: object) -> object:
    """Controller class factory

    :returns: An instance of Controller
    :rtype: object
    """
    return Controller(
        collection=Dataset, conf=Xlsx2sqliteConfig(config), database=Transaction
    )


class Controller:

    COMMA_DELIM = ","

    def __init__(self, collection: Callable, conf: object, database: object) -> None:
        self._collection = collection()
        self._db = database
        if conf is not None:
            self._memory_db = False
            self.setup(conf=conf)
        else:
            raise ValueError

    def __getattr__(self, name: str) -> Any | Callable:
        attr = getattr(self._collection, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            return attr(*args, **kwargs)

        return wrapper

    def setup(self, conf) -> None:
        """Creates a connection with the specified Sqlite3 database.

        :param conf: Full path of the configuration file, if no path is
                     given the DatabaseWrapper class will initialize an
                     in memory database.
        """
        self._ini = conf
        self._db_file = self._ini.get("db_file")
        self._log_file = self._ini.get("log_file")
        self._conn = self._db(path=self._db_file)
        self._memory_db = True if self._conn.is_in_memory else False
        self._views_path = self._ini.get("sql_views")
        self._workbook = self._ini.get("xlsx_file")
        self._worksheets = self._ini.get_tables_names
        self._models = self._ini.get_models
        # observer pattern
        self._conn.attach(self)

    def update(self, subject):
        "Observer pattern"
        if self._log_file:
            with open(self._log_file, mode="a") as f:
                f.write(pformat(subject.log[-1]))
                f.close()

    def close_db(self):
        """Close the connection to the database."""
        self._conn.close()

    def get_db_table_name(self, tablename):
        """Return the name to give to the database table.

        :param tablename: Name of the table to check if it is declared a 'db_table' attribute
                          in the INI file.
        :returns: A string representing the name of the database table as declared
                  in the INI file.
        :rtype: string
        """
        db_table = self._ini.get_db_tables_names[tablename]
        return db_table[0] if isinstance(db_table, list) else tablename

    def import_table(self, tablename=None):
        """Import the given table in the collection.

        :key tablename: Name of the table to be imported.
        :returns: A dict with data consisting in the rows imported from the xlsx file
                  and an instance of Definition class
        :rtype: dict
        """
        # check if the table has already been imported
        if tablename not in self._collection:
            self.create_dataset(
                workbook=self._workbook,
                worksheet=tablename,
                subset_cols=self._ini.get_columns_to_import,
                header=self._models[tablename]["header"],
            )
        if self._models is not None:
            # retrieve rows
            table = self.get(tablename)
            self._models[tablename]["headers"] = table.headers
            self._models[tablename]["first_row"] = table[0]
            self._models[tablename]["db_table_name"] = self.get_db_table_name(tablename)
            return {"data": table, "model": self._models[tablename]}
        else:
            raise ValueError

    def initialize_db(self):
        """Creates the database tables and populates them with the data
        imported from the tables in the collection.

        The collection contains tablib.Dataset instances.
        """
        with closing(self._conn) as db:
            with db:
                for ws in self._worksheets:
                    table = self.import_table(ws)
                    op1 = CreateTable(db, model=table["model"])
                    op1.run()
                    op2 = InsertInto(db, model=table["model"])
                    op2.run(data=[v for v in table["data"]])

    def insert_or_replace(self, tablename=None):
        """Perform a REPLACE operation on the database.

        :key tablename: Name of the table on which to perform the REPLACE operation.
        """
        TABLE_NOT_FOUND = "Table {} not found.".format(tablename)
        PRIMARYKEY_NOT_FOUND = (
            "Primary Key not found on {}, REPLACE operation aborted.".format(tablename)
        )

        if tablename in self._worksheets:
            table = self.import_table(tablename)
            with closing(self._conn) as db:
                with db:
                    db_table = self.get_db_table_name(tablename)
                    tinfo = Pragma(db, pragma="table_info", tablename=db_table)
                    s = tinfo.run().fetchall()
                    if s == []:
                        return TABLE_NOT_FOUND
                    db_pk = [dict(i) for i in s if dict(i)["pk"] == True][0]["name"]
                    columns = self._ini.get_columns_to_import[tablename]
                    if db_pk not in columns:
                        columns.insert(0, db_pk)
                    try:
                        # retrieve first row from new data
                        first_row = dict(zip(table["data"].headers, table["data"][0]))
                        # check if the primary key is in new data
                        if db_pk in first_row:
                            replace = Replace(db, model=table["model"])
                            replace.run(data=[v for v in table["data"]])
                        else:
                            return PRIMARYKEY_NOT_FOUND
                    except ValueError:
                        return PRIMARYKEY_NOT_FOUND
        else:
            return TABLE_NOT_FOUND

    def drop_tables(self):
        """Drop all the database tables if the name is declared in the configuration file."""
        db_tables = [
            self.get_db_table_name(tablename) for tablename in self._worksheets
        ]
        with closing(self._conn) as db:
            with db:
                for t in db_tables:
                    op = DropEntity(db, entity_name=t, entity_type="TABLE")
                    op.run()

    def drop_table(self, tablename=None):
        """Drop the database table with the corresponding worksheet name.

        :key db: Connection object
        :key tablename: Name of the table to drop from the database.
        """
        t = self.get_db_table_name(tablename)
        with closing(self._conn) as db:
            with db:
                ope = DropEntity(db, entity_name=t, entity_type="TABLE")
                ope.run()

    def create_views(self):
        if self._views_path:
            with closing(self._conn) as db:
                with db:
                    for f in list(Path(self._views_path).glob("**/*.sql")):
                        op = CreateView(db, viewname=f.stem, select=f.read_text())
                        op.run()

    def drop_views(self):
        """Drop all the views from the database."""
        if self._views_path:
            with closing(self._conn) as db:
                with db:
                    viewnames = [
                        f.stem for f in list(Path(self._views_path).glob("**/*.sql"))
                    ]
                    for v in viewnames:
                        op = DropEntity(db, entity_name=v, entity_type="VIEW")
                        op.run()

    def select_all(self, table_name=None, where_clause=None):
        """Perform a `SELECT *` SQL query on the database.

        :key table_name: Name of the table or view to query.
        :key where_clause: Valid SQL `WHERE` clause.
        :returns: A table as a tablib.Dataset instance.
        :rtype: tablib.Dataset
        """
        parameters = {"from_table": table_name}
        results = None
        with closing(self._conn) as db:
            with db:
                if table_name in self._worksheets:
                    table = self.import_table(table_name)
                    if self._memory_db:
                        op1 = CreateTable(db, model=table["model"])
                        op1.run()
                        op2 = InsertInto(db, model=table["model"])
                        op2.run(data=[v for v in table["data"]])
                        if self._views_path:
                            for f in list(Path(self._views_path).glob("**/*.sql")):
                                op = CreateView(
                                    db, viewname=f.stem, select=f.read_text()
                                )
                                op.run()
                if where_clause:
                    parameters["where"] = where_clause
                op3 = Select(db, **parameters)
                q = op3.run().fetchall()
                if q:
                    results = self._dataset(
                        *[tuple(row) for row in q], headers=q[0].keys()
                    )
        return results

    def ls_entities(self, entity_type=None):
        """List all the entities in the database.

        :key entity_type: Type of the entity to list.
        :returns: A table as a tablib.Dataset instance.
        :rtype: tablib.Dataset
        """
        parameters = {"table_name": "sqlite_master"}
        results = None
        if entity_type in ["table", "view"]:
            parameters["where_clause"] = "type='{ent_type}'".format(
                ent_type=entity_type
            )
        q = self.select_all(**parameters)
        if q:
            results = q.subset(cols=["type", "name"])
        return results

    def dump_database(self):
        """Dump database in SQL format."""
        results = StringIO()
        with closing(self._conn) as db:
            with db:
                [results.write(f"{line}\n") for line in db.iterdump()]
        return results

    def export_worksheet(self, filename=None, viewname=None, rows=None):
        """Relay function to export_worksheet"""
        export_worksheet(filename=filename, ws_name=viewname, rows=rows)
