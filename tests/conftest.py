# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True


@pytest.fixture(scope="module")
def ini_path():
    return Path("./tests/parsing_test.ini", exists=True).resolve()


@pytest.fixture(scope="module")
def disk_db_ini():
    return Path("./tests/disk_database.ini", exists=True).resolve()


@pytest.fixture(scope="module")
def no_pk_ini():
    return Path("./tests/no_primary_key.ini", exists=True).resolve()
