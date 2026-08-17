import os
import json
import hashlib
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'halogen_secure_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
SESSIONS_FILE = os.path.join(BASE_DIR, 'active_sessions.json')

def hash_password(password):
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
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Wypełnij pola'}), 400

    users = load_json(USERS_FILE, {})
    hashed_pass = hash_password(password)

    if username not in users:
        users[username] = hashed_pass
        save_json(USERS_FILE, users)
    
    if users[username] == hashed_pass:
        session['user'] = username
        active = load_json(SESSIONS_FILE, [])
        if username not in active:
            active.append(username)
            save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Błędne hasło!'}), 401

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
        broadcast_user_list()
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
    users[username] = hash_password(password)
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

connected_users = {}

def broadcast_user_list():
    users_list = list(connected_users.keys())
    socketio.emit('update_user_list', users_list)

@socketio.on('connect')
def handle_connect():
    print("Klient połączył się z Socket.IO:", request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    for uname, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[uname]
            break
    broadcast_user_list()
    print("Klient rozłączył się:", request.sid)

@socketio.on('register_socket')
def handle_register_socket(data):
    user = data.get('user') or session.get('user', 'GUEST')
    connected_users[user] = request.sid
    broadcast_user_list()
    print(f"Zarejestrowano socket dla użytkownika: {user} -> SID: {request.sid}")

@socketio.on('join')
def on_join(data):
    user = data.get('user') or session.get('user', 'GUEST')
    room = data.get('room', 'global')
    join_room(room)
    emit('status', {'msg': f'{user} dołączył do pokoju: {room}'}, room=room)

@socketio.on('chat_msg')
def handle_chat_msg(data):
    user = data.get('user') or session.get('user', 'GUEST')
    room = data.get('room', 'global')
    msg = data.get('msg')
    recipient = data.get('recipient')

    if not msg:
        return

    if recipient and recipient != 'global':
        target_sid = connected_users.get(recipient)
        private_payload = {'user': user, 'msg': msg, 'private': True, 'recipient': recipient}
        if target_sid:
            socketio.emit('new_message', private_payload, room=target_sid)
        emit('new_message', private_payload)
    else:
        emit('new_message', {'user': user, 'msg': msg, 'room': room}, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
