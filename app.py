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
from face import encodings
from werkzeug.security import generate_password_hash, check_password_hash



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

#--------------------------------------------
# DASHBOARD ROUTE WITH ROLE-BASED REDIRECTION
#--------------------------------------------

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

#---------------------------------------------
# JOB ROUTE
#---------------------------------------------

@app.route('/job')
def job():
    if 'user' not in session:
        return redirect(url_for('home'))

    role = session.get('role', 'user')
    if role == 'Accountant':
        return redirect(url_for('cashtable'))
    elif role == 'HR':
        return redirect(url_for('jobtable'))
    elif role == 'Head':
        return redirect(url_for('headtable'))
    else:
        return redirect(url_for('jobtable'))


@app.route('/acc_job')
def acc_job():
    return render_template('acc_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/hr_job')
def hr_job():
    return render_template('hr_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/head_job')
def head_job():
    return render_template('head_job.html', username=session['user'], role=session.get('role', 'user'))


@app.route('/doc')
def doc():
    return render_template('doc.html', username=session['user'], role=session.get('role', 'user'))


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

@app.route("/encrypt", methods=["POST"])
def encrypt_file():
    file = request.files.get("file")
    key = request.form.get("key")
    salt = key[::-1]  # always derive salt from key for simplicity

    if not file or not key:
        flash("File and key are required")
        return redirect(url_for("encrypt_file"))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    cipher = EncryptionTool(filepath, key, salt)
    for _ in cipher.encrypt():  # run generator
        pass

    return send_file(
        cipher.encrypt_output_file,
        as_attachment=True,
        download_name=os.path.basename(cipher.encrypt_output_file)
    )


@app.route("/decrypt", methods=["POST"])
def decrypt_file():
    file = request.files.get("file")
    key = request.form.get("key")
    salt = key[::-1]  # must be exactly the same as encryption

    if not file or not key:
        flash("File and key are required")
        return redirect(url_for("decrypt_file"))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    cipher = EncryptionTool(filepath, key, salt)
    for _ in cipher.decrypt():
        pass

    return send_file(
        cipher.decrypt_output_file,
        as_attachment=True,
        download_name=os.path.basename(cipher.decrypt_output_file)
    )


#**************************
# JOB CRUD OPERATIONS
#**************************

#-------------------------------
# HR CRUD
#-------------------------------

@app.route('/jobtable')
def jobtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    employee_to_edit = None
    if edit_id:
        cursor.execute("SELECT * FROM employees WHERE id=%s", (edit_id,))
        employee_to_edit = cursor.fetchone()
    conn.close()
    return render_template('hr_job.html', employees=employees, employee_to_edit=employee_to_edit)

# Add employee
@app.route('/addj', methods=['POST'])
def addj():
    name = request.form['name']
    age = request.form['age']
    city = request.form['city']
    email = request.form['email']
    number = request.form['number']
    role = request.form['role']
    date_hired = request.form['date_hired']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (name, age, city, email, number, role, date_hired)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (name, age, city, email, number, role, date_hired))
    conn.commit()
    conn.close()
    return redirect(url_for('jobtable'))

# Edit employee
@app.route('/editj/<int:id>', methods=['POST'])
def editj(id):
    name = request.form['name']
    age = request.form['age']
    city = request.form['city']
    email = request.form['email']
    number = request.form['number']
    role = request.form['role']
    date_hired = request.form['date_hired']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE employees
        SET name=%s, age=%s, city=%s, email=%s, number=%s, role=%s, date_hired=%s
        WHERE id=%s
    """, (name, age, city, email, number, role, date_hired, id))
    conn.commit()
    conn.close()
    return redirect(url_for('jobtable'))

# Delete employee
@app.route('/deletej/<int:id>', methods=['POST'])
def deletej(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('jobtable'))


#-------------------------------
# ACC CRUD
#-------------------------------

# View cash flow table
@app.route('/cashtable')
def cashtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM cash_flow ORDER BY flow_date DESC")
    cash_flows = cursor.fetchall()
    cash_to_edit = None

    if edit_id:
        cursor.execute("SELECT * FROM cash_flow WHERE id=%s", (edit_id,))
        cash_to_edit = cursor.fetchone()

    conn.close()
    return render_template('acc_job.html', cash_flows=cash_flows, cash_to_edit=cash_to_edit)


# Add cash flow
@app.route('/addc', methods=['POST'])
def addc():
    flow_date = request.form['flow_date']
    cash_in = request.form['cash_in']
    cash_out = request.form['cash_out']
    name = request.form['name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cash_flow (flow_date, cash_in, cash_out, name)
        VALUES (%s, %s, %s, %s)
    """, (flow_date, cash_in, cash_out, name))
    conn.commit()
    conn.close()
    return redirect(url_for('cashtable'))


# Edit cash flow
@app.route('/editc/<int:id>', methods=['POST'])
def editc(id):
    flow_date = request.form['flow_date']
    cash_in = request.form['cash_in']
    cash_out = request.form['cash_out']
    name = request.form['name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cash_flow
        SET flow_date=%s, cash_in=%s, cash_out=%s, name=%s
        WHERE id=%s
    """, (flow_date, cash_in, cash_out, name, id))
    conn.commit()
    conn.close()
    return redirect(url_for('cashtable'))


# Delete cash flow
@app.route('/deletec/<int:id>', methods=['POST'])
def deletec(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cash_flow WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('cashtable'))



#-------------------------------
# HEAD CRUD
#-------------------------------

# View all Head users
@app.route('/headtable')
def headtable():
    if 'user' not in session:
        return redirect(url_for('home'))

    edit_id = request.args.get('edit_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    user_to_edit = None

    if edit_id:
        cursor.execute("SELECT * FROM users WHERE id=%s", (edit_id,))
        user_to_edit = cursor.fetchone()

    conn.close()
    return render_template('head_job.html', users=users, user_to_edit=user_to_edit)


# Add Head user
@app.route('/addh', methods=['POST'])
def addh():
    name = request.form['name']
    password = request.form['password']
    role = request.form['role']
    image_file = request.files['face_image']  # face image input

    # Save temporarily to get encoding
    image_path = f"temp/{image_file.filename}"
    image_file.save(image_path)

    face_encode_b64 = encodings(image_path)
    if not face_encode_b64:
        return "No face detected in the image.", 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, password, role, face_encode)
        VALUES (%s, %s, %s, %s)
    """, (name, password, role, face_encode_b64))
    conn.commit()
    conn.close()

    return redirect(url_for('headtable'))


# Edit Head user
@app.route('/edith/<int:id>', methods=['POST'])
def edith(id):
    name = request.form['name']
    password = request.form['password']
    role = request.form['role']
    image_file = request.files.get('face_image')  # optional, may not upload new image

    conn = get_db_connection()
    cursor = conn.cursor()

    if image_file and image_file.filename != "":
        image_path = f"temp/{image_file.filename}"
        image_file.save(image_path)
        face_encode_b64 = encodings(image_path)
        cursor.execute("""
            UPDATE users
            SET name=%s, password=%s, role=%s, face_encode=%s
            WHERE id=%s
        """, (name, password, role, face_encode_b64, id))
    else:
        cursor.execute("""
            UPDATE users
            SET name=%s, password=%s, role=%s
            WHERE id=%s
        """, (name, password, role, id))

    conn.commit()
    conn.close()
    return redirect(url_for('headtable'))


# Delete Head user
@app.route('/deleteh/<int:id>', methods=['POST'])
def deleteh(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('headtable'))




# LOGOUT ROUTE #

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)


