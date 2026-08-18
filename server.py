import os
import json
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*")
app.secret_key = 'halogen_secure_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
SESSIONS_FILE = os.path.join(BASE_DIR, 'active_sessions.json')

def init_storage():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
            
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

init_storage()

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

@app.route('/api/debug_data', methods=['GET'])
def api_debug():
    users = load_json(USERS_FILE, {})
    active = load_json(SESSIONS_FILE, [])
    return jsonify({
        'wszyscy_zarejestrowani_uzytkownicy': list(users.keys()),
        'obecnie_zalogowani': active
    })

@app.route('/api/status', methods=['POST', 'GET'])
def api_status():
    # Pobieramy użytkownika z żądania POST lub nagłówka, aby uniknąć problemów z sesjami ciasteczkowymi
    data = request.get_json() if request.is_json else {}
    user = data.get('user') or request.args.get('user')
    
    if user:
        active = load_json(SESSIONS_FILE, [])
        if user in active:
            return jsonify({'logged': True, 'user': user})
            
    return jsonify({'logged': False, 'user': 'GUEST'})

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
        return jsonify({'status': 'error', 'message': 'Konto nie istnieje. Najpierw się zarejestruj!'}), 401

    if users[username] == hashed_pass:
        active = load_json(SESSIONS_FILE, [])
        
        if username in active:
            return jsonify({'status': 'error', 'message': 'Ten użytkownik jest już zalogowany na innym urządzeniu!'}), 401
        
        active.append(username)
        save_json(SESSIONS_FILE, active)
        return jsonify({'status': 'success', 'user': username})
    
    return jsonify({'status': 'error', 'message': 'Błędne hasło!'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    data = request.get_json() or {}
    username = data.get('user')
    if username:
        active = load_json(SESSIONS_FILE, [])
        if username in active:
            active.remove(username)
            save_json(SESSIONS_FILE, active)
        
        for sid, uname in list(connected_users.items()):
            if uname == username:
                del connected_users[sid]
        broadcast_user_list()
        
    return jsonify({'status': 'success'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')
    if not username or not password: 
        return jsonify({'status': 'error', 'message': 'Wypełnij pola'}), 400
    
    users = load_json(USERS_FILE, {})
    if username in users: 
        return jsonify({'status': 'error', 'message': 'exists'})
    
    users[username] = hash_password(password)
    save_json(USERS_FILE, users)
    return jsonify({'status': 'success'})

connected_users = {}

def broadcast_user_list():
    clean_users = set()
    for sid, uname in connected_users.items():
        if uname and isinstance(uname, str):
            uname_clean = uname.strip()
            if uname_clean and uname_clean != 'GUEST' and uname_clean != 'undefined':
                clean_users.add(uname_clean)
                
    users_list = list(clean_users)
    socketio.emit('update_user_list', users_list)

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on('disconnect')
def handle_disconnect():
    username = connected_users.get(request.sid)
    if username:
        active = load_json(SESSIONS_FILE, [])
        if username in active:
            active.remove(username)
            save_json(SESSIONS_FILE, active)
        del connected_users[request.sid]
    broadcast_user_list()

@socketio.on('register_socket')
def handle_register_socket(data):
    user = data.get('user')
    if not user or user == 'GUEST' or user == 'undefined' or user.strip() == '':
        return
    
    active = load_json(SESSIONS_FILE, [])
    if user not in active:
        return

    connected_users[request.sid] = user
    broadcast_user_list()

@socketio.on('join')
def on_join(data):
    user = data.get('user', 'GUEST')
    room = data.get('room', 'global')
    join_room(room)
    if user != 'GUEST':
        emit('status', {'msg': f'{user} dołączył do pokoju: {room}'}, room=room)

@socketio.on('chat_msg')
def handle_chat_msg(data):
    user = data.get('user', 'GUEST')
    room = data.get('room', 'global')
    msg = data.get('msg')
    recipient = data.get('recipient')

    if not msg or user == 'GUEST' or user == 'undefined':
        return

    if recipient and recipient != 'global':
        target_sid = None
        for sid, uname in connected_users.items():
            if uname == recipient:
                target_sid = sid
                break

        private_payload = {'user': user, 'msg': msg, 'private': True, 'recipient': recipient}
        if target_sid:
            socketio.emit('new_message', private_payload, room=target_sid)
        emit('new_message', private_payload)
    else:
        emit('new_message', {'user': user, 'msg': msg, 'room': room}, room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
