from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from forms import BudgetForm, TransactionForm

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
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  user_id = session['user_id']
  cursor.execute("SELECT category, limit_amount, amount_spent FROM Budgets WHERE user_id = ?", (user_id, ))
  budgets = cursor.fetchall()
  conn.close()

  total_limit = sum(budget['limit_amount'] for budget in budgets)
  total_spent = sum(budget['amount_spent'] for budget in budgets)
  total_remaining = total_limit - total_spent

  return render_template(
    'dashboard.html',
    username=session['username'],
    budgets=budgets,
    total_limit=total_limit,
    total_spent=total_spent,
    total_remaining=total_remaining
    )

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
  session.clear()
  return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = BudgetForm()
    conn = get_db_connection()
    cursor = conn.cursor()

    if form.validate_on_submit():
      category = form.category.data
      limit_amount = form.limit_amount.data
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

    return render_template('budget.html', budgets=budgets)


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
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("DELETE FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  conn.commit()
  conn.close()

  flash("Budget deleted successfully!", "info")
  return redirect(url_for('budget'))

@app.route('/budget/<int:budget_id>/add_transaction', methods=['GET', 'POST'])
def add_transaction(budget_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
    conn.close()
    return "Budget not found or access denied", 404

  if request.method == 'POST':
    amount = float(request.form.get('amount'))
    date = request.form.get('date')
    description = request.form.get('description')

    cursor.execute(
      "INSERT INTO BudgetTransactions (budget_id, amount, date, description) VALUES (?,?,?,?)",
      (budget_id, amount,date, description)
    )
    conn.commit()
    conn.close()

    flash("Transaction added successfully!", "success")
    return redirect(url_for('view_transactions', budget_id=budget_id))

  conn.close()
  return render_template('add_transaction.html', budget=budget)

@app.route('/budget/<int:budget_id>/transactions')
def view_transactions(budget_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
    conn.close()
    return "Budget not found or access denied", 404

  cursor.execute("SELECT * FROM BudgetTransactions WHERE budget_id = ?", (budget_id,))
  transactions = cursor.fetchall()
  conn.close()

  return render_template('view_transactions.html', budget=budget, transactions=transactions)


if __name__ == '__main__':
  init_db()
  app.run(debug=True)


