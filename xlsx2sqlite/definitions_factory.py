# -*- coding: utf-8 -*-
from datetime import datetime

from xlsx2sqlite.constraint_factory import *


class Definitions:
    """Definitions generator for Sqlite3 tables."""

    COMMA_DELIM = ","

    def __init__(
        self,
        model=None,
    ):
        try:
            if model is None:
                raise TypeError
            self.tablename = model["db_table_name"]
            self.headers = model["headers"]
            self.row = model["first_row"]
            self.unique_keys = model["unique"]
            self.pk = model["primary_key"]
            self.not_null = model["not_null"]
            self.table_constraints = []
            # map types to column names
            self._fields = dict(
                zip(
                    self.headers,
                    [{"type": self.test_type(v)} for v in self.row],
                )
            )
            if self.pk is None:
                """If a table has a single column primary key and the declared type of that column
                is "INTEGER" and the table is not a WITHOUT ROWID table, then the column is known
                as an INTEGER PRIMARY KEY. The column become an alias for the rowid column.
                If an INSERT statement attempts to insert a NULL value into a rowid or integer
                primary key column, the system chooses an integer value to use as the rowid
                automatically.
                """
                self.primary_key = Field(
                    field_name="id", field_type="INTEGER", definition="PrimaryKey"
                )
            elif isinstance(self.pk, list):
                if any(set(self.pk) & set(self.headers)):
                    for key in self.pk:
                        if key in set(self._fields):
                            pass
                        else:
                            self.primary_key = Field(
                                field_name=key,
                                field_type="INTEGER",
                                definition="NotNull",
                            )
                    # support for composite primary key
                    self.table_constraints.append(
                        create_table_constraint(clause="PrimaryKey", columns=self.pk)
                    )
                else:
                    # set a custom name for the row_id alias
                    self.primary_key = Field(
                        field_name=self.pk[0],
                        field_type="INTEGER",
                        definition="PrimaryKey",
                    )
            if self.unique_keys and isinstance(self.unique_keys, list):
                self.table_constraints.append(
                    create_table_constraint(clause="Unique", columns=self.unique_keys)
                )
        except TypeError:
            print("Must declare headers and row.")
            return

    @staticmethod
    def test_type(value):
        """Detect the type of an object and return a Sqlite3 type affinity.

        :param value: An instance to check for affinity.
        :returns: The name of the Sqlite3 affinity type.
        :rtype: str
        """
        if isinstance(value, str):
            return "TEXT"
        elif isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, datetime):
            return "TIMESTAMP"
        elif value is None:
            return "BLOB"
        else:
            return "TEXT"

    def get_fields(self):
        """Get the list of fields for using as columns definitions.
        This method doesn't return the primary key in the list of fields.

        :returns: A list of Field instances describing the columns of the database.
        :rtype: list
        """

        def column_constraint(key):
            if pk is not None and key in pk:
                # workaround primary key field bug in sqlite, using NOT NULL column constraint
                return "NotNull"
            else:
                if not_null is not None and key in not_null:
                    return "NotNull"
                else:
                    return "Field"

        pk = None if self.pk is None else set(self.pk)
        not_null = None if self.not_null is None else set(self.not_null)
        fields = [
            Field(field_name=k, field_type=v["type"], definition=column_constraint(k))
            for k, v in self._fields.items()
        ]
        return fields

    def prepare_sql(self):
        """Returns the complete sql definition as a string.

        :returns: A string representing the SQL definitions for the CREATE TABLE statement.
        :rtype: str
        """
        fields = self.get_fields()

        if hasattr(self, "primary_key"):
            fields.insert(0, self.primary_key)
        sql_strings = [field.to_sql() for field in fields]
        if any(self.table_constraints):
            [
                sql_strings.append(costraint.to_sql())
                for costraint in self.table_constraints
            ]
        return self.COMMA_DELIM.join(sql_strings)

    def get_labels(self):
        labels = [field.label() for field in self.get_fields()]
        return self.COMMA_DELIM.join(labels)
