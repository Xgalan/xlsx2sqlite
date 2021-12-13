# -*- coding: utf-8 -*-
import pytest

import xlsx2sqlite.controller as controller

from tests.test_ini_parsing import ini_path



def test_new_controller(ini_path):
    """support for in-memory database
    """
    ctrler = controller.new_controller(ini_path)
    assert ctrler._config is not None
    assert ctrler._ini.get('db_file') is None
