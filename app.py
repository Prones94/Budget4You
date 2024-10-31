from flask import Flask, render_template, request, redirect, url_for,session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

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
@app.route('/budget', methods=['GET','POST'])
def budget():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  conn = get_db_connection()
  cursor = conn.cursor()

  if request.method == 'POST':
    category = request.form['category']
    limit_amount = float(request.form['limit_amount'])
    user_id = session['user_id']

    cursor.execute(
      "INSERT INTO Budgets (category, limit_amount, amount_spent) VALUES (?,?,?)",
      (category, limit_amount, limit_amount, 0.00)
    )
    conn.commit()

  user_id = session['user_id']
  cursor.execute("SELECT * FROM Budgets WHERE user_id = ?", (user_id,))
  budgets = cursor.execute("SELECT * FROM Budgets").fetchall()
  conn.close()

  return render_template('budget.html',budgets=budgets)

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
    return "Budfget not found or access denied", 400

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

  return redirect(url_for('budget'))


if __name__ == '__main__':
  init_db()
  app.run(debug=True)


