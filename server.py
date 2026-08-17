from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import json
import hashlib

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'halogen_secure_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
SESSIONS_FILE = os.path.join(BASE_DIR, 'active_sessions.json')

def hash_password(password):
    # Trwałe zabezpieczenie haseł za pomocą szyfrowania SHA-256 z solą systemową
    salt = "halogen_secure_salt_key_"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(BASE_DIR, filename)
    return "Plik nie istnieje", 404

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    users = load_json(USERS_FILE, {})

    hashed_pass = hash_password(password)

    if username in users and users[username] == hashed_pass:
        session['user'] = username
        active = load_json(SESSIONS_FILE, [])
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    data = request.get_json() or {}
    username = data.get('user') or session.get('user')
    
    if 'user' in session:
        session.pop('user', None)
        
    if username:
        active = load_json(SESSIONS_FILE, [])
        if username in active:
            active.remove(username)
            save_json(SESSIONS_FILE, active)
            
    return jsonify({'status': 'success'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    if not username or not password: 
        return jsonify({'status': 'error'}), 400
    
    users = load_json(USERS_FILE, {})
    if username in users: 
        return jsonify({'status': 'error', 'message': 'exists'})
    
    # Zapisujemy zaszyfrowane hasło trwale w pliku users.json
    users[username] = hash_password(password)
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    if request.method == 'GET':
        return jsonify({'user': session.get('user', 'GUEST')})
    
    data = request.get_json() or {}
    username = data.get('user')
    if username:
        session['user'] = username
        active = load_json(SESSIONS_FILE, [])
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    return jsonify(load_json(USERS_FILE, {}))

@app.route('/api/admin/active_sessions', methods=['GET'])
def api_admin_sessions():
    return jsonify(load_json(SESSIONS_FILE, []))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'halogen_secure_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
SESSIONS_FILE = os.path.join(BASE_DIR, 'active_sessions.json')

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(BASE_DIR, filename)
    return "Plik nie istnieje", 404

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    users = load_json(USERS_FILE, {})

    if username in users and users[username] == password:
        session['user'] = username
        active = load_json(SESSIONS_FILE, [])
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    data = request.get_json() or {}
    username = data.get('user') or session.get('user')
    
    if 'user' in session:
        session.pop('user', None)
        
    if username:
        active = load_json(SESSIONS_FILE, [])
        if username in active:
            active.remove(username)
            save_json(SESSIONS_FILE, active)
            
    return jsonify({'status': 'success'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    if not username or not password: 
        return jsonify({'status': 'error'}), 400
    
    users = load_json(USERS_FILE, {})
    if username in users: 
        return jsonify({'status': 'error', 'message': 'exists'})
    
    users[username] = password
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    if request.method == 'GET':
        return jsonify({'user': session.get('user', 'GUEST')})
    
    data = request.get_json() or {}
    username = data.get('user')
    if username:
        session['user'] = username
        active = load_json(SESSIONS_FILE, [])
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    return jsonify(load_json(USERS_FILE, {}))

@app.route('/api/admin/active_sessions', methods=['GET'])
def api_admin_sessions():
    return jsonify(load_json(SESSIONS_FILE, []))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
