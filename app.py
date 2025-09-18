from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "yoursecretkey"  # needed for session

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",       
        password="",       
        database="icsp"  
    )

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE name=%s AND password=%s", (name, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = user['name']
        session['role'] = user['role']
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password")
        return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('test.html', username=session['username'])
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
