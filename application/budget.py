from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from application.auth import login_required
from application.db import get_db
from datetime import datetime

bp = Blueprint('budget', __name__, url_prefix='/budget')

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
        budget_type = request.form['budget_type']
        amount = request.form['amount']
        currency = request.form['currency']
        details = request.form['details']
        project_id = request.form['project']
        res = db.execute(
            'SELECT * FROM budget WHERE user_id = ? AND project_id = ? AND type = ?',
            (g.user['id'], project_id, budget_type)
        ).fetchone()
        if res:
            flash(f'Budget {budget_type} has been set. Do you want to update it?')
            return redirect(url_for('account.budget.update', project_id=project_id, budget_type=budget_type))
        db.execute(
            'INSERT INTO budget (user_id, project_id, type, amount, unit, details)'
            ' VALUES(?, ?, ?, ?, ?, ?)',
            (g.user['id'], project_id, budget_type, amount, currency, details)
        )
        db.commit()
        return redirect(url_for('account.index'))
    return render_template('account/create_budget.html', projects=projects)

@bp.route('/update/<project_id>/<budget_type>', methods=['GET', 'POST'])
@login_required
def update(project_id, budget_type):
    db = get_db()
    budget = db.execute(
        'SELECT * FROM budget WHERE project_id = ? AND type = ?',
        (project_id, budget_type)
        ).fetchone()
    
    if request.method == 'POST':
        amount = request.form['amount']
        currency = request.form['currency']
        details = request.form['details']
        db.execute(
            'UPDATE budget SET amount = ?, unit = ?, details = ? WHERE user_id = ? AND project_id = ? AND type = ?',
            (amount, currency, details, g.user['id'], project_id, budget_type)
        )
        db.commit()
        return redirect(url_for('account.index'))
    return render_template('account/update_budget.html', budget=budget)
