# --- OBSŁUGA CZATU (SOCKET.IO) ---
@socketio.on('join')
def on_join(data):
    user = data.get('user') or data.get('username') or session.get('user', 'GUEST')
    room = data.get('room', 'global')
    join_room(room)
    emit('status', {'msg': f'{user} dołączył do pokoju'}, room=room)

@socketio.on('chat_msg')
def handle_chat_msg(data):
    # Wyświetlamy w konsoli serwera dokładnie to, co przychodzi z przeglądarki, żeby zobaczyć strukturę
    print("Otrzymane dane czatu:", data)
    
    # Sprawdzamy wszystkie możliwe warianty klucza użytkownika
    user = data.get('user') or data.get('username') or data.get('name')
    if not user or user == 'GUEST':
        user = session.get('user', 'GUEST')
        
    room = data.get('room', 'global')
    msg = data.get('msg') or data.get('message')
    
    if msg:
        emit('new_message', {'user': user, 'msg': msg}, room=room)

@socketio.on('message')
def handle_message(data):
    print("Otrzymane dane message:", data)
    user = data.get('user') or data.get('username') or session.get('user', 'GUEST')
    room = data.get('room', 'global')
    msg = data.get('msg') or data.get('message')
    
    if msg:
        emit('new_message', {'user': user, 'msg': msg}, room=room)
