# -*- coding: utf-8 -*-

from pathlib import Path
import pytest


@pytest.fixture(scope="module")
def ini_path():
    return Path("./tests/parsing_test.ini", exists=True).resolve()
