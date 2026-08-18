import os
import hashlib
import psycopg2
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*")
app.secret_key = 'halogen_secure_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Connection string do bazy Neon/Postgres - ustaw jako zmienną środowiskową
# DATABASE_URL w panelu Render (Environment -> Add Environment Variable)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Stabilne sesje w pamięci RAM serwera (odporne na restarty dysku Render)
ACTIVE_SESSIONS = set()


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def init_storage():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_storage()

def hash_password(password):
    salt = "halogen_secure_salt_key_"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def get_user_hash(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def user_exists(username):
    return get_user_hash(username) is not None

def create_user(username, password_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
    conn.commit()
    cur.close()
    conn.close()

def get_all_usernames():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username FROM users ORDER BY username')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]

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
    return jsonify({
        'wszyscy_zarejestrowani_uzytkownicy': get_all_usernames(),
        'obecnie_zalogowani': list(ACTIVE_SESSIONS)
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('user', '').strip()
    password = data.get('pass', '')

    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Wypełnij pola'}), 400

    stored_hash = get_user_hash(username)

    if stored_hash is None:
        return jsonify({'status': 'error', 'message': 'Konto nie istnieje. Najpierw się zarejestruj!'}), 401

    if stored_hash == hash_password(password):
        ACTIVE_SESSIONS.add(username)
        return jsonify({'status': 'success', 'user': username})

    return jsonify({'status': 'error', 'message': 'Błędne hasło!'}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    data = request.get_json() or {}
    username = data.get('user')
    if username and username in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.discard(username)

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

    if user_exists(username):
        return jsonify({'status': 'error', 'message': 'exists'})

    create_user(username, hash_password(password))
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
    if username and username in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.discard(username)
        del connected_users[request.sid]
    broadcast_user_list()

@socketio.on('register_socket')
def handle_register_socket(data):
    user = data.get('user')
    if not user or user == 'GUEST' or user == 'undefined' or user.strip() == '':
        return

    ACTIVE_SESSIONS.add(user)
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
