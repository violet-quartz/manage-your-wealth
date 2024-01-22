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
    # list account balance
    balance = db.execute(
        'SELECT * FROM balance WHERE user_id = ?',
        (g.user['id'],)
        ).fetchall()
    # list recent 3 earnings
    earnings = db.execute(
        'SELECT * FROM income WHERE user_id = ? ORDER BY date DESC LIMIT ?',
        (g.user['id'], 3)
        ).fetchall()
    # list recent 5 expenses
    expenses = db.execute(
        'SELECT * FROM expense WHERE user_id = ? ORDER BY date DESC LIMIT ?',
        (g.user['id'], 5)
        ).fetchall()
    # list savings 
    saving = db.execute(
        'SELECT SUM(amount) AS amount, unit FROM saving_account WHERE user_id = ?',
        (g.user['id'],)
        ).fetchall()
    
    today = datetime.now().date()
    # list ongoing projects    
    projects = db.execute(
        'SELECT * FROM project WHERE user_id = ? AND end_date >= ?',
        (g.user['id'], today)
        ).fetchall()

    # list ongoing investments
    investments = db.execute(
        'SELECT * FROM investment WHERE user_id = ? AND status = "ongoing" ',
        (g.user['id'],)
        ).fetchall()
    # list ongoing saving plans
    saving_plans = db.execute(
        'SELECT * FROM saving_plan WHERE user_id = ? AND end_date >= ?',
        (g.user['id'], today)
        ).fetchall()
    
    return render_template('account/index.html', 
                           balance=balance, earnings=earnings,
                           expenses=expenses, savings=saving,
                           projects=projects, investments=investments,
                           saving_plans=saving_plans)

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
        db.execute(
            'INSERT INTO investment(user_id, name, type, details, invest_date, amount, unit, status)'
            ' VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
            (g.user['id'], name, investment_type, details, invest_date, amount, currency, "ongoing")
        )
        db.commit()
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





    