from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from application.auth import login_required
from application.db import get_db
from application.classes import Expense
from datetime import datetime

bp = Blueprint('account', __name__, url_prefix='/account')
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
    # TODO: list saving details    

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
