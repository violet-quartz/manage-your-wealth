class Expense:
    def __init__(self, project_id, expense_date, start_date, end_date, expense_type, amount, unit, details):
        self.project_id = project_id
        self.date = expense_date
        self.start_date = start_date
        self.end_date = end_date
        self.type = expense_type
        self.amount = amount
        self.unit = unit
        self.details = details

        