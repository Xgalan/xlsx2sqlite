# -*- coding: utf-8 -*-
import pytest

import xlsx2sqlite.controller as controller


@pytest.fixture
def new_controller(ini_path):
    return controller.new_controller(ini_path)


class TestController:
    def test_new_controller(self, new_controller):
        """support for in-memory database"""
        self.ctrler = new_controller
        self.ctrler._db.attach(self.ctrler)
        assert self.ctrler is not None
        assert self.ctrler._config is not None
        assert self.ctrler._ini.get("db_file") is None
        assert self.ctrler._ini.get("root_path") == "./tests/samples"
        assert self.ctrler.get_db_table_name("SalesOrders") == "Sales Orders"

    def test_initialize_db(self, new_controller):
        """unit testint initialize_db method"""
        self.test_new_controller(new_controller)
        self.ctrler.initialize_db(close_db=False)
        res = self.ctrler.ls_entities(entity_type="table")
        assert any(res)
        tables = set([self.ctrler.get_db_table_name(tablename) for tablename in self.ctrler._worksheets])
        assert set([t[1] for t in res]) == tables

    def test_drop_tables(self, new_controller):
        self.test_initialize_db(new_controller)
        self.ctrler.drop_tables()
        res = self.ctrler.ls_entities(entity_type="table")
        assert res is None
