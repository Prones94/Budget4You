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
  return render_template('dashboard.html')

@app.route('/login', methods=['GET','POST'])
def login():
  """Route for users to be able to log into their account"""
  if request.method == 'POST':
    return redirect(url_for('home'))
  return render_template('login.html')

@app.route('/logout')
def logout():
  return redirect(url_for('login'))

##### BUDGET ROUTES #####
@app.route('/budget', methods=['GET','POST'])
def budget():
  conn = get_db_connection()
  cursor = conn.cursor()

  if request.method == 'POST':
    category = request.form['category']
    limit_amount = float(request.form['limit_amount'])

    cursor.execute(
      "INSERT INTO Budgets (category, limit_amount, amount_spent) VALUES (?,?,?)",
      (category, limit_amount, 0.00)
    )
    conn.commit()
    return redirect(url_for('budget'))

  budgets = cursor.execute("SELECT * FROM Budgets").fetchall()
  conn.close()
  return render_template('budget.html',budgets=budgets)


if __name__ == '__main__':
  init_db()
  app.run(debug=True)


