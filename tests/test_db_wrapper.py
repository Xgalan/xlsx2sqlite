# -*- coding: utf-8 -*-
import pytest

from xlsx2sqlite.db_wrapper import DatabaseWrapper


@pytest.fixture()
def definitions():
    return """ 'id' INTEGER PRIMARY KEY, \
               'col1' TEXT, \
               'col2' BLOB, \
               'col3' REAL, \
               'col4' INT
               """

@pytest.fixture()
def fake_data():
    return [(1, 'test1', None, 1.2, 5),
            (2, 'test2', 'Some', 2.2, 6),
            (3, 'test3', None, 2.66, 1),
            ]

NAME = 'testtable'

def test_createdb(definitions):
    db = DatabaseWrapper()
    db.create_table(tablename=NAME,
                    definitions=definitions)
    s = db.select(from_table=NAME)
    assert s == []

def test_insert_into(definitions, fake_data):
    db = DatabaseWrapper()
    db.create_table(tablename=NAME,
                    definitions=definitions)
    db.insert_into(tablename=NAME,
                   fields="'id', 'col1', 'col2', 'col3', 'col4'",
                   args="?,?,?,?,?",
                   data=fake_data)
    s = db.select(from_table=NAME)
    res = [row for row in s]
    assert any(res)
    
