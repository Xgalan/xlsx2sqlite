# -*- coding: utf-8 -*-
import pytest

import xlsx2sqlite.constraint_factory as csf


@pytest.fixture(scope="module")
def column_list():
    return ["col" + "{0}".format(n) for n in range(10)]


def test_create_table_constraint(column_list):
    tc = csf.create_table_constraint(clause="Unique", columns=column_list)
    print(tc)
    assert str(tc) == "<UNIQUE({0})>".format(column_list)
    assert (
        tc.to_sql()
        == "UNIQUE(`col0`,`col1`,`col2`,`col3`,`col4`,`col5`,`col6`,`col7`,`col8`,`col9`)"
    )


def test_create_field():
    field = csf.Field(field_name="col1", field_type="INT", definition="PrimaryKey")
    print(field)
    assert str(field) == "<Field col1, type=INT, definition=NOT NULL PRIMARY KEY>"
