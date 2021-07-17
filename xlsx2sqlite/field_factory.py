# -*- coding: utf-8 -*-
__all__ = ["create_field"]


COMMA_DELIM = ','
SPACE_DELIM = ' '


def create_field(type_of: str, field_name: str, field_type: str) -> object:
    """Field factory
    """
    fields = {
        "Field": Field,
        "Unique": UniqueField,
        "PrimaryKey": PrimaryKey,
        "NotNullField": NotNullField
    }
    return fields[type_of](field_name, field_type)


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
