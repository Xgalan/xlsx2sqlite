# -*- coding: utf-8 -*-
__all__ = ["create_table_constraint"]


COMMA_DELIM = ','
SPACE_DELIM = ' '


def create_table_constraint(clause: str, columns: list) -> object:
    """Table-level constraint class factory
    """
    definition = {
        "Unique": "UNIQUE",
        "PrimaryKey": "PRIMARY KEY"
    }
    return TableConstraint(definition[clause], columns)


class TableConstraint:
    """Class for defining a table-level constraint on the table, permit to support a composite primary key.
    """
    def __init__(self, keyword, columns):
        self._keyword = keyword
        self._columns = columns

    def __repr__(self):
        return f'<{self._keyword}({self._columns})>'

    def to_sql(self):
        """Return a suitable string for using in the database.

        :returns: SQL definition in the form of a table level constraint, list of columns 
                  names to be declared with a clause.

                  i.e.: UNIQUE(col1, col2)
        :rtype: str
        """
        backtick = "`"
        return "{keyword}({columns})".format(
            keyword=self._keyword,
            columns=COMMA_DELIM.join([f'{backtick}{col}{backtick}' for col in self._columns])
        )
