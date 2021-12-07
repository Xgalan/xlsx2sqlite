# -*- coding: utf-8 -*-
"""Command line interface for xlsx2sqlite API.

Parse the INI file passed as argument for retrieving the options, then
executes the choosen command.
"""
from pathlib import Path

import click

from xlsx2sqlite.import_export import export_worksheet
from xlsx2sqlite.config import Xlsx2sqliteConfig
import xlsx2sqlite.controller as ctrl


pass_config = click.make_pass_decorator(Xlsx2sqliteConfig)


@click.group()
@click.argument('ini', required=True, type=click.Path(exists=True))
@click.pass_context
def cli(ctx, ini):
    """Generate a Sqlite3 database parsing options from a .INI
    configuration file.
    """
    try:
        ctx.obj = Xlsx2sqliteConfig(ini)
    except KeyError as err:        
        click.secho(str(err), bg='red', fg='black')
        raise click.Abort
    # check for warning messages
    [click.secho(msg, bg='yellow', fg='black') for msg in ctx.obj.log]
    click.secho('Parsed the config file.', bg='green', fg='black')


@click.command()
@pass_config
def initialize_db(config):
    """Database creation and initialization.

    Populates the database with data imported from the worksheets.
    """
    controller = ctrl.new_controller(config)
    res = controller.initialize_db()
    click.secho('Finished importing.', bg='green', fg='black')
    [click.echo(msg) for msg in res]
    controller.close_db()


@click.command()
@click.argument(
    'table-name', type=click.STRING
)
@pass_config
def update(config, table_name):
    """Upsert data on a specified table.
    """
    controller = ctrl.new_controller(config)
    if table_name:
        # Replace operation on sqlite database
        if table_name in config.get_tables_names:
            res = controller.insert_or_replace(tablename=table_name)
            click.secho('Finished importing.', bg='green', fg='black')
    [click.echo(msg) for msg in res]
    controller.close_db()


@click.command()
@click.confirmation_option(prompt='Are you sure you want to drop the tables?')
@pass_config
def drop_tables(config):
    """Drop the tables in the database.

    Drop only the tables which have a name corresponding
    to the worksheets specified in the config file.
    """
    controller = ctrl.new_controller(config)
    res = controller.drop_tables(config.get_tables_names)
    [click.echo(msg) for msg in res]
    controller.close_db()


@click.command()
@pass_config
def create_views(config):
    """Create database views.

    Create views on the database loading `*.sql` from the path specified in
    the INI config file. A file must contain a valid `SELECT` query.
    """
    controller = ctrl.new_controller(config)
    p = Path(config.get('sql_views'))
    res = [controller.create_view(viewname=f.stem, select=f.read_text()) for f in list(p.glob('**/*.sql'))]
    [click.echo(msg) for msg in res]
    controller.close_db()


@click.command()
@click.confirmation_option(prompt='Are you sure you want to drop the views?')
@pass_config
def drop_views(config):
    """Drop the views in the database.

    Drop all the views of the database.
    """
    controller = ctrl.new_controller(config)
    p = Path(config.get('sql_views'))
    res = [controller.drop_view(viewname=f.stem) for f in list(p.glob('**/*.sql'))]
    [click.echo(msg) for msg in res]
    controller.close_db()


@click.command()
@click.argument('viewname',
                required=True,
                type=click.STRING)
@click.option('-f', 'file_format', type=click.STRING,
              help='Desired file format for the exported data.')
@click.option('-o', 'dest', type=click.File('wb'),
              help='Output file for the exported data.')
@pass_config
def export_view(config, viewname, file_format, dest):
    """Export the given database view in the specified format.

    Valid file formats are:
    
    - csv
    - json
    - yaml
    - xlsx
    - dbf
    """
    export_in = {'csv': lambda _: _.export('csv'),
                 'json': lambda _: _.export('json'),
                 'yaml': lambda _: _.export('yaml')}

    controller = ctrl.new_controller(config)
    res = controller.select_all(table_name=viewname)
    controller.close_db()
    if dest is None and file_format in export_in:
        click.echo(export_in[file_format](res))
    elif file_format in export_in:
        dest.write(bytes(export_in[file_format](res), 'utf8'))
        dest.close()
        click.echo('Created file: ' + dest.name)
    elif file_format == 'xlsx':
        export_worksheet(filename=dest, ws_name=viewname, rows=res)
        click.echo('Created file: ' + dest.name)
    elif file_format == 'dbf':
        dest.write(bytes(res.export('dbf')))
        dest.close()
        click.echo('Created file: ' + dest.name)
    else:
        click.echo(res)


@click.command()
@click.argument('table-type',
                required=True,
                type=click.Choice(['table', 'view', 'all']))
@pass_config
def list_def(config, table_type):
    """List all tables or list all views in the database.
    """
    controller = ctrl.new_controller(config)
    if table_type == 'all':
        res = controller.ls_entities()
    else:
        res = controller.ls_entities(entity_type=table_type)
    controller.close_db()
    click.echo(res) if res else click.echo('Not found any ' + table_type)


cli.add_command(initialize_db)
cli.add_command(update)
cli.add_command(drop_tables)
cli.add_command(drop_views)
cli.add_command(create_views)
cli.add_command(export_view)
cli.add_command(list_def)
