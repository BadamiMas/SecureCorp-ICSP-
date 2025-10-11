from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import mysql.connector
from flask_bcrypt import Bcrypt, generate_password_hash
from flask_wtf import CSRFProtect
from datetime import timedelta
from flask_wtf.csrf import generate_csrf
import cv2
import numpy as np
import face_recognition
import base64


app = Flask(__name__)
app.secret_key = "icsp"  # needed for session

# Security Config
app.config['SESSION_COOKIE_SECURE'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
@app.before_request
def make_session_permanent():
    session.permanent = True
    session.modified = True  # tells Flask to reset the expiration

# Extensions
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
csrf.init_app(app)





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
    cursor.execute("SELECT name, face_encode FROM users")
    users = cursor.fetchall()
    conn.close()

    for user in users:
        db_encoding = np.frombuffer(base64.b64decode(user["face_encode"]), dtype=np.float64)
        match = face_recognition.compare_faces([db_encoding], current_encoding)[0]
        if match:
            session["user"] = user["name"]
            session["role"] = user.get("role", "user")
            return jsonify({"success": True, "redirect": url_for("dashboard")})

    return jsonify({"success": False, "message": "Face not recognized"})


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    role = session.get('role', 'user')
    if role == 'acc':
        return redirect(url_for('acc_dashboard'))
    elif role == 'hr':
        return redirect(url_for('hr_dashboard'))
    elif role == 'head':
        return redirect(url_for('head_dashboard'))
    else:
        return render_template('test.html', username=session['user'])

    

@app.route('/acc_dashboard')
def acc_dashboard():
        return render_template('acc_dashboard.html', username=session['user'])

@app.route('/head_dashboard')
def head_dashboard():
        return render_template('head_dashboard.html', username=session['user'])

@app.route('/hr_dashboard')
def hr_dashboard():
        return render_template('hr_dashboard.html', username=session['user'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)


