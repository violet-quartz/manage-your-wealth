from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from application.auth import login_required
from application.db import get_db

bp = Blueprint('project', __name__, url_prefix='/project')

DEFAULT_PROJECT_ENDDATE = '2100-01-01'

@bp.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        details = request.form['details']
        error = None

        if not name:
            error = 'Name is required'
        # TODO: display error if name is repeated.
        
        if error is not None:
            flash(error)
        else:
            end_date = end_date if end_date else DEFAULT_PROJECT_ENDDATE
            db = get_db()
            db.execute(
                'INSERT INTO project (user_id, name, start_date, end_date, details)'
                ' VALUES (?, ?, ?, ?, ?)',
                (g.user['id'], name, start_date, end_date, details)
            )
            db.commit()
            return redirect(url_for('account.index'))
    return render_template('account/create_project.html')

@bp.route('/list/<id>', methods=['GET', 'POST'])
@login_required
def list(id):
    db = get_db()
    project = db.execute(
        'SELECT name, start_date, end_date, details FROM project WHERE id = ?',
        (id,)
    ).fetchone()

    if not project:
        abort(404, "Project doesn't exist.") 

    expenses = db.execute(
        'SELECT date, type, amount, unit, details FROM expense WHERE project_id = ?',
        (id,)
    ).fetchall()

    expense_summary = db.execute(
        'SELECT IFNULL(exp.type, b.type) AS type, IFNULL(exp.amount, 0) AS amount, IFNULL(exp.unit, "") AS unit, '
        'IFNULL(b.amount, 0) AS budget_amount, IFNULL(b.unit, "") AS budget_unit, details FROM'
        '(SELECT type, IFNULL(SUM(amount), 0) AS amount, IFNULL(unit, "") AS unit '
        'FROM expense WHERE project_id = ? GROUP BY type, unit) AS exp '
        'FULL OUTER JOIN '
        '(SELECT type, amount, unit, details FROM budget WHERE project_id = ?) AS b '
        'ON exp.type = b.type',
        (id, id)
    ).fetchall()

    earnings = db.execute(
        'SELECT date, type, amount, unit, details FROM income WHERE project_id = ?',
        (id,)
    ).fetchall()

    earning_summary = db.execute(
        'SELECT type, IFNULL(SUM(amount), 0) AS amount, IFNULL(unit, "") AS unit '
        'FROM income WHERE project_id = ? GROUP BY type, unit',
        (id, )
    ).fetchall()

    
    return render_template('account/list_project.html',
                           project=project,
                           expenses=expenses, expense_summary=expense_summary,
                           earnings=earnings, earning_summary=earning_summary)

@bp.route('/list/all', methods=['GET'])
@login_required
def list_all():
    db = get_db()
    projects = db.execute(
        'SELECT p.id, p.name, p.details, p.start_date, p.end_date, IFNULL(total_income, 0) - IFNULL(total_expense, 0) AS balance, '
        'IFNULL(IFNULL(i.unit, e.unit), "") AS unit FROM '
        '(SELECT id, name, details, start_date, end_date FROM project WHERE user_id=? ) AS p '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_expense, unit FROM expense GROUP BY project_id, unit) AS e '
        'ON e.project_id = p.id '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_income, unit FROM income GROUP BY project_id, unit) AS i '
        'ON i.project_id = p.id '
        'WHERE e.unit = i.unit OR e.unit IS NULL OR i.unit IS NULL',        
        (g.user['id'], )
        ).fetchall()
    return render_template('account/list_projects.html', projects=projects)