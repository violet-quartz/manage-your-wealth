from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from application.auth import login_required
from application.db import get_db
from application.classes import Expense
from datetime import datetime
import logging

bp = Blueprint('account', __name__)
DEFAULT_PROJECT_ENDDATE = '2100-01-01'

@bp.route('/')
def index():
    if g.user is None:
        return render_template('account/index.html')
    db = get_db()
    today = datetime.now().date()
    # list projects
    ongoing_projects = db.execute(
        'SELECT p.id, p.name, p.details, IFNULL(total_income, 0) - IFNULL(total_expense, 0) AS balance, '
        'IFNULL(IFNULL(i.unit, e.unit), "") AS unit FROM '
        '(SELECT id, name, details FROM project WHERE user_id = ? AND end_date >= ?) AS p '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_expense, unit FROM expense GROUP BY project_id, unit) AS e '
        'ON e.project_id = p.id '
        'LEFT OUTER JOIN '
        '(SELECT project_id, SUM(amount) AS total_income, unit FROM income GROUP BY project_id, unit) AS i '
        'ON i.project_id = p.id '
        'WHERE e.unit = i.unit OR e.unit IS NULL OR i.unit IS NULL',        
        (g.user['id'], today)
        ).fetchall()
    
    # list savings 
    saving = db.execute(
        'SELECT IFNULL(SUM(amount), 0) AS amount, IFNULL(unit, "") AS unit FROM saving_account WHERE user_id = ?',
        (g.user['id'],)
        ).fetchall()
    

    # list ongoing investments
    investments = db.execute(
        'SELECT id, name, type, invest_date, investment.amount, investment.unit, details, '
        'IFNULL(it.amount, "") AS latest_amount, '
        'IFNULL(it.unit, "") AS latest_unit FROM investment LEFT OUTER JOIN '
        '(SELECT investment_id, amount, unit, date FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY investment_id ORDER BY date DESC) AS rn '
        'FROM investment_track) AS temp WHERE rn = 1) AS it '
        'ON investment.id = it.investment_id WHERE user_id = ? AND status = "ongoing" ',
        (g.user['id'],)
        ).fetchall()
    
    return render_template('account/index.html', 
                           savings=saving, 
                           projects=ongoing_projects, 
                           investments=investments)

@bp.route('/create/expense', methods=['POST', 'GET'])
@login_required
def create_expense():
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
            return redirect(url_for('account.create_investment', source=source, id=inserted_id))
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

@bp.route('/create/investment', methods=['GET', 'POST'], defaults={'source':None, 'id':None})
@bp.route('/create/investment/<source>/<id>', methods=['GET','POST'])
@login_required
def create_investment(source, id):
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
            'INSERT INTO innvestment_track(investment_id, date, amount, unit) '
            'VALUES(?, ?, ?, ?)',
            (inserted_id, invest_date, amount, currency)
        )
        db.execute()
        return redirect(url_for('account.index'))

    return render_template('account/create_investment.html', item=source_item)

@bp.route('/create/saving', methods=['GET','POST'])
@login_required
def create_saving():
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

@bp.route('/create/project', methods=['POST', 'GET'])
@login_required
def create_project():
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

@bp.route('/create/earning', methods=['GET', 'POST'])
@login_required
def create_earning():
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

@bp.route('/create/budget', methods=['GET', 'POST'])
@login_required
def create_budget():
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
            return redirect(url_for('account.update_budget', project_id=project_id, budget_type=budget_type))
        db.execute(
            'INSERT INTO budget (user_id, project_id, type, amount, unit, details)'
            ' VALUES(?, ?, ?, ?, ?, ?)',
            (g.user['id'], project_id, budget_type, amount, currency, details)
        )
        db.commit()
        return redirect(url_for('account.index'))
    return render_template('account/create_budget.html', projects=projects)

@bp.route('/update/budget/<project_id>/<budget_type>', methods=['GET', 'POST'])
@login_required
def update_budget(project_id, budget_type):
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

@bp.route('/list/project/<id>', methods=['GET', 'POST'])
@login_required
def list_project(id):
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

@bp.route('/list/projects', methods=['GET'])
@login_required
def list_projects():
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

@bp.route('/list/investment/<id>', methods=['GET', 'POST'])
@login_required
def list_investment(id):
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
        return redirect(url_for('account.list_investment', id=id))

    return render_template('account/list_investment.html', investment=investment, tracks=investment_track)




    