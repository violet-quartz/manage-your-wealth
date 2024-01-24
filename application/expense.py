from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from application.auth import login_required
from application.db import get_db
from application.classes import Expense
from datetime import datetime

bp = Blueprint('expense', __name__, url_prefix='/expense')

@bp.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    db = get_db()
    today = datetime.now().date()
    projects = db.execute(
        'SELECT * FROM project WHERE user_id = ? AND end_date >= ?',
        (g.user['id'], today)
        ).fetchall()

    if request.method == 'POST':
        e = Expense(
            project_id=request.form['project'],
            expense_date=request.form['expense_date'],
            start_date=request.form['start_date'],
            end_date=request.form['end_date'],
            expense_type=request.form['expense_type'],
            amount=request.form['amount'],
            unit=request.form['currency'],
            details=request.form['details']
        )
        use_saving = request.form['use_saving']

        # TODO: check required field
        inserted_id = None
        source = 'saving' if use_saving == 'yes' else 'expense'
        if use_saving == 'yes':
            row = db.execute(
                'INSERT INTO saving_account (user_id, date, amount, unit, details)'
                ' VALUES(?, ?, ?, ?, ?) RETURNING id',
                (g.user['id'], e.date, 0 - float(e.amount), e.unit, e.details)
            ).fetchone()
        else:
            row = db.execute(
                'INSERT INTO expense (user_id, project_id, date, start_date, end_date, type, amount, unit, details)'
                ' VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id',
                (g.user['id'], e.project_id, e.date, e.start_date, e.end_date, e.type, e.amount, e.unit, e.details)
            ).fetchone()
        db.commit()
        (inserted_id, ) = row
        message = 'Successfully add new expense.'
        if e.type == 'investment':
            flash(message + 'Please finish investment information.')
            return redirect(url_for('account.investment.create', source=source, id=inserted_id))
        elif e.type == 'saving':
            db.execute(
                'INSERT INTO saving_account (user_id, date, amount, unit, details)'
                ' VALUES(?, ?, ?, ?, ?)',
                (g.user['id'], e.date, e.amount, e.unit, e.details)
            )
            db.commit()
            flash(message + 'And add new saving.')
        else:
            flash(message)
        return redirect(url_for('account.index'))        
        
    return render_template('account/create_expense.html', projects=projects)