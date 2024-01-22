import datetime
import sqlite3

import click
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# > flask --app application init-db
@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

if __name__ == '__main__':
    db = sqlite3.connect(
        'test.sqlite',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    with open('schema.sql') as f:
        db.executescript(f.read())

    db.execute(
        'INSERT INTO user (name, password, email)'
        ' VALUES (?, ?, ?)',
        ('MYF', '123', 'myf.py@163.com')
    )

    db.execute(
        'INSERT INTO project (user_id, name, start_date, end_date, details)'
        ' VALUES (?, ?, ?, ?, ?)',
        (1, '2024-01', datetime.datetime(2024,1,1), datetime.datetime(2024,1,31), '2024-January-life')
    )

    db.execute(
        'INSERT INTO expense (user_id, project_id, start_date, end_date, type, amount, details)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
        (1, 1, None, None, 'food', 34, 'cake')
    )

    db.commit()
    res = db.execute(
        'SELECT * FROM user'
    ).fetchone()
    for k in res.keys():
        print(f'{k} = {res[k]}')


    res = db.execute('SELECT * FROM project').fetchone()
    for k in res.keys():
        print(f'{k} = {res[k]}')

    res = db.execute('SELECT * FROM expense').fetchone()
    for k in res.keys():
        print(f'{k} = {res[k]}')

    db.close()

