# -*- coding: utf-8 -*-
from genericpath import exists
from pathlib import Path
import pytest


@pytest.fixture(scope="module")
def ini_path():
    return Path("./tests/parsing_test.ini", exists=True).resolve()


@pytest.fixture(scope="module")
def disk_db_ini():
    return Path("./tests/disk_database.ini", exists=True).resolve()