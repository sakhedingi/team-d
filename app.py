from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'personal_budget'

mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    port=app.config['MYSQL_PORT'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

@app.route('/')
def index():
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pwd = request.form["password"]

        cursor = mysql.cursor()
        cursor.execute(f"SELECT username, password FROM users WHERE username = '{username}'")
        user = cursor.fetchone()
        cursor.close()

        hashed_pwd = user[1].encode('utf-8')

        def verify_password(pwd, hashed_pwd):
            return bcrypt.checkpw(pwd.encode('utf-8'), hashed_pwd)

        is_verified = verify_password(pwd, hashed_pwd)

        if is_verified:
            session['username'] = user[0]
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form["username"]
        pwd = request.form["password"]
        confirm_pwd = request.form["confirm_password"]

        if pwd == confirm_pwd:
            print("password match")
        else:
            error = "Confirm password donnot match"
            return render_template('signup.html', error=error)

        def hash_password(pwd):
            salt = bcrypt.gensalt()
            hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), salt)
            return hashed_pwd
            
        hashed_pwd = hash_password(pwd)

        cash = request.form["cash"]

        if not cash:
            cash = 0.00

        cursor = mysql.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pwd))
        mysql.commit()

        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO income (user_id, source, amount) VALUES (%s, %s, %s)", (user_id, "cash", cash))
        mysql.commit()
        cursor.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        cursor = mysql.cursor()

        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(amount) AS totalIncome FROM income INNER JOIN users ON income.user_id = %s AND users.id = %s", (user_id, user_id))
        totalIncome = cursor.fetchone()[0]

        cursor.execute("select SUM(amount) as totalExpenses from expenses inner join users on expenses.user_id = %s and users.id = %s", (user_id, user_id))
        totalExpenses = cursor.fetchone()[0]

        if totalExpenses is not None:
            balance = totalIncome - totalExpenses
        else:
            totalExpenses = 0.00
            totalExpenses = "{:.2f}".format(totalExpenses)
            balance = totalIncome

        cursor.close()
        return render_template('dashboard.html', totalIncome=totalIncome, totalExpenses=totalExpenses, balance=balance)
    return redirect(url_for('login'))

@app.route('/track')
def track():
    if 'username' in session:
        username = session['username']
        cursor = mysql.cursor()

        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = cursor.fetchone()[0]

        cursor.execute("select description, category, amount, date from expenses where user_id = %s", (user_id,))
        expenses = cursor.fetchall()

        cursor.execute("select source, amount, date from income where user_id = %s", (user_id,))
        incomes = cursor.fetchall()

        cursor.close()
        return render_template('track.html', incomes=incomes, expenses=expenses)
    return redirect(url_for('home'))

@app.route('/add_income', methods=['POST'])
def add_income():
    if 'username' in session:
        username = session['username']
        cursor = mysql.cursor()

        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = cursor.fetchone()[0]

        source = request.form['source']
        amount = request.form['amount']

        cursor.execute("INSERT INTO income (user_id, source, amount) VALUES (%s, %s, %s)", (user_id, source, amount))
        mysql.commit()

        cursor.close()

        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'username' in session:
        username = session['username']
        cursor = mysql.cursor()

        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        user_id = cursor.fetchone()[0]

        description = request.form['description']
        category = request.form['category']
        amount = request.form['amount']

        cursor.execute("INSERT INTO expenses (user_id, description, category, amount) VALUES (%s, %s, %s, %s)", (user_id, description, category, amount))
        mysql.commit()

        cursor.close()

        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
