-- Users Table
CREATE TABLE IF NOT EXISTS Users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE
);

-- Accounts Table
CREATE TABLE IF NOT EXISTS Accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  account_name TEXT,
  FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- Transactions Table (for Accounts)
CREATE TABLE IF NOT EXISTS Transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL,
  date TEXT,
  amount REAL,
  description TEXT,
  category TEXT,
  FOREIGN KEY (account_id) REFERENCES Accounts(id)
);

-- Budgets Table
CREATE TABLE IF NOT EXISTS Budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  category TEXT NOT NULL,
  limit_amount REAL NOT NULL,
  amount_spent REAL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- Goals Table
CREATE TABLE IF NOT EXISTS Goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  goal_name TEXT,
  target_amount REAL,
  current_amount REAL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- BudgetTransaction Table for (tracking transactions within budgets)
CREATE TABLE IF NOT EXISTS BudgetTransaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  budget_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  date TEXT NOT NULL,
  description TEXT,
  FOREIGN KEY (budget_id) REFERENCES Budgets(id)
);