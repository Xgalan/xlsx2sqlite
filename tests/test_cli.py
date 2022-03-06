# -*- coding: utf-8 -*-
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


def test_initialize_no_pk(no_pk_ini):
    response = runner.invoke(cli, [str(no_pk_ini), "initialize-db"])
    # KeyError on ini file, why ? Operations are correct.
    assert response.exit_code == 1


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
    response1 = runner.invoke(cli, [str(disk_db_ini), "list-def", "all"])
    assert response1.exit_code == 0


def test_replace(disk_db_ini):
    response0 = runner.invoke(cli, [str(disk_db_ini), "initialize-db"])
    assert response0.exit_code == 0
    response1 = runner.invoke(cli, [str(disk_db_ini), "update", "SalesOrders"])
    assert response1.exit_code == 0


def test_create_views(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "create-views"])
    assert response.exit_code == 0


def test_drop_tables(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "drop-tables", "--yes"])
    assert response.exit_code == 0


def test_drop_views(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "drop-views", "--yes"])
    assert response.exit_code == 0
