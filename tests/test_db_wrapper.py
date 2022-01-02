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


@pytest.fixture()
def fake_data2():
    return [
        (1, "test1", None, 1.2, 5),
        (2, "updated", "Some", 4.4, 12),
        (3, "test3", None, 2.66, 1),
    ]


@pytest.fixture
def inmemory_db():
    return DatabaseWrapper()


class TestDatabaseWrapper:
    NAME = "testtable"
    VIEWNAME = "TestView"

    def test_createdb(self, inmemory_db):
        self.db = inmemory_db
        assert type(self.db) == DatabaseWrapper

    def test_create_table(self, inmemory_db, definitions):
        self.test_createdb(inmemory_db)
        inmemory_db.create_table(tablename=self.NAME, definitions=definitions)
        rows = inmemory_db.select(
            columns="'id','col1','col2','col3','col4'", from_table=self.NAME
        )
        assert rows == []

    def test_insert_into(self, inmemory_db, definitions, fake_data):
        self.test_create_table(inmemory_db, definitions)
        inmemory_db.insert_into(
            tablename=self.NAME,
            fields="'id', 'col1', 'col2', 'col3', 'col4'",
            args="?,?,?,?,?",
            data=fake_data,
        )
        s = inmemory_db.select(from_table=self.NAME)
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (1, "test1", None, 1.2, 5)

    def test_create_view(self, inmemory_db, definitions, fake_data):
        self.test_insert_into(inmemory_db, definitions, fake_data)
        inmemory_db.create_view(
            viewname=self.VIEWNAME, select="SELECT * FROM {0}".format(self.NAME)
        )
        s = inmemory_db.select(from_table=self.VIEWNAME)
        res = [row for row in s]
        assert tuple(res[1]) == (2, "test2", "Some", 2.2, 6)

    def test_insert_or_replace(self, inmemory_db, definitions, fake_data, fake_data2):
        self.test_insert_into(inmemory_db, definitions, fake_data)
        inmemory_db.insert_or_replace(
            tablename=self.NAME,
            fields="'id', 'col1', 'col2', 'col3', 'col4'",
            args="?,?,?,?,?",
            data=fake_data2,
        )
    
    def test_select(self, inmemory_db, definitions, fake_data):
        self.test_insert_into(inmemory_db, definitions, fake_data)
        s = inmemory_db.select(from_table=self.NAME)
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (1, "test1", None, 1.2, 5)

    def test_drop_entity(self, inmemory_db, definitions, fake_data):
        self.test_create_view(inmemory_db, definitions, fake_data)
        inmemory_db.drop_entity(self.VIEWNAME, entity_type="VIEW")
        res = inmemory_db.table_info(tablename=self.VIEWNAME)
        assert res == []
