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
