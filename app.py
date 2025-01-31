from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from models import db, User, Budget, Transaction, Goal
from forms import RegistrationForm, BudgetForm, TransactionForm, GoalForm

# Load environment variables
load_dotenv()

# Plaid Environment Variable
PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_ENV = os.getenv('PLAID_ENV', 'sandbox')

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = '@$hKetchum12'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.before_first_request
def create_tables():
    """Ensures all tables are created before first request."""
    db.create_all()

##### USER AUTHENTICATION ROUTES #####
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration Route"""
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            if User.query.filter_by(username=form.username.data).first():
                flash("Username already taken.", "error")
                return redirect(url_for('register'))
            if User.query.filter_by(email=form.email.data).first():
                flash("Email is already registered.", "error")
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error registering user: {e}", "danger")
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Login Route"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User Logout"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

##### BUDGET ROUTES #####
@app.route('/budget', methods=['GET', 'POST'])
def budget():
    """View and Add Budgets"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    form = BudgetForm()
    if form.validate_on_submit():
        try:
            new_budget = Budget(category=form.category.data, limit_amount=form.limit_amount.data, user_id=session['user_id'])
            db.session.add(new_budget)
            db.session.commit()
            flash("Budget added successfully!", "success")
            return redirect(url_for('budget'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding budget: {e}", "danger")

    budgets = Budget.query.filter_by(user_id=session['user_id']).all()
    return render_template('budget.html', form=form, budgets=budgets)

##### TRANSACTION ROUTES #####
@app.route('/budget/<int:budget_id>/add_transaction', methods=['GET', 'POST'])
def add_transaction(budget_id):
    """Add a transaction to a budget using SQLAlchemy ORM."""

    if not session.get('user_id'):
        return redirect(url_for('login'))

    form = TransactionForm()
    budget = Budget.query.filter_by(id=budget_id, user_id=session['user_id']).first()

    if not budget:
        flash("Budget not found or access denied.", "danger")
        return redirect(url_for('budget'))

    if form.validate_on_submit():
        try:
            new_transaction = Transaction(
                budget_id=budget.id,
                amount=form.amount.data,
                date=form.date.data,
                description=form.description.data
            )
            db.session.add(new_transaction)

            budget.amount_spent += form.amount.data
            db.session.commit()

            flash("Transaction added successfully!", "success")
            return redirect(url_for('budget'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding transaction: {e}", "danger")

    return render_template('add_transaction.html', form=form, budget=budget)

##### DASHBOARD ROUTE #####
@app.route('/dashboard')
def dashboard():
    """Render the User Dashboard"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    budgets = Budget.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', username=session['username'], budgets=budgets)

##### DELETE BUDGET ROUTE #####
@app.route('/budget/delete/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    """Delete a budget by ID"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    try:
        budget = Budget.query.filter_by(id=budget_id, user_id=session['user_id']).first()
        if not budget:
            flash("Budget not found.", "error")
            return redirect(url_for('budget'))

        db.session.delete(budget)
        db.session.commit()
        flash("Budget deleted successfully!", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting budget: {e}", "danger")

    return redirect(url_for('budget'))

##### INITIALIZE DATABASE #####
@app.before_first_request
def create_tables():
    """Ensures all tables are created before first request."""
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
