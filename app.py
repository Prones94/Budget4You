from webbrowser import get
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from forms import BudgetForm, TransactionForm, GoalForm
from datetime import datetime

def init_db():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  with open('schema.sql','r') as f:
    cursor.executescript(f.read())

  conn.commit()
  conn.close()
  print("Database initialized successfully")

def get_db_connection():
  conn = sqlite3.connect('database.db')
  conn.row_factory = sqlite3.Row
  return conn

app = Flask(__name__)
app.secret_key = '@$hKetchum12'
app.config['WTF_CSRF_SECRET_KEY'] = 'financekey123'

##### USER ROUTES ######
@app.route('/')
def home():
  """Home Page - Dashboard"""
  if 'user_id' not in session:
    return redirect(url_for('home.html'))
  return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route for users to be able to log into their account"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Username and password are required.", 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            return "Invalid username or password."
    return render_template('login.html')


@app.route('/logout')
def logout():
  """Logouts user"""
  session.clear()
  return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
  """Route to register a new user"""
  if request.method == 'POST':
      username = request.form.get('username')
      email = request.form.get('email')
      password = request.form.get('password')

      if not username or not email or not password:
          return "All fields are required.", 400

      password_hash = generate_password_hash(password, method='pbkdf2:sha256')

      conn = get_db_connection()
      cursor = conn.cursor()

      cursor.execute("SELECT * FROM Users WHERE username = ? OR email = ?", (username, email))
      existing_user = cursor.fetchone()

      if existing_user:
          conn.close()
          return "Username or email already exists."

      cursor.execute(
          "INSERT INTO Users (username, password_hash, email) VALUES (?, ?, ?)",
          (username, password_hash, email)
      )
      conn.commit()
      conn.close()

      return redirect(url_for('login'))
  return render_template('register.html')

##### BUDGET ROUTES #####
@app.route('/budget', methods=['GET', 'POST'])
def budget():
  """Route to view and add budgets"""
  if 'user_id' not in session:
      return redirect(url_for('login'))

  form = BudgetForm()
  conn = get_db_connection()
  cursor = conn.cursor()

  if form.validate_on_submit():
    category = form.category.data
    limit_amount = float(form.limit_amount.data)
    user_id = session['user_id']
    cursor.execute(
        "INSERT INTO Budgets (user_id, category, limit_amount, amount_spent) VALUES (?, ?, ?, ?)",
        (user_id, category, limit_amount, 0.00)
    )
    conn.commit()
    flash("Budget added successfully!", "success")
    return redirect(url_for('budget'))

  user_id = session['user_id']
  cursor.execute("SELECT * FROM Budgets WHERE user_id = ?", (user_id,))
  budgets = cursor.fetchall()
  conn.close()

  return render_template('budget.html', budgets=budgets, form=form)


@app.route('/budget/edit/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
    conn.close()
    return "Budget not found or access denied", 400

  if request.method == 'POST':
    category = request.form.get('category')
    limit_amount = float(request.form.get('limit_amount'))

    cursor.execute(
      "UPDATE Budgets SET category = ?, limit_amount = ? WHERE id = ? AND user_id = ?", (category, limit_amount, budget_id, session['user_id'])
    )
    conn.commit()
    conn.close()

    return redirect(url_for('budget'))
  conn.close()
  return render_template('edit_budget.html', budget=budget)

@app.route('/budget/delete/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
  """Delete a budget by ID"""
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("DELETE FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  conn.commit()
  conn.close()

  flash("Budget deleted successfully!", "info")
  return redirect(url_for('budget'))

##### TRANSACTIONS ROUTES #####
@app.route('/budget/<int:budget_id>/add_transaction', methods=['GET', 'POST'])
def add_transaction(budget_id):
  """Add a transaction to a budget"""
  if 'user_id' not in session:
    return redirect(url_for('login'))

  form = TransactionForm()
  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
    conn.close()
    return "Budget not found or access denied", 404

  if form.validate_on_submit():
    amount = float(form.amount.data)
    date = form.date.data
    description = form.description.data

    cursor.execute(
      "INSERT INTO BudgetTransactions (budget_id, amount, date, description) VALUES (?,?,?,?)",
      (budget_id, amount,date, description)
    )
    conn.commit()
    conn.close()

    flash("Transaction added successfully!", "success")
    return redirect(url_for('view_transactions', budget_id=budget_id))

  conn.close()
  return render_template('add_transaction.html', budget=budget, form=form)

@app.route('/budget/<int:budget_id>/transactions', methods=['GET', 'POST'])
def view_transactions(budget_id):
  """View transactions for a specific budget"""
  if 'user_id' not in session:
      return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
      conn.close()
      print("Current session user_id:", session.get('user_id'))

      print("Debug: Budget not found or user access denied.")
      return "Budget not found or access denied.", 404

  base_query = "SELECT * FROM BudgetTransactions WHERE budget_id = ?"
  params = [budget_id]

  category = request.args.get('category')
  description = request.args.get('description')
  start_date = request.args.get('start_date')
  end_date = request.args.get('end_date')

  if category:
      base_query += " AND category = ?"
      params.append(category)

  if description:
      base_query += " AND description LIKE ?"
      params.append(f"%{description}%")

  if start_date:
      base_query += " AND date >= ?"
      params.append(start_date)

  if end_date:
      base_query += " AND date <= ?"
      params.append(end_date)

  cursor.execute(base_query, params)
  transactions = cursor.fetchall()
  conn.close()

  return render_template(
      'view_transactions.html',
      budget=budget,
      transactions=transactions,
      category=category,
      description=description,
      start_date=start_date,
      end_date=end_date
  )

@app.route('/budget/<int:budget_id>/edit_transaction/<int:transaction_id>', methods=['GET','POST'])
def edit_transaction(budget_id, transaction_id):
  """Edit an existing transaction"""
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute(
    """
    SELECT * FROM BudgetTransactions
    WHERE id = ? AND budget_id = ?
    """, (transaction_id, budget_id)
  )
  transaction = cursor.fetchone()

  if not transaction:
    conn.close()
    flash("Transaction not found or access denied", "danger")
    return redirect(url_for('view_transactions', budget_id=budget_id))

  if request.method == 'POST':
    amount = float(request.form['amount'])
    date = request.form['date']
    description = request.form['description']

    cursor.execute(
      """
      UPDATE Budget Transactions
      SET amount = ?, date = ?, description = ?
      WHERE id = ? AND budget_id = ?
      """, (amount, date, description, transaction_id, budget_id)
    )
    conn.commit()
    conn.close()

    flash("Transaction updated successfully", "success")
    return redirect(url_for('view_transactions', budget_id=budget_id))
  conn.close()
  return render_template('edit_transaction.html', transaction=transaction)

@app.route('/budget/<int:budget_id>/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(budget_id, transaction_id):
  """Delete an existing transaction"""
  if 'user_id' not in session:
      return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM BudgetTransactions WHERE id = ? AND budget_id = ?", (transaction_id, budget_id))
  transaction = cursor.fetchone()

  if not transaction:
      conn.close()
      flash("Transaction not found or access denied", "danger")
      return redirect(url_for('view_transactions', budget_id=budget_id))

  cursor.execute("DELETE FROM BudgetTransactions WHERE id = ?", (transaction_id,))
  conn.commit()
  conn.close()

  flash("Transaction deleted successfully", "success")
  return redirect(url_for('view_transactions', budget_id=budget_id))


##### DASHBOARD ROUTES #####
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(limit_amount), 0) AS total_limit,
               COALESCE(SUM(amount_spent), 0) AS total_spent
        FROM Budgets
        WHERE user_id = ?
    """, (session['user_id'],))
    summary = cursor.fetchone()
    total_limit = summary['total_limit'] if summary else 0
    total_spent = summary['total_spent'] if summary else 0
    total_remaining = total_limit - total_spent

    print("Total Limit:", total_limit)
    print("Total Spent:", total_spent)
    print("Total Remaining", total_remaining)

    cursor.execute("""
        SELECT B.category, COALESCE(SUM(T.amount), 0) AS total_spent
        FROM Budgets AS B
        LEFT JOIN BudgetTransactions AS T ON B.id = T.budget_id
        WHERE B.user_id = ?
        GROUP BY B.category
    """, (session['user_id'],))
    category_data = cursor.fetchall()
    labels = [row['category'] for row in category_data]
    values = [row['total_spent'] for row in category_data]

    print("Caegory Data:", [dict(row) for row in category_data])

    cursor.execute("""
        SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total_spent
        FROM BudgetTransactions
        WHERE budget_id IN (SELECT id FROM Budgets WHERE user_id = ?)
        GROUP BY month
        ORDER BY month
    """, (session['user_id'],))
    monthly_spending = cursor.fetchall()
    months = [row['month'] for row in monthly_spending]
    spending_values = [row['total_spent'] for row in monthly_spending]

    print("Monthly Spending:", [dict(row) for row in monthly_spending])

    cursor.execute("""
        SELECT B.category, B.limit_amount AS budgeted, COALESCE(SUM(T.amount), 0) AS actual_spent
        FROM Budgets AS B
        LEFT JOIN BudgetTransactions AS T ON B.id = T.budget_id
        WHERE B.user_id = ?
        GROUP BY B.category
    """, (session['user_id'],))
    budget_vs_actual = cursor.fetchall()
    categories = [row['category'] for row in budget_vs_actual]
    budgeted_values = [row['budgeted'] for row in budget_vs_actual]
    actual_spent_values = [row['actual_spent'] for row in budget_vs_actual]

    print("Budget vs Actual", [dict(row) for row in budget_vs_actual])

    cursor.execute("SELECT * FROM Budgets WHERE user_id = ?", (session['user_id'],))
    budgets = cursor.fetchall()

    print("Budgets:", [dict(row) for row in budgets])

    cursor.execute("SELECT * FROM Goals WHERE user_id = ?", (session['user_id'],))
    goals = cursor.fetchall()
    goal_names = [goal['goal_name'] for goal in goals]
    current_amounts = [goal['current_amount'] for goal in goals]
    target_amounts = [goal['target_amount'] for goal in goals]

    print("Goals:", [dict(row) for row in goals])

    conn.close()

    return render_template(
        'dashboard.html',
        username=session.get('username', 'User'),
        labels=labels,
        values=values,
        total_limit=total_limit,
        total_spent=total_spent,
        total_remaining=total_remaining,
        budgets=budgets,
        goals=goals,
        goal_names=goal_names,
        current_amounts=current_amounts,
        target_amounts=target_amounts,
        months=months,
        spending_values=spending_values,
        categories=categories,
        budgeted_values=budgeted_values,
        actual_spent_values=actual_spent_values
    )

##### GOALS ROUTES #####
@app.route('/goals')
def view_goals():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM Goals WHERE user_id = ?", (session['user_id'],))
  goals = cursor.fetchall()
  conn.close()

  return render_template('goals.html', goals=goals)

@app.route('/goals/add', methods=['GET', 'POST'])
def add_goal():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  form = GoalForm()
  if form.validate_on_submit():
    goal_name = form.goal_name.data
    target_amount = float(form.target_amount.data)
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Goals (user_id, goal_name, target_amount, current_amount) VALUES (?,?,?,?)", (user_id, goal_name, target_amount, 0))

    conn.commit()
    conn.close()

    flash("Goal added successfully!", "success")
    return redirect(url_for('view_goals'))

  return render_template('add_goal.html', form=form)

@app.route('/goals/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Goals WHERE id = ? AND user_id = ?", (goal_id, session['user_id']))
  goal = cursor.fetchone()

  if not goal:
    conn.close()
    flash("Goal not found or access denied", "danger")
    return redirect(url_for('view_goals'))

  cursor.execute("DELETE FROM Goals WHERE id = ? AND user_id = ?", (goal_id, session['user_id']))
  conn.commit()
  conn.close()

  flash("Goal deleted successfully", "success")
  return redirect(url_for('view_goals'))

@app.route('/goals/add_funds/<int:goal_id>', methods=['GET','POST'])
def add_funds(goal_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Goals WHERE id = ? AND user_id = ?", (goal_id, session['user_id']))
  goal = cursor.fetchone()

  if not goal:
    conn.close()
    flash("Goal not found or access denied." , "danger")
    return redirect(url_for('view_goals'))

  if request.method == 'POST':
    try:
      amount_to_add = float(request.form['amount'])
    except ValueError:
      flash("Invalid amount entered", "danger")
      return redirect(url_for('add_funds', goal_id=goal_id))

    new_amount = goal['current_amount'] + amount_to_add
    cursor.execute("UPDATE Goals SET current_amount = ? WHERE id = ?", (new_amount, goal_id))
    conn.commit()
    conn.close()

    flash("Funds added successfully", "success")
    return redirect(url_for('dashboard'))
  conn.close()
  return render_template('add_funds.html', goal=goal)

@app.route('/goals/edit/<int:goal_id>', methods=['GET','POST'])
def edit_goal(goal_id):
  """Edit an existing goal"""
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute(
    """
    SELECT * FROM Goals
    WHERE id = ? AND user_id = ?
    """, (goal_id, session['user_id'])
  )
  goal = cursor.fetchone()

  if not goal:
    conn.close()
    flash("Goal not found or access denied", "danger")
    return redirect(url_for('view_goals'))

  form = GoalForm(data={'goal_name':goal['goal_name'], 'target_amount': goal['target_amount']})

  if form.validate_on_submit():
    goal_name = form.goal_name.data
    target_amount = float(form.target_amount.data)

    cursor.execute(
      """
      UPDATE Goals SET goal_name = ?,
      target_amount = ? WHERE id = ? AND user_id = ?
      """, (goal_name, target_amount, goal_id, session['user_id'])
    )
    conn.commit()
    conn.close()

    flash("Goal updated successfully", "success")
    return redirect(url_for('view_goals'))

  conn.close()
  return render_template('edit_goal.html', form=form, goal_id=goal_id)

if __name__ == '__main__':
  init_db()
  app.run(debug=True)


