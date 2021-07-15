# -*- coding: utf-8 -*-
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
    """Field factory
    """
    fields = {
        "Field": Field,
        "Unique": UniqueField,
        "PrimaryKey": PrimaryKey,
        "NotNullField": NotNullField
    }
    return fields[type_of](field_name, field_type)


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


def get_table_level_constraint(clause: str, columns: list) -> object:
    """Table-level constraint class factory
    """
    definition = {
        "Unique": "UNIQUE",
        "PrimaryKey": "PRIMARY KEY"
    }
    return TableConstraint(definition[clause], columns)


class Definitions:
    """Definitions generator for Sqlite3 tables.
    """
    def __init__(self, name=None, headers=None, row=None, primary_key=None, unique_keys=None):
        try:
            if headers is None or row is None:
                raise TypeError
            self.tablename = name
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
