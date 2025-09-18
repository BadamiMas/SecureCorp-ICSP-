from flask import Flask
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",       # your MySQL password
        database="icsp"    # your database name
    )

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
conn.close()

print("Users in DB:", users)

app = Flask(__name__)
        

@app.route('/')
def hello():
    return "Hello, Flask is working!"

if __name__ == "__main__":
    app.run(debug=True)
