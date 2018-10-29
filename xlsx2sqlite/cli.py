# -*- coding: utf-8 -*-
"""Command line interface for xlsx2sqlite API.


"""
import click

from .utils import ConfigModel
from .core import Controller


pass_config = click.make_pass_decorator(ConfigModel)


@click.group()
@click.argument('ini', required=True, type=click.Path(exists=True))
@click.pass_context
def cli(ctx, ini):
    """Generate a Sqlite3 database parsing options from a .INI
    configuration file.
    """
    ctx.obj = ConfigModel()
    ctx.obj.import_config(ini)
    click.echo('Parsed the config file.')


@click.command()
@pass_config
def initdb(config):
    """Initialize the sqlite3 database.

    Populates the database with data imported from the worksheets.
    """
    controller.import_tables(workbook=config.get('xlsx_file'),
                             worksheets=config.get_imports()['worksheets'],
                             subset_cols=config.get_imports()['subset_cols'])
    controller.create_db(config.get('db_file'))
    if config._parser.has_section('CONSTRAINTS'):
        controller.set_constraints(dict(config._parser.items('CONSTRAINTS')))
    controller.initialize_db()
    controller.close_db()


@click.command()
@click.argument('table-name',
                default='all',
                type=click.STRING)
@pass_config
def update_data(config, table_name):
    """Upsert of xlsx table on specified database table."""
    controller.import_tables(workbook=config.get('xlsx_file'),
                             worksheets=config.get_imports()['worksheets'],
                             subset_cols=config.get_imports()['subset_cols'])
    controller.create_db(config.get('db_file'))
    # Replace operation on sqlite database
    if table_name in config.get_imports()['worksheets']:
        controller.replace_values(table_name)
        click.echo('Updated table: ' + table_name)
    else:
        controller.update_tables()
        click.echo('Updated all tables.')
    controller.close_db()


@click.command()
@click.confirmation_option(prompt='Are you sure you want to drop the tables?')
@pass_config
def drop_tables(config):
    """Drop the tables in the database.

    Drop only the tables which have a name corresponding
    to the worksheets specified in the config file.
    """
    controller.create_db(config.get('db_file'))
    controller.drop_tables(config.get_imports()['worksheets'])
    controller.close_db()


@click.command()
@pass_config
def create_views(config):
    """Create database views.

    Create views on the database loading '*.sql' from the path specified in
    the INI config file. A file must contain a valid SELECT query.
    """
    from pathlib import Path

    controller.create_db(config.get('db_file'))
    p = Path(config.get('sql_views'))
    [controller.create_view(viewname=f.stem, select=f.read_text())
     for f in list(p.glob('**/*.sql'))]
    controller.close_db()


@click.command()
@click.option('-v', 'viewname',
              required=True,
              type=click.STRING,
              help='Please select a valid database view name.')
@click.option('-f', 'file_format', type=click.STRING,
              help='Desired file format for the exported data.')
@click.option('-o', 'dest', type=click.File('wb'),
              help='Output file for the exported data.')
@pass_config
def export_view(config, viewname, file_format, dest):
    """Export the given database view in the specified format."""

    export_in = {'csv': lambda _: _.export('csv'),
                 'json': lambda _: _.export('json'),
                 'yaml': lambda _: _.export('yaml')}

    controller.create_db(config.get('db_file'))
    res = controller.select_all(table_name=viewname)
    controller.close_db()
    if dest is None and file_format in export_in:
        click.echo(export_in[file_format](res))
    elif file_format in export_in:
        dest.write(bytes(export_in[file_format](res), 'utf8'))
        dest.close()
    else:
        click.echo(res)


@click.command()
@click.argument('table-type',
                required=True,
                type=click.Choice(['table', 'view']))
@pass_config
def list_def(config, table_type):
    """List all tables or list all views in the database."""
    controller.create_db(config.get('db_file'))
    if table_type == 'table':
        res = controller.list_tables()
    else:
        res = controller.list_views()
    controller.close_db()
    click.echo(res)


cli.add_command(initdb)
cli.add_command(update_data)
cli.add_command(drop_tables)
cli.add_command(create_views)
cli.add_command(export_view)
cli.add_command(list_def)
controller = Controller()


if __name__ == "__main__":
    cli()
