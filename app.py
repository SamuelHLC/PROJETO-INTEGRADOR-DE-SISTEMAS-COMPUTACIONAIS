from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify
import sqlite3
import hashlib
import os
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import uuid # Importado para gerar nomes de arquivo únicos
from werkzeug.utils import secure_filename # Importado para garantir nomes de arquivos seguros

# --- Configuração ---
DATABASE = 'chat_database.db'
SECRET_KEY = os.environ.get('SECRET_KEY', 'uma_chave_secreta_muito_forte_e_unica') 
# Nova configuração para a pasta de uploads
UPLOADS_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DATABASE'] = DATABASE
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER
socketio = SocketIO(app, manage_session=False)

# Cria a pasta de uploads se ela não existir
if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

# --- Funções Auxiliares do Banco de Dados (sem alterações) ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS salas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            )
        ''')
        # Tabela de Mensagens - agora com um campo para tipo (texto, imagem)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sala_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                conteudo TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'text',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sala_id) REFERENCES salas (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuario_sala_ativo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                sala_id INTEGER NOT NULL,
                timestamp_entrada DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (sala_id) REFERENCES salas (id),
                UNIQUE(usuario_id, sala_id)
            )
        ''')
        db.commit()

# --- Funções Auxiliares do Banco de Dados ---
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_user_by_username(username):
    return query_db('SELECT * FROM usuarios WHERE username = ?', [username], one=True)

def add_user(username, password_hash):
    db = get_db()
    try:
        db.execute('INSERT INTO usuarios (username, password_hash) VALUES (?, ?)', [username, password_hash])
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_rooms():
    return query_db('SELECT * FROM salas ORDER BY nome')

def get_room_by_id(room_id):
    return query_db('SELECT * FROM salas WHERE id = ?', [room_id], one=True)

def add_room(room_name):
    db = get_db()
    try:
        db.execute('INSERT INTO salas (nome) VALUES (?)', [room_name])
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_messages_in_room(room_id):
    # Alterado para buscar o tipo da mensagem também
    return query_db("""
        SELECT m.conteudo, u.username, m.timestamp, m.tipo
        FROM mensagens m
        JOIN usuarios u ON m.usuario_id = u.id
        WHERE m.sala_id = ?
        ORDER BY m.timestamp
    """, [room_id])

def add_message(room_id, user_id, content, message_type='text'):
    db = get_db()
    db.execute('INSERT INTO mensagens (sala_id, usuario_id, conteudo, tipo) VALUES (?, ?, ?, ?)', [room_id, user_id, content, message_type])
    db.commit()

def get_active_users_in_room(room_id):
    result = query_db('SELECT COUNT(DISTINCT usuario_id) as count FROM usuario_sala_ativo WHERE sala_id = ?', [room_id], one=True)
    return result['count'] if result and result['count'] else 0

def set_user_active_in_room(user_id, room_id):
    db = get_db()
    db.execute('INSERT OR REPLACE INTO usuario_sala_ativo (usuario_id, sala_id, timestamp_entrada) VALUES (?, ?, ?)', [user_id, room_id, datetime.now()])
    db.commit()

def remove_user_from_room(user_id, room_id):
    db = get_db()
    db.execute('DELETE FROM usuario_sala_ativo WHERE usuario_id = ? AND sala_id = ?', [user_id, room_id])
    db.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password_hash, provided_password):
    return stored_password_hash == hash_password(provided_password)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rotas Flask (com pequenas modificações) ---
@app.before_request
def before_request():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    if 'user_id' not in session and request.endpoint not in ['login', 'register', 'static', 'create_room', 'get_rooms_api', 'join_room_api', 'upload_image']:
        return redirect(url_for('login'))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('rooms'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('rooms'))
        else:
            return render_template('login.html', error="Usuário ou senha incorretos.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error="Nome de usuário e senha não podem ser vazios.")
        password_hash = hash_password(password)
        if add_user(username, password_hash):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Nome de usuário já existe.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'current_room_id' in session:
        if 'user_id' in session:
            remove_user_from_room(session['user_id'], session['current_room_id'])
        del session['current_room_id']
        del session['current_room_name']
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/rooms')
def rooms():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if 'current_room_id' in session:
        if 'user_id' in session:
            remove_user_from_room(session['user_id'], session['current_room_id'])
        del session['current_room_id']
        del session['current_room_name']
    return render_template('rooms.html', username=session['username'], rooms=get_rooms())

@app.route('/create_room', methods=['POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    room_name = request.form['room_name']
    if room_name and add_room(room_name):
        return redirect(url_for('rooms'))
    else:
        return render_template('rooms.html', username=session['username'], rooms=get_rooms(), error="Nome da sala inválido ou já existe.")

@app.route('/chat/<int:room_id>')
def chat(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    room = get_room_by_id(room_id)
    if not room:
        return "Sala não encontrada", 404
    session['current_room_id'] = room['id']
    session['current_room_name'] = room['nome']
    return render_template('chat.html', 
                           username=session['username'], 
                           room_name=room['nome'],
                           room_id=room_id,
                           messages=get_messages_in_room(room_id))

# --- Nova Rota para Upload de Imagens ---
@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'user_id' not in session or 'current_room_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Gera um nome de arquivo único para evitar conflitos
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file_path = os.path.join(app.config['UPLOADS_FOLDER'], filename)
        file.save(file_path)
        
        # O caminho relativo para o cliente (web)
        image_url = url_for('static', filename=f'uploads/{filename}')
        
        user_id = session['user_id']
        room_id = session['current_room_id']

        # Salva a mensagem como tipo 'image' no banco de dados
        add_message(room_id, user_id, image_url, message_type='image')
        
        # Emite o evento 'new_message' para a sala com a URL da imagem
        message_data = {
            'username': session['username'],
            'message': image_url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'room_id': room_id,
            'type': 'image'
        }
        
        socketio.emit('new_message', message_data, room=f'room_{room_id}')
        
        return jsonify({'success': True, 'url': image_url})
    
    return jsonify({'error': 'Invalid file type'}), 400

# --- Rotas API (sem alterações) ---
@app.route('/api/rooms', methods=['GET'])
def get_rooms_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    rooms = get_rooms()
    room_list = []
    for room in rooms:
        active_count = get_active_users_in_room(room['id'])
        room_list.append({
            'id': room['id'],
            'name': room['nome'],
            'active_users': active_count
        })
    return jsonify(room_list)

@app.route('/api/rooms/<int:room_id>/join', methods=['POST'])
def join_room_api(room_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    room = get_room_by_id(room_id)
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    set_user_active_in_room(user_id, room_id)
    session['current_room_id'] = room_id
    session['current_room_name'] = room['nome']
    
    join_room_event_data = {
        'username': session['username'],
        'room_id': room_id,
        'message': f"{session['username']} entrou na sala.",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    emit('user_joined_room', join_room_event_data, room=f'room_{room_id}')
    
    return jsonify({'message': 'Successfully joined room', 'room_name': room['nome'], 'room_id': room_id})

# --- Eventos Socket.IO ---
@socketio.on('connect')
def handle_connect():
    print(f"Cliente conectado: {request.sid}")
    if 'user_id' in session and 'current_room_id' in session:
        user_id = session['user_id']
        room_id = session['current_room_id']
        username = session['username']
        
        join_room(f'room_{room_id}')
        set_user_active_in_room(user_id, room_id)
        
        join_event_data = {
            'username': username,
            'room_id': room_id,
            'message': f"{username} entrou na sala.",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        emit('user_joined_room', join_event_data, room=f'room_{room_id}')
        print(f"{username} reentrou na sala {room_id} via Socket.IO")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente desconectado: {request.sid}")
    if 'user_id' in session and 'current_room_id' in session:
        user_id = session['user_id']
        room_id = session['current_room_id']
        username = session['username']

        remove_user_from_room(user_id, room_id)
        
        leave_event_data = {
            'username': username,
            'room_id': room_id,
            'message': f"{username} saiu da sala.",
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        emit('user_left_room', leave_event_data, room=f'room_{room_id}')
        print(f"{username} saiu da sala {room_id} via Socket.IO")

        del session['current_room_id']
        del session['current_room_name']

@socketio.on('join_room_event')
def on_join_room_event(data):
    room_id = data.get('room_id')
    user_id = session.get('user_id')
    username = session.get('username')

    if not user_id or not room_id or not username:
        print("Erro: Informações incompletas para join_room_event")
        return

    room = get_room_by_id(room_id)
    if not room:
        print(f"Erro: Sala com ID {room_id} não encontrada no evento join_room_event.")
        return

    room_name_for_socket = f'room_{room_id}'
    join_room(room_name_for_socket)
    set_user_active_in_room(user_id, room_id)
    session['current_room_id'] = room_id
    session['current_room_name'] = room['nome']

    print(f"{username} juntou-se à sala {room_name_for_socket} via Socket.IO.")
    
    join_event_data = {
        'username': username,
        'room_id': room_id,
        'message': f"{username} entrou na sala.",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    emit('user_joined_room', join_event_data, room=room_name_for_socket, include_self=False)

@socketio.on('leave_room_event')
def on_leave_room_event(data):
    room_id = data.get('room_id')
    user_id = session.get('user_id')
    username = session.get('username')
    
    if not user_id or not room_id or not username:
        print("Erro: Informações incompletas para leave_room_event")
        return

    room_name_for_socket = f'room_{room_id}'
    leave_room(room_name_for_socket)
    remove_user_from_room(user_id, room_id)
    
    if 'current_room_id' in session and session['current_room_id'] == room_id:
        del session['current_room_id']
        del session['current_room_name']
    
    print(f"{username} saiu da sala {room_name_for_socket} via Socket.IO.")

    leave_event_data = {
        'username': username,
        'room_id': room_id,
        'message': f"{username} saiu da sala.",
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    emit('user_left_room', leave_event_data, room=room_name_for_socket)

@socketio.on('send_message')
def handle_send_message(data):
    user_id = session.get('user_id')
    username = session.get('username')
    room_id = data.get('room_id')
    message_content = data.get('message')

    if not user_id or not username or not room_id or not message_content:
        print("Erro: Informações incompletas para send_message")
        return
    
    # Adiciona a mensagem ao banco de dados com tipo 'text'
    add_message(room_id, user_id, message_content, message_type='text')
    
    # Prepara os dados para serem enviados aos outros clientes na sala.
    message_data = {
        'username': username,
        'message': message_content,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'room_id': room_id,
        'type': 'text' # Adicionado o tipo da mensagem
    }
    
    emit('new_message', message_data, room=f'room_{room_id}')

@socketio.on('get_active_users')
def handle_get_active_users(data):
    room_id = data.get('room_id')
    if room_id:
        active_count = get_active_users_in_room(room_id)
        emit('active_users_update', {'room_id': room_id, 'count': active_count})

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)