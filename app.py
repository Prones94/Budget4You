from flask import Flask, render_template, request, redirect, url_for
import sqlite3

def init_db():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  with open('schema.sql','r') as f:
    cursor.executescript(f.read())

  conn.commit()
  conn.close()

app = Flask(__name__)

# Sample data tp simulate budgets
budgets = [
  {"category": "Groceries", "limit_amount": 300.00, "amount_spent": 120.50},
  {"category": "Rent", "limit_amount": 1000.00, "amount_spent": 1000.00}
]

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
  if request.method == 'POST':
    category = request.form['category']
    limit_amount = float(request.form['limit_amount'])

    budgets.append({
      "category": category,
      "limit_amount": limit_amount,
      "amount_spent": 0.00
    })

    return redirect(url_for('budget'))
  return render_template('budget.html',budgets=budgets)


if __name__ == '__main__':
  init_db()
  app.run(debug=True)


