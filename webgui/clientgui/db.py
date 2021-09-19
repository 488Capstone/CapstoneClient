#import sqlite3
from capstoneclient.db_manager import DBManager
import click
from flask import current_app, g
from flask.cli import with_appcontext

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


def get_db():
    if 'db' not in g:
        g.db = DBManager()
        g.db.start_databases()
        #g.db = sqlite3.connect(
        #    current_app.config['DATABASE'],
        #    detect_types=sqlite3.PARSE_DECLTYPES
        #)
        #g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = DBManager()
    db.start_databases()
    #DW old code from prototype website
#    db = get_db()
#    with current_app.open_resource('schema.sql') as f:
#        strmsg = f.read()
#        #DW the db init is throwing an error if I have all the other tables. reducing to just user table is working tho
#        #print(strmsg)
#        db.executescript(strmsg.decode('utf8'))

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

