from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Transaction, SavingsGoal
from config import Config
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def dashboard():
    """
    Fetch and display the dashboard with user transactions, savings goals,
    and financial statistics (income, expenses, balance).
    """
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()

    income = sum(t.amount for t in transactions if t.type == 'income')
    expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = income - expenses
    current_amount = income - expenses

    categories = ['Income', 'Expenses']
    values = [income, expenses]
    plt.bar(categories, values)
    plt.xlabel('Category')
    plt.ylabel('Amount')
    plt.title('Income vs Expenses')

    img = io.BytesIO()
    plt.savefig(img, format='png') 
    img.seek(0) 
    plt.close() 
    chart_url = base64.b64encode(img.getvalue()).decode('utf8') 

    return render_template(
        'dashboard.html',
        income=income,
        expenses=expenses,
        balance=balance,
        chart_url=chart_url,
        goals=goals,
        transactions=transactions,
        current_amount=current_amount
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Allow users to log in by verifying their username and password.
    Redirect to the dashboard upon successful login.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user) 
            return redirect(url_for('dashboard')) 
        else:
            flash('Login Unsuccessful. Check username and password.', 'danger') 

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Allow new users to register by providing a username and password.
    Redirect to the login page after successful registration.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created!', 'success') 
        return redirect(url_for('login')) 

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """
    Log the user out and redirect to the login page.
    """
    logout_user() 
    return redirect(url_for('login'))

@app.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    """
    Allow users to add new transactions (income or expense) to their account.
    Redirect back to the dashboard after adding the transaction.
    """
    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        category = request.form.get('category')
        type_ = request.form.get('type')

        transaction = Transaction(amount=amount, category=category, type=type_, user_id=current_user.id)
        db.session.add(transaction)
        db.session.commit()

        flash('Transaction added successfully!', 'success') 
        return redirect(url_for('dashboard'))

    return render_template('add_transaction.html')

@app.route('/add_goal', methods=['GET', 'POST'])
@login_required
def add_goal():
    """
    Allow users to set new savings goals.
    Redirect back to the dashboard after adding the goal.
    """
    if request.method == 'POST':
        name = request.form.get('name')
        target_amount = float(request.form.get('target_amount'))

        goal = SavingsGoal(name=name, target_amount=target_amount, user_id=current_user.id)
        db.session.add(goal)
        db.session.commit()

        flash('Savings goal added!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_goal.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=False)
