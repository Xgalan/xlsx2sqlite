# -*- coding: utf-8 -*-
"""Core module. Contains the main controller class.
"""
from pathlib import Path
from io import StringIO
from xlsx2sqlite.config import Xlsx2sqliteConfig
from xlsx2sqlite.dataset import Dataset
from xlsx2sqlite.db_wrapper import DatabaseWrapper
from xlsx2sqlite.definitions_factory import Definitions
from xlsx2sqlite.import_export import export_worksheet

__all__ = ["new_controller"]


def new_controller(config: object) -> object:
    """Controller class factory

    :returns: An instance of Controller
    :rtype: object
    """
    return Controller(conf=Xlsx2sqliteConfig(config))


class Controller:

    COMMA_DELIM = ","

    def __init__(self, conf=None, database=None):
        self._collection = Dataset()
        self._db = database or DatabaseWrapper
        if conf is not None:
            self.setup(conf=conf)
        else:
            raise ValueError

    def __getattr__(self, name):
        attr = getattr(self._collection, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            return attr(*args, **kwargs)

        return wrapper

    def setup(self, conf=None):
        """Creates a connection with the specified Sqlite3 database.

        :param conf: Full path of the configuration file, if no path is
                     given the DatabaseWrapper class will initialize an
                     in memory database.
        """
        self._ini = conf
        self._db_file = self._ini.get("db_file")
        self._conn = self._db(path=self._db_file)
        # observer pattern
        self._conn.attach(self)
        self._views_path = self._ini.get("sql_views")
        self._workbook = self._ini.get("xlsx_file")
        self._worksheets = self._ini.get_tables_names
        self._models = self._ini.get_models

    def update(self, subject):
        print(subject.log[-1])

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
        if isinstance(db_table, list):
            db_table = db_table[0]
        else:
            db_table = tablename
        return db_table

    def import_table(self, tablename=None):
        """Import the given table in the collection.

        :param tablename: Name of the table to be imported.
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
            # create definitions
            d = Definitions(
                name=self.get_db_table_name(tablename),
                headers=table.headers,
                row=table[0],
                model=self._models[tablename],
            )
            return {"data": table, "definitions": d}
        else:
            raise ValueError

    def initialize_db(self):
        """Creates the database tables and populates them with the data
        imported from the tables in the collection.

        The collection contains tablib.Dataset instances.
        """
        commands = [self.create_table, self.insert_into]
        with self._conn as db:
            [
                [command(db=db, tablename=name) for name in self._worksheets]
                for command in commands
            ]

    def create_table(self, db=None, tablename=None):
        """Create a new table in the database.

        Retrieve the constraints if they exists, then generates the
        definitions for the SQL query, finally creates the table
        in the database.
        The table name must exists in the tables collection.

        :key db: Connection object
        :key tablename: Name of the table to be created.
        """
        table = self.import_table(tablename)
        db.create_table(
            tablename=table["definitions"].tablename,
            definitions=table["definitions"].prepare_sql(),
        )

    def insert_into(self, db=None, tablename=None):
        """Insert data into the declared table.

        :key db: Connection object
        :key tablename: Name of the table to import from the xlsx file.
        """
        table = self.import_table(tablename)
        fields = table["definitions"].get_fields()
        db.insert_into(
            tablename=self.get_db_table_name(tablename),
            fields=table["definitions"].get_labels(),
            args=self.COMMA_DELIM.join(len(fields) * "?"),
            data=[v for v in table["data"]],
        )

    def insert_or_replace(self, tablename=None):
        """Perform a REPLACE operation on the database.

        :param tablename: Name of the table on which to perform the REPLACE operation.
        """
        TABLE_NOT_FOUND = "Table {} not found.".format(tablename)
        PRIMARYKEY_NOT_FOUND = (
            "Primary Key not found on {}, REPLACE operation aborted.".format(tablename)
        )

        if tablename in self._worksheets:
            table = self.import_table(tablename)
            with self._conn as db:
                db_table = self.get_db_table_name(tablename)
                tinfo = db.table_info(tablename=db_table)
                if tinfo == []:
                    return TABLE_NOT_FOUND
                db_pk = [dict(i) for i in tinfo if dict(i)["pk"] == True][0]["name"]
                columns = self._ini.get_columns_to_import[tablename]
                if db_pk not in columns:
                    columns.insert(0, db_pk)
                if table["definitions"].table_constraints is None:
                    return PRIMARYKEY_NOT_FOUND
                # retrieve first row from new data
                first_row = dict(zip(table["data"].headers, table["data"][0]))
                fields = table["definitions"].get_fields()
                # check if the primary key is in new data
                if db_pk in first_row:
                    db.insert_or_replace(
                        tablename=db_table,
                        fields=table["definitions"].get_labels(),
                        args=self.COMMA_DELIM.join(len(fields) * "?"),
                        data=[v for v in table["data"]],
                    )
                else:
                    return PRIMARYKEY_NOT_FOUND
        else:
            return TABLE_NOT_FOUND

    def drop_tables(self):
        """Drop all the database tables with a name in the list.

        :param tables_list: List of tables names to drop from the database.
        """
        db_tables = [
            self.get_db_table_name(tablename) for tablename in self._worksheets
        ]
        with self._conn as db:
            [db.drop_entity(entity_name=t, entity_type="TABLE") for t in db_tables]

    def drop_table(self, tablename=None):
        """Drop the database table with the corresponding name.

        :key tablename: Name of the table to drop from the database.
        """
        with self._conn as db:
            db.drop_entity(entity_name=tablename, entity_type="TABLE")

    def create_view(self, viewname=None, select=None):
        """Create a database view.

        :key viewname: Name of the view.
        :key select: `SELECT` query statement.
        """
        with self._conn as db:
            db.create_view(viewname=viewname, select=select)

    def create_views(self):
        if self._views_path:
            p = Path(self._views_path)
            with self._conn as db:
                [
                    db.create_view(viewname=f.stem, select=f.read_text())
                    for f in list(p.glob("**/*.sql"))
                ]

    def drop_view(self, viewname=None):
        """Drop the database view with the corresponding name.

        :key viewname: Name of the view to drop from the database.
        """
        with self._conn as db:
            db.drop_entity(entity_name=viewname, entity_type="VIEW")

    def drop_views(self):
        """Drop all the views from the database."""
        if self._views_path:
            p = Path(self._views_path)
            with self._conn as db:
                viewnames = [f.stem for f in list(p.glob("**/*.sql"))]
                [db.drop_entity(entity_name=v, entity_type="VIEW") for v in viewnames]

    def select_all(self, table_name=None, where_clause=None):
        """Perform a `SELECT *` SQL query on the database.

        :key table_name: Name of the table or view to query.
        :key where_clause: Valid SQL `WHERE` clause.
        :returns: A table as a tablib.Dataset instance.
        :rtype: tablib.Dataset
        """
        parameters = {"from_table": table_name}
        results = None
        with self._conn as db:
            if where_clause:
                parameters["where"] = where_clause
            q = db.select(**parameters)
            if q:
                results = self._dataset(*[tuple(row) for row in q], headers=q[0].keys())
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
        with self._conn as db:
            [results.write(f"{line}\n") for line in db.iterdump()]
        return results

    def export_worksheet(self, filename=None, viewname=None, rows=None):
        """Relay function to export_worksheet"""
        export_worksheet(filename=filename, ws_name=viewname, rows=rows)
