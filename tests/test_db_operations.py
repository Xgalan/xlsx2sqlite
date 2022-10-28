# -*- coding: utf-8 -*-
import pytest


from xlsx2sqlite.db_operations import (
    CreateTable,
    CreateView,
    DropEntity,
    InsertInto,
    Replace,
    Select,
    Pragma,
    Transaction,
)


@pytest.fixture()
def definitions():
    return """ 'id' INTEGER PRIMARY KEY, \
               'col1' TEXT, \
               'col2' BLOB, \
               'col3' REAL, \
               'col4' INT
               """


@pytest.fixture
def model():
    return {
        "db_table": ["testtable"],
        "db_table_name": "testtable",
        "headers": ["col1", "col2", "col3", "col4"],
        "first_row": ("test2", "Some", float(2.2), 6),
        "unique": None,
        "primary_key": None,
        "not_null": ["col4"],
    }


@pytest.fixture()
def fake_data():
    return [
        ("test1", None, 1.2, 5),
        ("test2", "Some", 2.2, 6),
        ("test3", None, 2.66, 1),
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
    return Transaction()


class TestTransaction:
    NAME = "testtable"
    VIEWNAME = "TestView"

    def test_createdb(self, inmemory_db):
        self.db = inmemory_db
        assert type(self.db) == Transaction

    def test_create_table(self, inmemory_db, model):
        self.test_createdb(inmemory_db)
        with self.db as db:
            db.run(CreateTable(connection=db, model=model))
            parameters = {
                "columns": "'id','col1','col2','col3','col4'",
                "from_table": self.NAME,
            }
            rows = db.run(Select(connection=db, **parameters)).fetchall()
            db.close()
        assert rows == []

    def test_insert_into(self, inmemory_db, model, fake_data):
        self.test_createdb(inmemory_db)
        with self.db as db:
            db.run(CreateTable(connection=db, model=model))
            db.run(InsertInto(connection=db, model=model), data=fake_data)
            s = db.run(Select(connection=db, from_table=self.NAME)).fetchall()
            db.close()
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (1, "test1", None, 1.2, 5)

    def test_create_view(self, inmemory_db, model, fake_data):
        self.test_createdb(inmemory_db)
        with self.db as db:
            db.run(CreateTable(connection=db, model=model))
            db.run(InsertInto(connection=db, model=model), data=fake_data)
            db.run(
                CreateView(
                    connection=db,
                    viewname=self.VIEWNAME,
                    select="SELECT * FROM {0}".format(self.NAME),
                )
            )
            s = db.run(Select(connection=db, from_table=self.VIEWNAME)).fetchall()
            db.close()
        res = [row for row in s]
        assert tuple(res[1]) == (2, "test2", "Some", float(2.2), 6)

    def test_drop_entity(self, inmemory_db, model, fake_data):
        self.test_createdb(inmemory_db)
        with self.db as db:
            db.run(CreateTable(connection=db, model=model))
            db.run(InsertInto(connection=db, model=model), data=fake_data)
            db.run(
                CreateView(
                    connection=db,
                    viewname=self.VIEWNAME,
                    select="SELECT * FROM {0}".format(self.NAME),
                )
            )
            db.run(
                DropEntity(connection=db, entity_name=self.VIEWNAME, entity_type="VIEW")
            )
            res = db.run(
                Pragma(connection=db, pragma="table_info", tablename=self.VIEWNAME)
            ).fetchall()
            db.close()
        assert res == []

    def test_select(self, inmemory_db, model, fake_data):
        self.test_createdb(inmemory_db)
        with self.db as db:
            db.run(CreateTable(connection=db, model=model))
            db.run(InsertInto(connection=db, model=model), data=fake_data)
            s = db.run(Select(connection=db, from_table=self.NAME)).fetchall()
            db.close()
        res = [row for row in s]
        assert any(res)
        assert tuple(res[0]) == (1, "test1", None, 1.2, 5)
