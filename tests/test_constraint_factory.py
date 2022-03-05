# -*- coding: utf-8 -*-
import pytest

import xlsx2sqlite.constraint_factory as csf


@pytest.fixture(scope="module")
def column_list():
    return ["col" + "{0}".format(n) for n in range(10)]


def test_create_table_constraint(column_list):
    tc = csf.create_table_constraint(clause="Unique", columns=column_list)
    assert str(tc) == "<UNIQUE({0})>".format(column_list)
    assert (
        tc.to_sql()
        == "UNIQUE(`col0`,`col1`,`col2`,`col3`,`col4`,`col5`,`col6`,`col7`,`col8`,`col9`)"
    )
