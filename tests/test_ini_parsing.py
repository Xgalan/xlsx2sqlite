# -*- coding: utf-8 -*-
import pytest

from xlsx2sqlite.config import Xlsx2sqliteConfig


@pytest.fixture
def mandatory_sections():
    return set(
        [
            "PATHS",
        ]
    )


@pytest.fixture
def model_keywords():
    return ["db_table", "columns", "primary_key", "unique", "not_null"]


@pytest.fixture
def config(ini_path):
    config = Xlsx2sqliteConfig(ini_path)
    return config


def test_mandatory_sections(config, mandatory_sections):
    """Test if there are the mandatory sections in the .ini file."""
    for section in mandatory_sections:
        s = config.has_section(section)
        assert s == True


def test_get_reserved_words(config):
    """Test get_reserved_words method."""
    reserved = config.get_reserved_words()
    assert any(reserved)


def test_worksheets_as_sections(config):
    """Test if the listed worksheets to import are declared as sections."""
    names = config.get_tables_names
    assert any(names)
    assert names == set(config.get_models.keys())


def test_duplicate_keys(config, model_keywords):
    """Is it a problem working with duplicate keys in different sections of the ini file?
    Yes, it is... if using config.get method
    Use _parser.get, can use nested items
    """
    worksheets_names = config.get_tables_names
    assert any(worksheets_names)

    names = [
        config._parser.get(name, "worksheet", fallback=None)
        for name in worksheets_names
    ]

    models = {name: config.get(name) for name in worksheets_names}
    assert [k for k in models.keys()] == list(worksheets_names)
    # TODO: assure that no model keywords is outside of a section as a key


def test_get_model(config):
    worksheets_names = config.get_tables_names
    assert any(worksheets_names)
    m = config.get_models
    assert m["SalesOrders"]["db_table"] == ["Sales Orders"]
    cols = m["SalesOrders"]["columns"]
    assert type(cols) == list


def test_section_complex_name(config, mandatory_sections):
    sections = config.sections()
    worksheets_names = config.get_tables_names
    assert set(sections) - mandatory_sections == worksheets_names
    assert "Complex UTF-8 key value àèò§" in worksheets_names


def test_custom_header_row(config):
    # TODO
    pass
