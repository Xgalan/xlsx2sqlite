# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from xlsx2sqlite.config import Xlsx2sqliteConfig



@pytest.fixture
def ini_path():
    return Path('./tests/parsing_test.ini', exists=True).resolve()


@pytest.fixture
def mandatory_sections():
    return set(['PATHS', 'WORKSHEETS'])


@pytest.fixture
def model_keywords():
    return [
        'table_name',
        'columns',
        'primary_key',
        'unique',
        'not_null'
    ]


@pytest.fixture
def config(ini_path):
    config = Xlsx2sqliteConfig(ini_path)
    return config


def test_mandatory_sections(config, mandatory_sections):
    """Test if there are the mandatory sections in the .ini file.
    """
    for section in mandatory_sections:
        s = config.has_section(section)
        assert s == True


def test_worksheets_as_sections(config):
    """Test if the listed worksheets to import are declared as sections.
    """
    names = config.get_imports()['worksheets']
    assert any(names)
    for name in names:
        s = config.get(name)
        assert s['worksheet'] == name


def test_duplicate_keys(config):
    """Is it a problem working with duplicate keys in different sections of the ini file?
    Yes, it is... if using config.get method
    Use _parser.get, can use nested items
    """
    worksheets_names = config.get_imports()['worksheets']
    assert any(worksheets_names)
    names = [
        config._parser.get(name, 'worksheet', fallback=None) for name in worksheets_names
    ]
    assert names == worksheets_names
    models = {
        name: config.get(name) for name in worksheets_names
    }
    assert [k for k in models.keys()] == worksheets_names


def test_get_model(config):
    worksheets_names = config.get_imports()['worksheets']
    assert any(worksheets_names)
    m = config.get_model('SalesOrders')
    assert m['SalesOrders']['table_name'] == ['Sales Orders']
    cols = m['SalesOrders']['columns']
    assert type(cols) == list


def test_section_complex_name(config):
    sections = config.sections()
    pass


def test_custom_header_row(config):
    pass
