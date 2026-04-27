from flask import send_from_directory
import os
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template,send_from_directory
import mysql.connector
import bcrypt
from config import DB_CONFIG

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def home():
    return render_template('index.html')

# REGISTER API
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    
    name = data['name']
    email = data['email']
    password = data['password']

    # HASH PASSWORD
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    db = get_db()
    cursor = db.cursor()

    query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, email, hashed_password))
    db.commit()

    return jsonify({"message": "User registered successfully"})

# LOGIN API  👈 MUST BE HERE
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    
    email = data['email']
    password = data['password']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM users WHERE email=%s"
    cursor.execute(query, (email,))
    
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"message": "Login successful", "user": user})
    else:
        return jsonify({"message": "Invalid email or password"}), 401
    
 # ADD TASK API
@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.json

    user_id = data['user_id']
    task_title = data['task_title']
    description = data['description']
    due_date = data['due_date']

    db = get_db()
    cursor = db.cursor()

    query = """
    INSERT INTO tasks (user_id, task_title, description, due_date)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (user_id, task_title, description, due_date))
    db.commit()

    return jsonify({"message": "Task added successfully"})

# GET TASKS API
@app.route('/get_tasks/<int:user_id>', methods=['GET'])
def get_tasks(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM tasks WHERE user_id=%s"
    cursor.execute(query, (user_id,))

    tasks = cursor.fetchall()

    return jsonify(tasks)

# UPDATE TASK STATUS
@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    status = data['status']

    db = get_db()
    cursor = db.cursor()

    query = "UPDATE tasks SET status=%s WHERE id=%s"
    cursor.execute(query, (status, task_id))
    db.commit()

    return jsonify({"message": "Task updated successfully"})

# DELETE TASK API
@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    db = get_db()
    cursor = db.cursor()

    query = "DELETE FROM tasks WHERE id=%s"
    cursor.execute(query, (task_id,))
    db.commit()

    return jsonify({"message": "Task deleted successfully"})


@app.route('/edit_task/<int:task_id>', methods=['PUT'])
def edit_task(task_id):
    data = request.json

    task_title = data['task_title']
    description = data['description']
    due_date = data['due_date']

    db = get_db()
    cursor = db.cursor()

    query = """
    UPDATE tasks
    SET task_title=%s, description=%s, due_date=%s
    WHERE id=%s
    """

    cursor.execute(query, (task_title, description, due_date, task_id))
    db.commit()

    return jsonify({"message": "Task updated successfully"})



@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')


@app.route('/admin_data', methods=['GET'])
def admin_data():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get all users
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()

    # Get all tasks
    cursor.execute("SELECT id, user_id, task_title, status,uploaded_file FROM tasks")
    tasks = cursor.fetchall()

    return jsonify({
        "users": users,
        "tasks": tasks
    })

@app.route('/admin_register')
def admin_register_page():
    return render_template('admin_register.html')


@app.route('/admin_login')
def admin_login_page():
    return render_template('admin_login.html')


@app.route('/admin_register_api', methods=['POST'])
def admin_register_api():
    data = request.json

    admin_name = data['admin_name']
    admin_email = data['admin_email']
    password = data['password']

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    db = get_db()
    cursor = db.cursor()

    query = "INSERT INTO admins (admin_name, admin_email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (admin_name, admin_email, hashed_password))
    db.commit()

    return jsonify({"message": "Admin registered successfully"})


@app.route('/admin_login_api', methods=['POST'])
def admin_login_api():
    data = request.json

    admin_email = data['admin_email']
    password = data['password']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM admins WHERE admin_email=%s"
    cursor.execute(query, (admin_email,))

    admin = cursor.fetchone()

    if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
        return jsonify({"message": "Admin login successful", "admin": admin})
    else:
        return jsonify({"message": "Invalid admin email or password"}), 401


@app.route('/upload_task/<int:task_id>', methods=['POST'])
def upload_task(task_id):
    print("Upload API called")

    if 'file' not in request.files:
        print("No file key found")
        return jsonify({"message": "No file selected"}), 400

    file = request.files['file']

    if file.filename == '':
        print("Empty filename")
        return jsonify({"message": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    print("Saving file to:", filepath)

    file.save(filepath)

    db = get_db()
    cursor = db.cursor()

    query = "UPDATE tasks SET uploaded_file=%s WHERE id=%s"
    cursor.execute(query, (filename, task_id))
    db.commit()

    return jsonify({"message": "File uploaded successfully"})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
# ALWAYS LAST
if __name__ == '__main__':
    print(app.url_map)
    app.run(debug=True)