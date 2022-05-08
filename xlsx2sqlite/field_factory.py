# -*- coding: utf-8 -*-


class Field:
    """Represents a database field.

    :param type_of: The type to assign to the database table column, choose between:

                    - Field: generic field without a column level constraint
                    - Unique: field with a UNIQUE clause
                    - PrimaryKey: field with PRIMARY KEY column level constraint
                    - NotNullField: set a NOT NULL column constraint on the database column

    :type type_of: str
    :param field_name: Label for the column of the database table.
    :type field_name: str
    :param field_type: Column type as a string defined in sqlite column types.
    :type field_type: str
    :param definition: Type of column-level constraint to declare.
    :type definition: str
    :returns: An instance of a Field object with a to_sql() method that returns an
              appropriate SQL string.
    :rtype: object
    """

    SPACE_DELIM = " "

    """This dictionary represents the column-level constraints as SQL strings."""
    DEFINITIONS = {
        "Field": None,
        "Unique": "UNIQUE",
        "PrimaryKey": "NOT NULL PRIMARY KEY",
        "NotNull": "NOT NULL",
        None: None,
    }

    def __init__(self, field_name=None, field_type=None, definition=None):
        # Can say: if definition is a list then declare all items as column-level constraints !
        self.field_name = field_name
        self.field_type = field_type
        self.definition = definition

    def __repr__(self):
        return f"<Field {self.field_name}, type={self.field_type}, definition={self.DEFINITIONS[self.definition]}>"

    def label(self):
        """A form of the string with the leading and trailing characters removed.

        :returns: A form of the string with the leading and trailing characters removed.
        :rtype: str
        """
        backtick = "`"
        label = f"{backtick}{self.field_name.strip()}{backtick}"
        return label

    def to_sql(self):
        """Return a suitable string for using in the database.

        :returns: A capitalized form of the string with the leading
                  and trailing characters removed.
        :rtype: str
        """
        params = [self.label(), self.field_type]
        d = self.DEFINITIONS[self.definition]
        if d is not None:
            params.append(d)
        return self.SPACE_DELIM.join(params)
