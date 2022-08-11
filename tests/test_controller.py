# -*- coding: utf-8 -*-
import pytest

import xlsx2sqlite.controller as controller


@pytest.fixture
def new_controller(ini_path):
    return controller.new_controller(ini_path)


@pytest.fixture
def new_controller_diskdb(disk_db_ini):
    return controller.new_controller(disk_db_ini)


class TestController:
    def clean_before_tests(self):
        from pathlib import Path

        samples_path = Path("./tests/samples/")
        if samples_path / "test_db.sqlite":
            f = samples_path / "test_db.sqlite"
            f.unlink()

    def test_new_controller(self, new_controller):
        """support for in-memory database"""
        self.ctrler = new_controller
        assert self.ctrler is not None
        assert self.ctrler._ini is not None
        assert self.ctrler._ini.get("db_file") is None
        assert self.ctrler._ini.get("root_path") == "./tests/samples"
        assert self.ctrler.get_db_table_name("SalesOrders") == "Sales Orders"

    def test_initialize_db(self, new_controller_diskdb):
        """unit testing initialize_db method"""
        self.clean_before_tests()
        self.ctrler = new_controller_diskdb
        self.ctrler.initialize_db()
        self.ctrler = new_controller_diskdb
        res = self.ctrler.ls_entities(entity_type="table")
        tables = set(
            [
                self.ctrler.get_db_table_name(tablename)
                for tablename in self.ctrler._worksheets
            ]
        )
        assert set([t[1] for t in res]) == tables

    def test_drop_tables(self, new_controller_diskdb):
        self.clean_before_tests()
        self.ctrler = new_controller_diskdb
        self.ctrler.initialize_db()
        self.ctrler = new_controller_diskdb
        self.ctrler.drop_tables()
        self.ctrler = new_controller_diskdb
        res = self.ctrler.ls_entities(entity_type="table")
        assert res is None
