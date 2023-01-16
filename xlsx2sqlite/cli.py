# -*- coding: utf-8 -*-
"""Command line interface for xlsx2sqlite API.

Parse the INI file passed as argument for retrieving the options, then
executes the choosen command.
"""
import click

import xlsx2sqlite.controller as controller


@click.group("cli")
@click.argument("ini", required=True, type=click.Path(exists=True))
@click.pass_context
def cli(ctx, ini):
    """Generate a Sqlite3 database parsing options from a .INI
    configuration file.
    """
    try:
        ctx.obj = controller.new_controller(ini)
    except KeyError as err:
        click.secho(str(err), bg="red", fg="black")
        raise click.Abort
    # check for warning messages
    [click.secho(msg, bg="yellow", fg="black") for msg in ctx.obj._ini.log]
    click.secho("Parsed the config file.", bg="green", fg="black")


@cli.command()
@click.pass_context
def initialize_db(ctx):
    """Database creation and initialization.

    Populates the database with data imported from the worksheets.
    """
    ctx.obj.initialize_db()
    click.secho("Finished importing.", bg="green", fg="black")


@cli.command()
@click.argument("table-name", type=click.STRING)
@click.pass_context
def update(ctx, table_name):
    """Upsert data on a specified table."""
    if table_name:
        res = ctx.obj.insert_or_replace(tablename=table_name)
        if res is None:
            click.secho("Finished importing.", bg="green", fg="black")
        else:
            click.secho(res, bg="red", fg="black")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to drop the tables?")
@click.pass_context
def drop_tables(ctx):
    """Drop the tables in the database.

    Drop only the tables which have a name corresponding
    to the worksheets specified in the config file.
    """
    ctx.obj.drop_tables()


@cli.command()
@click.pass_context
def create_views(ctx):
    """Create database views.

    Create views on the database loading `*.sql` from the path specified in
    the INI config file. A file must contain a valid `SELECT` query.
    """
    ctx.obj.create_views()


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to drop the views?")
@click.pass_context
def drop_views(ctx):
    """Drop the views in the database.

    Drop all the views from the database.
    """
    ctx.obj.drop_views()


@cli.command()
@click.argument("viewname", required=True, type=click.STRING)
@click.option(
    "-f",
    "file_format",
    type=click.STRING,
    help="Desired file format for the exported data.",
)
@click.option(
    "-o", "dest", type=click.File("wb"), help="Output file for the exported data."
)
@click.pass_context
def export_view(ctx, viewname, file_format, dest):
    """Export the given database view in the specified format.

    Valid file formats are:

    - csv
    - json
    - yaml
    - xlsx
    - dbf
    """
    export_in = {
        "csv": lambda _: _.export("csv"),
        "json": lambda _: _.export("json"),
        "yaml": lambda _: _.export("yaml"),
    }

    res = ctx.obj.select_all(table_name=viewname)
    if dest is None and file_format in export_in:
        click.echo(export_in[file_format](res))
    elif file_format in export_in:
        dest.write(bytes(export_in[file_format](res), "utf8"))
        dest.close()
        click.echo("Created file: " + dest.name)
    elif file_format == "xlsx":
        ctx.obj.export_worksheet(filename=dest, viewname=viewname, rows=res)
        click.echo("Created file: " + dest.name)
    elif file_format == "dbf":
        dest.write(bytes(res.export("dbf")))
        dest.close()
        click.echo("Created file: " + dest.name)
    else:
        click.echo(res)


@cli.command()
@click.argument(
    "table-type", required=True, type=click.Choice(["table", "view", "all"])
)
@click.pass_context
def list_def(ctx, table_type):
    """List all tables or list all views in the database."""
    if table_type == "all":
        res = ctx.obj.ls_entities()
    else:
        res = ctx.obj.ls_entities(entity_type=table_type)
    click.echo(res) if res else click.echo("Not found any " + table_type)


@cli.command()
@click.option(
    "-o",
    "dest",
    type=click.File("w"),
    help="Output file for dumped database in SQL format.",
)
@click.pass_context
def dump(ctx, dest):
    """Dump the entire database in SQL format. If a valid path is given write content to file."""
    res = ctx.obj.dump_database()
    if dest is None:
        click.echo(res.getvalue())
    else:
        dest.write(res.getvalue())
        dest.close()
        click.echo("Dumped database in " + dest.name)
