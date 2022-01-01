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
    return [
        (1, "test1", None, 1.2, 5),
        (2, "test2", "Some", 2.2, 6),
        (3, "test3", None, 2.66, 1),
    ]


NAME = "testtable"


def test_createdb():
    db = DatabaseWrapper()
    with db as db:
        assert any(db._db)


def test_create_table(definitions):
    db = DatabaseWrapper()
    with db as db:
        db.create_table(tablename=NAME, definitions=definitions)
        rows = db.select(columns="'id','col1','col2','col3','col4'", from_table=NAME)
        assert rows == []


def test_create_view(definitions, fake_data):
    db = DatabaseWrapper()
    VIEWNAME = "TestView"
    with db as db:
        db.create_table(tablename=NAME, definitions=definitions)
        db.create_view(viewname=VIEWNAME, select="SELECT * FROM {table}".format(NAME))
        db.insert_into(
            tablename=NAME,
            fields="'id', 'col1', 'col2', 'col3', 'col4'",
            args="?,?,?,?,?",
            data=fake_data,
        )
        s = db.select(from_table=VIEWNAME)
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (2, "test2", "Some", 2.2, 6)


def test_insert_into(definitions, fake_data):
    db = DatabaseWrapper()
    with db as db:
        db.create_table(tablename=NAME, definitions=definitions)
        db.insert_into(
            tablename=NAME,
            fields="'id', 'col1', 'col2', 'col3', 'col4'",
            args="?,?,?,?,?",
            data=fake_data,
        )
        s = db.select(from_table=NAME)
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (1, "test1", None, 1.2, 5)
