# -*- coding: utf-8 -*-
from click.testing import CliRunner

from xlsx2sqlite.cli import cli

runner = CliRunner()


def test_cli():
    response = runner.invoke(cli, ["--help"])
    assert response.exit_code == 0


def test_initialize_inmemory_db(ini_path):
    result = runner.invoke(cli, [str(ini_path), "initialize-db"])
    assert result.exit_code == 0


def test_initialize_no_pk(no_pk_ini):
    resp = runner.invoke(cli, [str(no_pk_ini), "initialize-db"])
    assert resp.exit_code == 0


def test_initialize_disk_db(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "initialize-db"])
    assert response.exit_code == 0


def test_create_views(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "create-views"])
    assert response.exit_code == 0


def test_export_view(disk_db_ini):
    run = CliRunner()
    run.isolated_filesystem(temp_dir="/tmp")
    run.invoke(cli, [str(disk_db_ini), "initialize-db"])
    run.invoke(cli, [str(disk_db_ini), "create-views"])
    response1 = run.invoke(
        cli,
        [str(disk_db_ini), "export-view", "units_lt_10", "-f", "json"],
    )
    response2 = run.invoke(
        cli,
        [str(disk_db_ini), "export-view", "Complex UTF-8 key value àèò§", "-f", "csv"],
    )
    response3 = run.invoke(
        cli,
        [
            str(disk_db_ini),
            "export-view",
            "Complex UTF-8 key value àèò§",
            "-f",
            "xlsx",
            "-o",
            "/tmp/dest.xlsx",
        ],
    )
    assert response1.exit_code == 0
    assert response2.exit_code == 0
    assert response3.exit_code == 0


def test_list_def(disk_db_ini):
    response1 = runner.invoke(cli, [str(disk_db_ini), "list-def", "all"])
    assert response1.exit_code == 0


def test_replace(disk_db_ini):
    run = CliRunner()
    run.isolated_filesystem(temp_dir="/tmp")
    run.invoke(cli, [str(disk_db_ini), "initialize-db"])
    response1 = run.invoke(cli, [str(disk_db_ini), "update", "SalesOrders"])
    assert response1.exit_code == 0


def test_drop_tables(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "drop-tables", "--yes"])
    assert response.exit_code == 0


def test_drop_views(disk_db_ini):
    response = runner.invoke(cli, [str(disk_db_ini), "drop-views", "--yes"])
    assert response.exit_code == 0
