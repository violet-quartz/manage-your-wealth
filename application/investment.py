from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from application.auth import login_required
from application.db import get_db

bp = Blueprint('investment', __name__, url_prefix="/investment")

@bp.route('/create', methods=['GET', 'POST'], defaults={'source':None, 'id':None})
@bp.route('/create/<source>/<id>', methods=['GET','POST'])
@login_required
def create(source, id):
    source_item = None
    if source and id:
        if source == 'expense':        
            source_item = get_expense(id)
        elif source == 'saving':
            source_item = get_saving(id)

    if request.method == 'POST':
        name = request.form['name']
        invest_date = request.form['invest_date']
        investment_type = request.form['investment_type']
        amount = request.form['amount']
        currency = request.form['currency']
        details = request.form['details']

        db = get_db()
        row = db.execute(
            'INSERT INTO investment(user_id, name, type, details, invest_date, amount, unit, status)'
            ' VALUES(?, ?, ?, ?, ?, ?, ?, ?) RETURNING id',
            (g.user['id'], name, investment_type, details, invest_date, amount, currency, "ongoing")
        ).fetchone()
        db.commit()
        (inserted_id,) = row
        db.execute(
            'INSERT INTO investment_track(investment_id, date, amount, unit) '
            'VALUES(?, ?, ?, ?)',
            (inserted_id, invest_date, amount, currency)
        )
        db.commit()
        return redirect(url_for('account.index'))

    return render_template('account/create_investment.html', item=source_item)

@bp.route('/list/<id>', methods=['GET', 'POST'])
@login_required
def list(id):
    db = get_db()
    investment = db.execute(
        'SELECT name, type, details, invest_date, amount, unit, status FROM investment '
        'WHERE id = ?',
        (id,)
    ).fetchone()

    investment_track = db.execute(
        'SELECT date, amount, unit FROM investment_track WHERE investment_id = ?',
        (id, )
    ).fetchall()

    if request.method == 'POST':
        track_date = request.form['track_date']
        amount = request.form['amount']
        currency = request.form['currency']
        db.execute(
            'INSERT INTO investment_track (investment_id, date, amount, unit) '
            'VALUES (?, ?, ?, ?)',
            (id, track_date, amount, currency)
        )
        db.commit()
        return redirect(url_for('account.investment.list', id=id))

    return render_template('account/list_investment.html', investment=investment, tracks=investment_track)

def get_expense(expense_id):
    db = get_db()
    expense = db.execute(
        'SELECT * FROM expense WHERE user_id = ? AND id = ?',
        (g.user['id'], expense_id)).fetchone()    
    if expense is None:
        abort(404, "Expense doesn't exist.")    
    return expense

def get_saving(saving_id):
    db = get_db()
    saving = db.execute(
        'SELECT * FROM saving_account WHERE user_id = ? AND id = ?',
        (g.user['id'], saving_id)).fetchone()
    if saving is None:
        abort(404, "Saving doesn't exist.")
    return saving
