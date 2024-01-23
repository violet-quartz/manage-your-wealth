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
        'C:\\Mine\\github\\manage-your-wealth\\instance\\app.sqlite',
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    # res = db.execute(
    #     'SELECT p.id, p.name, p.details, amount, unit FROM expense LEFT OUTER JOIN '
    #     '(SELECT id, name, details FROM project WHERE user_id=2 AND end_date>="2024-01-03") AS p '
    #     'ON expense.project_id = p.id'
    # ).fetchall()
    res = db.execute(
        'SELECT p.id, p.name, p.details, IFNULL(total_income, 0) - IFNULL(total_expense, 0) AS balance, '
        'IFNULL(IFNULL(i.unit, e.unit), "") AS unit FROM '
        '(SELECT id, name, details FROM project WHERE user_id=2 AND end_date>="2024-01-03") AS p '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_expense, unit FROM expense GROUP BY project_id, unit) AS e '
        'ON e.project_id = p.id '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_income, unit FROM income GROUP BY project_id, unit) AS i '
        'ON i.project_id = p.id '
        'WHERE e.unit = i.unit OR e.unit IS NULL OR i.unit IS NULL'
    ).fetchall()
    for row in res:
        for k in row.keys():
            print(f'{k} = {row[k]}', end=',')
        print()

    res = db.execute('SELECT project_id, SUM(amount) AS total, unit FROM income GROUP BY project_id, unit').fetchall()
    for row in res:
        for k in row.keys():
            print(f'{k} = {row[k]}', end=',')
        print()

    print()
    res = db.execute(
        'SELECT type, IFNULL(SUM(amount), 0) AS amount, IFNULL(unit, "") AS unit '
        'FROM expense WHERE project_id = 5 GROUP BY type, unit').fetchall()
    for row in res:
        for k in row.keys():
            print(f'{k} = {row[k]}', end=',')
        print()

    print()
    res = db.execute(
        'SELECT * '
        'FROM project').fetchall()
    for row in res:
        for k in row.keys():
            print(f'{k} = {row[k]}', end=',')
        print()

    print()
    res = db.execute(
        'SELECT id, name, type, invest_date, investment.amount, investment.unit, details, '
        'IFNULL(it.amount, "") AS latest_amount, '
        'IFNULL(it.unit, "") AS latest_unit FROM investment LEFT OUTER JOIN '
        '(SELECT investment_id, amount, unit, date FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY investment_id ORDER BY date DESC) AS rn '
        'FROM investment_track) AS temp WHERE rn = 1) AS it '
        'ON investment.id = it.investment_id WHERE user_id = 1 AND status = "ongoing" ').fetchall()
    for row in res:
        for k in row.keys():
            print(f'{k} = {row[k]}', end=',')
        print()
    


