# -*- coding: utf-8 -*-
from urllib import response
from click.testing import CliRunner
from xlsx2sqlite.cli import cli

runner = CliRunner()


def test_cli():
    response = runner.invoke(cli, ["--help"])
    assert response.exit_code == 0


def test_initialize_inmemory_db(ini_path):
    response = runner.invoke(cli, [str(ini_path), "initialize-db"])
    assert response.exit_code == 0


def test_initialize_disk_db(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "initialize-db"])
    assert response.exit_code == 0


def test_export_view(disk_db_ini):
    response0 = runner.invoke(cli, [str(disk_db_ini), "initialize-db"])
    assert response0.exit_code == 0
    response1 = runner.invoke(
        cli, [str(disk_db_ini), "export-view", "'Complex UTF-8 key value àèò§'"]
    )
    assert response1.exit_code == 0


def test_list_def(disk_db_ini):
    response0 = runner.invoke(cli, [str(disk_db_ini), "initialize-db"])
    assert response0.exit_code == 0
    response1 = runner.invoke(
        cli, [str(disk_db_ini), "list-def", "all"]
    )
    assert response1.exit_code == 0


def test_drop_tables(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "drop-tables", "--yes"])
    assert response.exit_code == 0
