# **Personal Finance Dashboard**

**Live Site URL**: [https://yourwebsiteurl.com](https://yourwebsiteurl.com)

## **About the Website**

The Personal Finance Dashboard is a web application designed to help users manage their budgets, track financial goals, and monitor transactions. The platform provides an intuitive interface for individuals to gain better control of their finances by offering tools to track spending, set financial goals, and analyze trends over time.

---

## **Features**

### **1. Budget Management**
- **What it does**: Users can create, edit, and delete budget categories, set spending limits, and view the amount spent versus the remaining balance.
- **Why implemented**: Budgeting is a cornerstone of financial planning, enabling users to allocate their resources effectively and avoid overspending.

### **2. Financial Goals**
- **What it does**: Allows users to set financial goals with a target amount, track progress, and add funds to their goals.
- **Why implemented**: Helps users focus on saving for specific objectives, such as buying a car, going on vacation, or creating an emergency fund.

### **3. Invoice Upload for Transactions**
- **What it does**: Users can upload bank statements in CSV or Excel format to automatically import and categorize transactions.
- **Why implemented**: Provides an alternative to Plaid API for integrating financial data, offering users more control and privacy.

### **4. Spending Analytics**
- **What it does**: Visualizes user spending through charts, such as doughnut charts for category breakdowns and bar charts for goal progress.
- **Why implemented**: Helps users quickly interpret financial trends and make informed decisions.

### **5. Quick Links**
- **What it does**: Provides users with easy access to manage budgets, view goals, and log out.
- **Why implemented**: Simplifies navigation and enhances user experience.

### **6. Plaid API Integration (Disabled)**
- **What it does**: Links bank accounts to automatically fetch and sync transactions.
- **Why implemented**: Intended to automate data import and reduce manual effort, though currently disabled due to alternative upload functionality.

---

## **User Flow**

1. **Registration/Login**:
   - New users sign up with a username, email, and password.
   - Returning users log in to access their dashboard.

2. **Dashboard Overview**:
   - View a snapshot of financial health, including budgets, goals, and recent spending trends.
   - Access links to manage budgets or upload bank statements.

3. **Manage Budgets**:
   - Add, edit, or delete budget categories and set spending limits.

4. **Track Financial Goals**:
   - Set new goals, add funds, and track progress visually.

5. **Upload Bank Statements**:
   - Upload CSV or Excel files to import and categorize transactions automatically.

6. **Visual Analytics**:
   - Explore spending breakdowns and goal progress via interactive charts.

---

## **Technology Stack**

### **Backend**
- **Flask**: Used as the web framework for handling routes, forms, and rendering templates.
- **SQLite**: Chosen for its lightweight, file-based database structure, ideal for this project.
- **WTForms**: Simplifies form handling and validation.

### **Frontend**
- **Foundation CSS Framework**: Provides responsive layouts and styling for components.
- **Chart.js**: Used to create interactive visualizations for spending and goals.
- **Custom CSS**: Adds project-specific styles for a polished look.

### **File Handling**
- **Pandas**: Processes uploaded bank statements (CSV/Excel) for transaction import.

### **Integration**
- **Plaid API (Disabled)**:
  - Was intended to enable seamless bank account linking.
  - Currently replaced with the invoice upload feature for enhanced user control.

---

## **Notes on the Plaid API**

- **Why Plaid API**:
  - Provides robust financial integrations, allowing users to link bank accounts and fetch real-time transaction data.
- **Challenges**:
  - Configuration and authentication issues led to temporary deactivation.
- **Future Plans**:
  - May re-enable Plaid integration to complement the existing invoice upload feature.

---

## **Deployment**

The project is deployed at: [https://yourwebsiteurl.com](https://yourwebsiteurl.com).

### **Running Locally**

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/personal-finance-dashboard.git
2. Create a virtual environment:
   ```bash
   - python -m venv venv
3. Activate the virtual environment:
   - on MacOS/Linux:
   ```bash
   source venv/bin/activate
   - on Windows:
   ```bash
   venv\Scripts\activate
4. Install dependencies
   ```bash
   pip install -r requirements.txt
5. Initialize the database:
   ```bash
   flask shell
   >>> from app import init_db
   >>> init_db()
   >>> exit()
6. Run the app:
   ```bash
   python3 app.py

