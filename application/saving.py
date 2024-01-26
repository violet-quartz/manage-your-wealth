from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from application.auth import login_required
from application.db import get_db

bp = Blueprint('saving', __name__, url_prefix='/saving')

@bp.route('/create', methods=['GET','POST'])
@login_required
def create():
    if request.method == 'POST':
        saving_date = request.form['saving_date']
        amount = request.form['amount']
        currency = request.form['currency']
        details = request.form['details']

        db = get_db()
        db.execute(
            'INSERT INTO saving_account (user_id, date, amount, unit, details)'
            ' VALUES(?, ?, ?, ?, ?)',
            (g.user['id'], saving_date, amount, currency, details)
        )
        db.commit()
        return redirect(url_for('account.index'))

    return render_template('account/create_saving.html')

@bp.route('/list/all', methods=['GET','POST'])
@login_required
def list_all():
    db = get_db()
    savings = db.execute(
        'SELECT s.date, s.amount, s.unit, s.details, s.project_id, p.name AS project_name FROM '
        '(SELECT date, amount, unit, details, project_id FROM saving_account WHERE user_id=?) AS s '
        'LEFT OUTER JOIN project AS p ON s.project_id = p.id',
        (g.user['id'],)
    ).fetchall()
    return render_template('account/list_savings.html', savings=savings)