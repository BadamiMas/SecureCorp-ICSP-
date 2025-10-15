from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from datetime import timedelta, datetime
from flask_wtf.csrf import generate_csrf
import cv2
import numpy as np
import face_recognition
import base64
from Secrefy import EncryptionTool
import os


app = Flask(__name__)
app.secret_key = "icsp"  # needed for session

# Security Config
app.config.update({
    'SESSION_COOKIE_SAMESITE': "None",
    'SESSION_COOKIE_SECURE': True,
    'PERMANENT_SESSION_LIFETIME' : timedelta(minutes=10)
})

# Extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
csrf.init_app(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

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

    if not name or not password:
        flash("Please fill in both fields")
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE name=%s AND password=%s", (name, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = user['name']
        session['role'] = user.get("role", "user")
        session.permanent = True
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password")
        return redirect(url_for('home'))


@app.route("/face_login", methods=["POST"])
def face_login():
    data = request.get_json()
    if not data or "image" not in data:
        print("No image received!")   # <-- debug
        return jsonify({"success": False, "message": "No image received"})
    
    print("Image received!")   # <-- debug
    print(data["image"][:50])   # <-- debug



    # Decode base64 image from browser
    image_data = data["image"].split(",")[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Detect face
    encodings = face_recognition.face_encodings(frame)
    if len(encodings) == 0:
        return jsonify({"success": False, "message": "No face detected. Try again."})

    current_encoding = encodings[0]

    # Load face encodes from DB
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, role, face_encode FROM users")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        db_encoding = np.frombuffer(base64.b64decode(user["face_encode"]), dtype=np.float64)
        match = face_recognition.compare_faces([db_encoding], current_encoding)[0]
        if match:
            session["user"] = user["name"]
            session["role"] = user.get("role", "user")
            return jsonify({"success": True, "redirect": url_for("dashboard")})

    print(f"Matched user: {user['name']} ({user['role']})")  # <-- debug
    return jsonify({"success": False, "message": "Face not recognized"})


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    role = session.get('role', 'user')
    if role == 'Accountant':
        return redirect(url_for('acc_dashboard'))
    elif role == 'HR':
        return redirect(url_for('hr_dashboard'))
    elif role == 'Head':
        return redirect(url_for('head_dashboard'))
    else:
        return render_template('test.html', username=session['user'])

    

@app.route('/acc_dashboard')
def acc_dashboard():
        return render_template('acc_dashboard.html', username=session['user'], role=session.get('role', 'user'))

@app.route('/head_dashboard')
def head_dashboard():
        return render_template('head_dashboard.html', username=session['user'], role=session.get('role', 'user'))

@app.route('/hr_dashboard')
def hr_dashboard():
        return render_template('hr_dashboard.html', username=session['user'], role=session.get('role', 'user'))

@app.route('/doc')
def doc():
    return render_template('doc.html')


# HEAD GRAPH

@app.route('/get_total_employees')
def get_total_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return jsonify({'total_employees': total})

@app.route('/get_company_progress')
def get_company_progress():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # --- Get current year and last 6 months range ---
    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # roughly 5 months before
    end_date = now

    # --- Get monthly cash flow (sum of in/out) within last 6 months ---
    cursor.execute("""
        SELECT 
            YEAR(flow_date) AS year,
            MONTH(flow_date) AS month,
            SUM(cash_in) AS total_in,
            SUM(cash_out) AS total_out
        FROM cash_flow
        WHERE flow_date BETWEEN %s AND %s
        GROUP BY YEAR(flow_date), MONTH(flow_date)
        ORDER BY YEAR(flow_date), MONTH(flow_date)
    """, (start_date, end_date))
    cash_data = cursor.fetchall()

    # --- Get employee count by hire month within last 6 months ---
    cursor.execute("""
        SELECT 
            YEAR(date_hired) AS year,
            MONTH(date_hired) AS month,
            COUNT(*) AS total_hired
        FROM employees
        WHERE date_hired BETWEEN %s AND %s
        GROUP BY YEAR(date_hired), MONTH(date_hired)
        ORDER BY YEAR(date_hired), MONTH(date_hired)
    """, (start_date, end_date))
    emp_data = cursor.fetchall()

    cursor.close()
    conn.close()

    # --- Merge data ---
    data_by_month = {}

    for row in cash_data:
        key = (row['year'], row['month'])
        data_by_month[key] = {
            'cash_in': float(row['total_in'] or 0),
            'cash_out': float(row['total_out'] or 0),
            'employees': 0
        }

    for row in emp_data:
        key = (row['year'], row['month'])
        if key not in data_by_month:
            data_by_month[key] = {'cash_in': 0, 'cash_out': 0, 'employees': 0}
        data_by_month[key]['employees'] = row['total_hired']

    formatted = []
    for (year, month) in sorted(data_by_month.keys()):
        if year == now.year:  # only this year
            formatted.append({
                'year': year,
                'month': month,
                'cash_in': data_by_month[(year, month)]['cash_in'],
                'cash_out': data_by_month[(year, month)]['cash_out'],
                'employees': data_by_month[(year, month)]['employees']
            })

    return jsonify(formatted)


# HR GRAPH

@app.route('/get_company_progress_hr')
def get_company_progress_hr():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # last 5 months
    end_date = now

    cursor.execute("""
        SELECT 
            YEAR(date_hired) AS year,
            MONTH(date_hired) AS month,
            COUNT(*) AS total_hired
        FROM employees
        WHERE date_hired BETWEEN %s AND %s
        GROUP BY YEAR(date_hired), MONTH(date_hired)
        ORDER BY YEAR(date_hired), MONTH(date_hired)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # fill missing months with 0
    data_by_month = {}
    for i in range(6):
        month = (start_date + timedelta(days=30*i)).month
        data_by_month[(now.year, month)] = 0

    for row in rows:
        key = (row['year'], row['month'])
        data_by_month[key] = row['total_hired']

    formatted = []
    for (year, month) in sorted(data_by_month.keys()):
        if year == now.year:
            formatted.append({
                'year': year,
                'month': month,
                'employees': data_by_month[(year, month)]
            })

    return jsonify(formatted)


# ACCOUNTANT GRAPH

@app.route('/get_company_progress_acc')
def get_cash_flow():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Last 6 months
    now = datetime.now()
    start_date = (now.replace(day=1) - timedelta(days=150)).replace(day=1)  # roughly 5 months before
    end_date = now

    cursor.execute("""
        SELECT 
            YEAR(flow_date) AS year,
            MONTH(flow_date) AS month,
            SUM(cash_in) AS cash_in,
            SUM(cash_out) AS cash_out
        FROM cash_flow
        WHERE flow_date BETWEEN %s AND %s
        GROUP BY YEAR(flow_date), MONTH(flow_date)
        ORDER BY YEAR(flow_date), MONTH(flow_date)
    """, (start_date, end_date))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Format to return month name + amounts
    data = []
    for row in rows:
        month_name = datetime(row['year'], row['month'], 1).strftime('%b')
        data.append({
            'month': month_name,
            'cash_in': float(row['cash_in'] or 0),
            'cash_out': float(row['cash_out'] or 0)
        })

    return jsonify(data)


# SECREFY TKINTER TO FLASK

@app.route("/encrypt", methods=["GET", "POST"])
def encrypt_file():
    if request.method == "POST":
        file = request.files.get("file")
        key = request.form.get("key")
        salt = request.form.get("salt") or key[::-1]

        if not file or not key:
            flash("File and key are required")
            return render_template("encrypt.html")

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        cipher = EncryptionTool(filepath, key, salt)
        # Run encryption fully
        for _ in cipher.encrypt():
            pass  # optionally track progress

        return send_file(cipher.encrypt_output_file, as_attachment=True)

    return render_template("encrypt.html")


@app.route("/decrypt", methods=["GET", "POST"])
def decrypt_file():
    if request.method == "POST":
        file = request.files.get("file")
        key = request.form.get("key")
        salt = request.form.get("salt") or key[::-1]

        if not file or not key:
            flash("File and key are required")
            return render_template("decrypt.html")

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        cipher = EncryptionTool(filepath, key, salt)
        for _ in cipher.decrypt():
            pass

        return send_file(cipher.decrypt_output_file, as_attachment=True)

    return render_template("decrypt.html")



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)


