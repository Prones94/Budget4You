from webbrowser import get
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from forms import BudgetForm, TransactionForm, GoalForm
from datetime import datetime
import os
import pandas as pd
import sqlite3
import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid import ApiClient, configuration
import json
from dotenv import load_dotenv

load_dotenv()

# Plaid configuration
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = ('PLAID_ENV','sandbox')

configuration = plaid.Configuration(
  host=plaid.Environment.Sandbox,
  api_key={
    'clientId':PLAID_CLIENT_ID,
    'secret':PLAID_SECRET,
  }
)
api_client = plaid.ApiClient(configuration)
client=plaid_api.PlaidApi(api_client)


def init_db():
  conn = sqlite3.connect('database.db')
  cursor = conn.cursor()

  with open('schema.sql','r') as f:
    cursor.executescript(f.read())

  conn.commit()
  conn.close()

def get_db_connection():
  conn = sqlite3.connect('database.db')
  conn.row_factory = sqlite3.Row
  return conn

app = Flask(__name__)
app.secret_key = '@$hKetchum12'
app.config['WTF_CSRF_SECRET_KEY'] = 'financekey123'

##### PLAID ROUTES #####
@app.route('/index')
def index():
  """Render the main page with Plaid Link"""
  return render_template('plaid_link.html')

@app.route('/link_account')
def link_account():
  """Render the Plaid Link page"""
  if 'user_id' not in session:
    return redirect(url_for('login'))
  try:
    request_data = LinkTokenCreateRequest(
      user = {
        "client_user_id": str(session.get('user_id')),
      },
      client_name="Budg3t4You",
      products=[Products.AUTH, Products.TRANSACTIONS],
      country_codes=[CountryCode('US')],
      language='en',
      webhook='https://yourapp.com/webhook'
    )
    response = client.link_token_create(request_data)
    link_token = response['link_token']
    return render_template('plaid_link.html', link_token=link_token)
  except plaid.ApiException as e:
    flash(f"Error generating link token: {e}", "danger")
    return redirect(url_for('dashboard'))

@app.route('/get_access_token', methods=['POST'])
def get_access_token():
  public_token = request.json.get('public_token')
  if not public_token:
    return jsonify({"error": "Public token is required"}), 400
  try:
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    session['access_token'] = access_token
    return jsonify({'access_token': access_token})
  except plaid.ApiException as e:
    error_response = json.loads(e.body)
    return jsonify({'error': error_response['error_message']}), 400

@app.route('/accounts', methods=['GET'])
def get_accounts():
  access_token = session.get('access_token')
  if not access_token:
    return redirect(url_for('index'))
  try:
    response = client.Accounts.get(access_token)
    return jsonify(response)
  except Exception as e:
    return jsonify({'error': str(e)}), 400


@app.route('/exchange_token', methods=['POST'])
def exchange_token():
  """Exchange the public token for an access token"""
  data = request.get_json()
  public_token = data.get('public_token')

  if not public_token:
    return jsonify({"error": "public_token is required"}), 400
  try:
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.Item.public_token.exchange(exchange_request)
    access_token = exchange_response['access_token']
    item_id = exchange_response['item_id']
    session['access_token'] = access_token
    return jsonify({'access_token': access_token, "item_id": item_id})
  except Exception as e:
    return jsonify*({'error': str(e)}), 400

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
  try:
    request = LinkTokenCreateRequest(
      products=[Products['transactions']],
      client_name="Budg3t4You",
      country_codes=[CountryCode.US],
      language='en',
      user={
        "client_user_id":str(session.get['user_id'])
      }
    )
    response = client.link_token_create(request)
    return jsonify(response.to_dict())
  except plaid.ApiException as e:
    return jsonify({"error":str(e)})

@app.route('/api/exchange_public_token', methods=['POST'])
def exchange_public_token():
  public_token = request.json.get('public_token')
  try:
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    session['access_token'] = access_token
    return jsonify({"access_token":access_token})
  except plaid.ApiException as e:
    return jsonify({"error": str(e)})

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
  access_token = session.get('access_token')
  if not access_token:
    return jsonify({"error": "Access token not found"}), 400

  try:
    response = client.transactions_get({
      'access_token': access_token,
      'start_date': '2023-01-01',
      'end_date': '2023-12-31'
    })
    return jsonify (response.to_dict())
  except plaid.ApiException as e:
    return jsonify({"error": str(e)})

##### INVOICE ROUTES #####
def process_bank_statement(filepath):
  """Parse and process the uploaded bank statement"""
  try:
    # Load file based on extension
    if filepath.endswith('.csv'):
      df = pd.read_csv(filepath) # Reads CSV file
    elif filepath.endswith('xslx'):
      df = pd.read_excel(filepath) # Reads Excel file
    else:
      raise ValueError("Unsupported file format")

    # Process each row in the file
    for index, row in df.iterrows():
      # Replace 'Amount', 'Date', "Description" with actual column names in file
      amount = row.get('Amount')
      date = row.get('Date')
      description = row.get('Description')

      # Convert date to the required format if necessary
      date = pd.to_datetime(date).strftime('%Y-%m-%d')

      # Save transaction to the database
      conn = get_db_connection()
      cursor = conn.cursor()
      cursor.execute(
        "INSERT INTO BudgetTransactions (amount, date, description) VALUES (?, ?, ?)",
        (amount, date, description)
      )
      conn.commit()
      conn.close()
    print("Bank statement processed successfully!")
  except Exception as e:
    print(f"Error processing bank statement: {e}")

def allowed_file(filename):
  """Check if the uploaded file has an allowed extension"""
  allowed_extensions = {'csv', 'xlsx'} # Ability to add other extensions if needed
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/upload_statement', methods=['GET','POST'])
def upload_statement():
  if request.method == 'POST':
    # Check if file is present
    if 'file' not in request.files:
      flash('No file uploaded', 'danger')
      return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
      flash('No selected file', 'danger')
      return redirect(request.url)

    # Validate the file
    if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      filepath = os.path.join('uploads', filename)
      file.save(filepath)

      # Process the file
      process_bank_statement(filepath)

      flash('Bank statement uploaded successfully', 'success')
      return redirect(url_for('dashboard'))
      
  return render_template('upload_statement.html')

##### USER ROUTES ######
@app.route('/')
def home():
  """Home Page - Dashboard"""
  if 'user_id' not in session:
    return redirect(url_for('login'))
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
            flash("Invalid username or password.", "danger")
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

      flash("Registration successful!", "success")
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

  try:
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
    elif request.method == 'POST':
      flash("Please correct the form errors.", "danger")
  except sqlite3.Error as e:
    conn.rollback()
    flash(f"An error occurred while adding the budget: {e}", "danger")
  finally:
    budgets = cursor.execute("SELECT * FROM Budgets WHERE user_id = ?", (session['user_id'],)).fetchall()
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
    if 'user_id' not in session:
        return redirect(url_for('login'))

    form = TransactionForm()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
        budget = cursor.fetchone()

        if not budget:
            flash("Budget not found or access denied", "danger")
            return redirect(url_for('budget'))

        if form.validate_on_submit():
            amount = float(form.amount.data)
            date = form.date.data
            description = form.description.data

            cursor.execute(
                "INSERT INTO BudgetTransactions (budget_id, amount, date, description) VALUES (?, ?, ?, ?)",
                (budget_id, amount, date, description)
            )

            cursor.execute(
                "UPDATE Budgets SET amount_spent = amount_spent + ? WHERE id = ?",
                (amount, budget_id)
            )

            conn.commit()
            flash("Transaction added successfully!", "success")
            return redirect(url_for('view_transactions', budget_id=budget_id))
    except sqlite3.Error as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "danger")
    finally:
        conn.close()

    return render_template('add_transaction.html', form=form, budget=budget)


@app.route('/budget/<int:budget_id>/transactions', methods=['GET', 'POST'])
def view_transactions(budget_id):
  """View transactions for a specific budget"""
  if 'user_id' not in session:
      return redirect(url_for('login'))

  page = int(request.args.get('page', 1))
  per_page = 10

  conn = get_db_connection()
  cursor = conn.cursor()

  cursor.execute("SELECT * FROM Budgets WHERE id = ? AND user_id = ?", (budget_id, session['user_id']))
  budget = cursor.fetchone()

  if not budget:
      conn.close()
      flash("Budget not found or access denied", "danger")
      return "Budget not found or access denied.", 404

  base_query = "SELECT * FROM BudgetTransactions WHERE budget_id = ?"
  params = [budget_id]

  category = request.args.get('category')
  description = request.args.get('description')
  start_date = request.args.get('start_date')
  end_date = request.args.get('end_date')
  sort_by = request.args.get('sort_by', 'date')
  order = request.args.get('order', 'asc')

  base_query = "SELECT * FROM BudgetTransactions WHERE budget_id = ?"
  params = [budget_id]

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

  order_by_clause = f"ORDER BY {sort_by} {order.upper()}"
  base_query = f"{base_query} {order_by_clause}"

  offset = (page - 1) * per_page
  paginated_query = f"{base_query} LIMIT ? OFFSET ?"
  params.extend([per_page, offset])

  cursor.execute(paginated_query, params)
  transactions = cursor.fetchall()

  total_count = cursor.execute(f"SELECT COUNT(*) FROM ({base_query})", params[:-2]).fetchone()[0]
  total_pages = (total_count + per_page - 1)
  conn.close()

  return render_template(
      'view_transactions.html',
      budget=budget,
      transactions=transactions,
      current_page=page,
      total_pages=total_pages,
      category=category,
      description=description,
      start_date=start_date,
      end_date=end_date,
      sort_by=sort_by,
      order=order
  )

@app.route('/budget/<int:budget_id>/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(budget_id, transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM BudgetTransactions WHERE id = ? AND budget_id = ?",
            (transaction_id, budget_id)
        )
        transaction = cursor.fetchone()

        if not transaction:
            flash("Transaction not found or access denied", "danger")
            return redirect(url_for('view_transactions', budget_id=budget_id))

        if request.method == 'POST':
            new_amount = float(request.form['amount'])
            amount_difference = new_amount - transaction['amount']

            cursor.execute(
                "UPDATE BudgetTransactions SET amount = ?, date = ?, description = ? WHERE id = ? AND budget_id = ?",
                (new_amount, request.form['date'], request.form['description'], transaction_id, budget_id)
            )

            cursor.execute(
                "UPDATE Budgets SET amount_spent = amount_spent + ? WHERE id = ?",
                (amount_difference, budget_id)
            )

            conn.commit()
            flash("Transaction updated successfully!", "success")
            return redirect(url_for('view_transactions', budget_id=budget_id))
    except sqlite3.Error as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "danger")
    finally:
        conn.close()

    return render_template('edit_transaction.html', transaction=transaction)


@app.route('/budget/<int:budget_id>/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(budget_id, transaction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM BudgetTransactions WHERE id = ? AND budget_id = ?", (transaction_id, budget_id))
        transaction = cursor.fetchone()

        if not transaction:
            flash("Transaction not found or access denied", "danger")
            return redirect(url_for('view_transactions', budget_id=budget_id))

        cursor.execute(
            "UPDATE Budgets SET amount_spent = amount_spent - ? WHERE id = ?",
            (transaction['amount'], budget_id)
        )

        cursor.execute("DELETE FROM BudgetTransactions WHERE id = ?", (transaction_id,))
        conn.commit()
        flash("Transaction deleted successfully!", "success")
    except sqlite3.Error as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for('view_transactions', budget_id=budget_id))



@app.route('/budget/<int:budget_id>/transaction/<int:transaction_id>')
def transaction_detail(budget_id, transaction_id):
  """View detailed information for a specific transaction"""
  if 'user_id' not in session:
    return redirect(url_for('login'))
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
    "SELECT * FROM BudgetTransactions WHERE id = ? AND budget_id = ?",
    (transaction_id, budget_id)
  )
  transaction = cursor.fetchone()
  conn.close()

  if not transaction:
    flash("Transaction not found or access denied", "danger")
    return redirect(url_for('view_transactions', budget_id=budget_id))
  return render_template('transaction_detail.html', transaction=transaction)


##### DASHBOARD ROUTES #####
@app.route('/dashboard')
def dashboard():
  """Render user dashboard"""
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

  cursor.execute("SELECT * FROM Budgets WHERE user_id = ?", (session['user_id'],))
  budgets = cursor.fetchall()

  cursor.execute("SELECT * FROM Goals WHERE user_id = ?", (session['user_id'],))
  goals = cursor.fetchall()
  goal_names = [goal['goal_name'] for goal in goals]
  current_amounts = [goal['current_amount'] for goal in goals]
  target_amounts = [goal['target_amount'] for goal in goals]

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
  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    if form.validate_on_submit():
      goal_name = form.goal_name.data
      target_amount = float(form.target_amount.data)
      user_id = session['user_id']

      cursor.execute("INSERT INTO Goals (user_id, goal_name, target_amount, current_amount) VALUES (?,?,?,?)", (user_id, goal_name, target_amount, 0))

      conn.commit()
      flash("Goal added successfully!", "success")
      return redirect(url_for('view_goals'))
    elif request.method == 'POST':
      flash("Please correct the form errors", "danger")
  except sqlite3.Error as e:
    conn.rollback()
    flash(f"An error occurred while setting the goal: {e}", "danger")
  finally:
    conn.close()

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


