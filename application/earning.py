from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from application.auth import login_required
from application.db import get_db
from datetime import datetime

bp = Blueprint('earning', __name__, url_prefix='/earning')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    db = get_db()
    today = datetime.now().date()
    projects = db.execute(
        'SELECT * FROM project WHERE user_id = ? AND end_date >= ?',
        (g.user['id'], today)
        ).fetchall()
    
    if request.method == 'POST':
        earning_type = request.form['earning_type']
        amount = request.form['amount']
        currency = request.form['currency']
        earning_date = request.form['earning_date']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        details = request.form['details']
        project_id = request.form['project']

        db = get_db()
        db.execute(
            'INSERT INTO income (user_id, project_id, date, start_date, end_date, type, amount, unit, details)'
            ' VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (g.user['id'], project_id, earning_date, start_date, end_date, earning_type, amount, currency, details)
        )
        db.commit()
        return redirect(url_for('account.index'))

    return render_template('account/create_earning.html', projects=projects)

