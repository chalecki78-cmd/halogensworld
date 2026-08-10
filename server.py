from flask import Flask, request, jsonify, session, render_template
import os
import json

# Ustawiamy template_folder='.', aby Flask szukał plików HTML w tym samym folderze, co server.py
app = Flask(__name__, template_folder='.')
app.secret_key = 'halogen_secure_secret_key'

USERS_FILE = 'users.json'
SESSION_FILE = 'current_session.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# Ścieżka do strony głównej
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')

    users = load_users()

    if username in users and users[username] == password:
        session['user'] = username
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Empty fields'}), 400

    users = load_users()

    if username in users:
        return jsonify({'status': 'error', 'message': 'exists'})

    users[username] = password
    save_users(users)

    return jsonify({'status': 'success'})

@app.route('/api/session', methods=['POST'])
def api_session():
    data = request.get_json()
    username = data.get('user')
    if username:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({'logged_user': username}, f, ensure_ascii=False, indent=4)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
