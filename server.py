from flask import Flask, request, jsonify, session, render_template, send_from_directory
import os
import json

app = Flask(__name__, template_folder='.', static_folder='.')
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

@app.route('/api/session', methods=['GET', 'POST'])
def api_session():
    if request.method == 'GET':
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return jsonify({'user': data.get('logged_user', 'GUEST')})
            except:
                pass
        return jsonify({'user': session.get('user', 'GUEST')})

    data = request.get_json()
    username = data.get('user')
    if username:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({'logged_user': username}, f, ensure_ascii=False, indent=4)
        session['user'] = username
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error'}), 400

# Endpoint diagnostyczny do podglądu zarejestrowanych użytkowników
@app.route('/api/admin/users', methods=['GET'])
def api_admin_users():
    users = load_users()
    return jsonify(users)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
