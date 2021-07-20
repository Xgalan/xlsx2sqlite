# -*- coding: utf-8 -*-
"""Classes for creating the necessary configuration parsing the options from the .ini file.
"""
import configparser

from click.termui import secho



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
        return f'<Configuration: {self.options}>'

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
                return [v[option] for k,v in self.options.items() if option in v][0]
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
        self._parser.read(ini)
        self._inipath = ini
        self.options = {
            section: dict(self._parser[section]) for section in self._parser.sections()
        }


class Xlsx2sqliteConfig(IniParser):
    """Config model for xlsx2sqlite, checks if the supplied file is conformant with the specifications.
    """

    COMMA_DELIM = ','
    
    MANDATORY_SECTIONS = [
        'PATHS',
        'WORKSHEETS'
    ]
    
    OPTIONAL_SECTIONS = {
        'CONSTRAINTS': None,
        'HEADERS': None
    }

    MODEL_KEYWORDS = [
        'table_name',
        'columns',
        'primary_key',
        'unique',
        'not_null'
    ]

    MODEL_TEMPLATE = {
        'worksheet': None,
        'header': None,
        'table_def': MODEL_KEYWORDS
    }

    def __init__(self, ini):
        super().__init__()
        self.import_config(ini)
        self.log = []
        try:
            for section in self.MANDATORY_SECTIONS:
                assert self.has_section(section)
        except AssertionError as err:
            raise KeyError("Must declare all the mandatory sections in the ini file.")
        for section in list(self.OPTIONAL_SECTIONS.keys()):
            if self.has_section(section):
                self.OPTIONAL_SECTIONS[section] = dict(self._parser.items(section))
            else:
                self.log.append(f'No {section} section specified in the .ini file')

    def get_model(self, tablename):
        """
        """
        worksheets_names = set(self.get_imports()['worksheets'])
        if tablename in worksheets_names:
            model = {
                tablename: {
                    keyword: str(self._parser.get(
                        tablename, keyword, fallback=None
                    )).split(
                        self.COMMA_DELIM
                    ) for keyword in self.MODEL_KEYWORDS
                }
            }
            return model

    def get_options(self):
        """Retrieve values of the optional sections if they exists

        :returns: A dictionary containing the options of the optional sections
        :rtype: dict
        """
        return self.OPTIONAL_SECTIONS

    def get_imports(self):
        """Retrieve the worksheets names and a subset of columns as declared.

        :returns: A dictionary with a list of worksheets names accessing the
                  `worksheets` key; a list of columns names as a representation
                  for the columns to be retrieved from a worksheet accessing
                  the `subset_cols` key of the dictionary.
                  The lists must be declared in the INI configuration file.
        :rtype: dict
        """
        def get_attrs(names, attribute):
            try:
                return dict([
                    (name, list(self.get(str(name + attribute).lower()).split(
                        self.COMMA_DELIM))) for name in names
                ])
            except IndexError:
                print('Must set an attribute with: {0}'.format(attribute))
        names = list(self.get('names').split(self.COMMA_DELIM))
        subset_cols = get_attrs(names, '_columns')
        return {
            'worksheets': names,
            'subset_cols': subset_cols
        }
