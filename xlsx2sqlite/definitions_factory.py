# -*- coding: utf-8 -*-
from datetime import datetime

import xlsx2sqlite.constraint_factory as constraint
import xlsx2sqlite.field_factory as field


class Definitions:
    """Definitions generator for Sqlite3 tables.
    """

    COMMA_DELIM = ','

    def __init__(self, name=None, headers=None, row=None, primary_key=None, unique_keys=None):
        try:
            if headers is None or row is None:
                raise TypeError
            self.tablename = name
            self.headers = headers
            self.row = row
            self.unique_keys = unique_keys
            self.table_constraints = []
            # map types to column names
            self._fields = dict(
                zip(self.headers,
                    [{"type": self.test_type(v), "cls": 'Field'} for v in self.row]
                )
            )
            if primary_key is None:
                """If a table has a single column primary key and the declared type of that column
                is "INTEGER" and the table is not a WITHOUT ROWID table, then the column is known
                as an INTEGER PRIMARY KEY. The column become an alias for the rowid column.
                If an INSERT statement attempts to insert a NULL value into a rowid or integer
                primary key column, the system chooses an integer value to use as the rowid 
                automatically.
                """
                self.primary_key = field.create_field('PrimaryKey', 'id', 'INTEGER')
            elif isinstance(primary_key, list):
                if any(set(primary_key) & set(headers)):
                    # workaround primary key field bug in sqlite, using NOT NULL column constraint
                    for key in primary_key:
                        if key in self._fields:
                            self._fields[key]['cls'] = 'NotNullField'
                        else:
                            self.primary_key = field.create_field('NotNullField', key, 'INTEGER')
                    # support for composite primary key
                    self.table_constraints.append(
                        constraint.create_table_constraint(clause="PrimaryKey", columns=primary_key)
                    )
                else:
                    # set a custom name for the row_id alias
                    self.primary_key = field.create_field('PrimaryKey', primary_key[0], 'INTEGER')
            if unique_keys and isinstance(unique_keys, list):
                self.table_constraints.append(
                    constraint.create_table_constraint(clause="Unique", columns=unique_keys)
                )
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
    
    def get_fields(self):
        """Get the list of fields for using as columns definitions.
        This method doesn't return the primary key in the list of fields.

        :returns: A list of Field instances describing the columns of the database.
        :rtype: list
        """
        fields = [field.create_field(v['cls'], k, v['type']) for k,v in self._fields.items()]
        return fields

    def prepare_sql(self):
        """Returns the complete sql definition as a string.

        :returns: A string representing the SQL definitions for the CREATE TABLE statement.
        :rtype: str
        """
        fields = self.get_fields()

        if hasattr(self, 'primary_key'):
            fields.insert(0, self.primary_key)
        sql_strings = [field.to_sql() for field in fields]
        if any(self.table_constraints):
            [sql_strings.append(costraint.to_sql()) for costraint in self.table_constraints]
        return self.COMMA_DELIM.join(sql_strings)

    def get_labels(self):
        labels = [field.label() for field in self.get_fields()]
        return self.COMMA_DELIM.join(labels)
