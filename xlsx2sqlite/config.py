# -*- coding: utf-8 -*-
"""Classes for creating the necessary configuration parsing the options from the .ini file.
"""
import configparser

try:
    from functools import cached_property
except ImportError:
    from cached_property import cached_property


class IniParser:
    """Representation for accessing the options of the parsed
    configuration file.
    """

    def __init__(self, options=None):
        self.options = options
        self._parser = configparser.ConfigParser()

    def __iter__(self):
        for option in self.options:
            yield option

    def __repr__(self) -> str:
        return f"<Configuration: {self.options}>"

    def sections(self):
        """List all the sections parsed from the INI file.

        :returns: A list of all the sections declared in the INI file.
        :rtype: list
        """
        return [section for section in self.options]

    def has_section(self, section):
        return self._parser.has_section(section)

    def get(self, option):
        """Retrieve a specific option declared in the INI file.

        :param option: Name of the option to retrieve.

        :returns: The value of the option.
        :rtype: str
        """
        try:
            if option in self.options:
                return self.options[option]
            else:
                l = [v[option] for k, v in self.options.items() if option in v]
                if l:
                    return l[0]
        except KeyError as e:
            raise KeyError((str(e) + " not in the options list."))

    def import_config(self, ini):
        """Parse the configuration declared in the INI file.

        Parse the INI file using the `configparser` module, then creates a
        dictionary with all the parsed options.

        :param ini: The path of the INI configuration file to parse.

        :returns: All the options retrieved from the INI file.
        :rtype: dict
        """
        self._parser.read(ini, encoding='UTF8')
        self._inipath = ini
        self.options = {
            section: dict(self._parser[section]) for section in self._parser.sections()
        }


class Xlsx2sqliteConfig(IniParser):
    """Config model for xlsx2sqlite, checks if the supplied file is conformant with the specifications."""

    COMMA_DELIM = ","

    MANDATORY_SECTIONS = [
        "PATHS",
    ]

    OPTIONAL_SECTIONS = {"EXCLUDE": None}

    MODEL_KEYWORDS = [
        "db_table",
        "columns",
        "primary_key",
        "unique",
        "not_null",
        "header",
    ]

    def __init__(self, ini):
        super().__init__()
        if ini:
            self.import_config(ini)
            self.log = []
            try:
                for section in self.MANDATORY_SECTIONS:
                    assert self.has_section(section)
            except AssertionError as err:
                raise KeyError(
                    "Must declare all the mandatory sections in the ini file."
                )
            for section in list(self.OPTIONAL_SECTIONS.keys()):
                if self.has_section(section):
                    self.OPTIONAL_SECTIONS[section] = dict(self._parser.items(section))
                else:
                    self.log.append(
                        f"No [{section}] section specified in the .ini file"
                    )

    def get_reserved_words(self):
        if bool(self.get_options()["EXCLUDE"]):
            exclude = self.get_options()["EXCLUDE"]["sections"].split(self.COMMA_DELIM)
            return set([*self.MANDATORY_SECTIONS, *self.OPTIONAL_SECTIONS, *exclude])
        else:
            return set([*self.MANDATORY_SECTIONS, *self.OPTIONAL_SECTIONS])

    def get_options(self):
        """Retrieve values of the optional sections if they exists

        :returns: A dictionary containing the options of the optional sections
        :rtype: dict
        """
        return self.OPTIONAL_SECTIONS

    def get_model_keywords(self):
        """Return the keywords that can be used to define a model

        :returns: A list containing all the keywords used to define a model
        :rtype: list
        """
        return self.MODEL_KEYWORDS

    @cached_property
    def get_tables_names(self):
        """Find the names of the tables to import.

        :returns: A list of the worksheets to import
        :rtype: set
        """
        return set(self.sections()) - self.get_reserved_words()

    @cached_property
    def get_columns_to_import(self):
        """Retrieve the subset of columns to import as declared in the .ini file.

        :returns: A dictionary with a list of columns names as a representation
                  for the columns to be retrieved from a worksheet accessing
                  the `subset_cols` key of the dictionary.
                  The lists must be declared in the INI configuration file.
        :rtype: dict
        """
        return {t: self.get_models[t]["columns"] for t in self.get_tables_names}

    @cached_property
    def get_db_tables_names(self):
        """Retrieve the names to give to the database tables, if any.

        :returns: A dictionary with the choosen names to set as the database tables names.
        :rtype: dict
        """
        return {t: self.get_models[t]["db_table"] for t in self.get_tables_names}

    @cached_property
    def get_models(self):
        """Returns a representation of the models as configured in the .ini file.

        :returns: A representation of the models parsed from the .ini file.
        :rtype: dict
        """

        def get_table_config(table, attr):
            try:
                d = dict({attr: self._parser.get(table, attr, fallback=None)})
                if isinstance(d[attr], str):
                    return d[attr].split(self.COMMA_DELIM)
                else:
                    return None
            except AttributeError as err:
                raise err

        models = {name: {} for name in self.get_tables_names}
        for k in models.keys():
            models[k].update(
                {
                    keyword: get_table_config(k, keyword)
                    for keyword in self.MODEL_KEYWORDS
                }
            )
        return models
