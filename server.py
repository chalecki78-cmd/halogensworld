from flask import Flask, request, jsonify, session, render_template, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app, supports_credentials=True)
app.secret_key = 'halogen_secure_secret_key'

USERS_FILE = 'users.json'
SESSIONS_FILE = 'active_sessions.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {} if filename == USERS_FILE else []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {} if filename == USERS_FILE else []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    users = load_json(USERS_FILE)

    if username in users and users[username] == password:
        session['user'] = username
        active = load_json(SESSIONS_FILE)
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    if not username or not password: 
        return jsonify({'status': 'error'}), 400
    
    users = load_json(USERS_FILE)
    if username in users: 
        return jsonify({'status': 'error', 'message': 'exists'})
    
    users[username] = password
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    if request.method == 'GET':
        return jsonify({'user': session.get('user', 'GUEST')})
    
    data = request.get_json()
    username = data.get('user')
    if username:
        session['user'] = username
        active = load_json(SESSIONS_FILE)
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    return jsonify(load_json(USERS_FILE))

@app.route('/api/admin/active_sessions', methods=['GET'])
def api_admin_sessions():
    return jsonify(load_json(SESSIONS_FILE))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)from flask import Flask, request, jsonify, session, render_template, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app, supports_credentials=True)
app.secret_key = 'halogen_secure_secret_key'

USERS_FILE = 'users.json'
SESSIONS_FILE = 'active_sessions.json'

def load_json(filename):
    if not os.path.exists(filename):
        return {} if filename == USERS_FILE else []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {} if filename == USERS_FILE else []

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    users = load_json(USERS_FILE)

    if username in users and users[username] == password:
        session['user'] = username
        active = load_json(SESSIONS_FILE)
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    if not username or not password: 
        return jsonify({'status': 'error'}), 400
    
    users = load_json(USERS_FILE)
    if username in users: 
        return jsonify({'status': 'error', 'message': 'exists'})
    
    users[username] = password
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    if request.method == 'GET':
        return jsonify({'user': session.get('user', 'GUEST')})
    
    data = request.get_json()
    username = data.get('user')
    if username:
        session['user'] = username
        active = load_json(SESSIONS_FILE)
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    return jsonify(load_json(USERS_FILE))

@app.route('/api/admin/active_sessions', methods=['GET'])
def api_admin_sessions():
    return jsonify(load_json(SESSIONS_FILE))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
