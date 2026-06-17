from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import uuid
import os
import hashlib
import jwt
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key-change-this')

# ✅ SIMPLEST AND MOST RELIABLE CORS CONFIGURATION
CORS(app, resources={r"/*": {"origins": "*"}})

# Use /tmp/ for SQLite on Render
DATABASE = '/tmp/tailorease.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            garment_type TEXT NOT NULL,
            service_type TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            special_instructions TEXT,
            payment_method TEXT DEFAULT 'UPI / Online',
            status TEXT DEFAULT 'Booking Confirmed',
            admin_notes TEXT,
            expected_completion_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Order status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            status_label TEXT NOT NULL,
            status_time TEXT,
            is_completed INTEGER DEFAULT 0,
            updated_by TEXT,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES bookings (order_id) ON DELETE CASCADE
        )
    ''')
    # Contact messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Create default users
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?)',
                       ('admin', admin_password, 'admin@tailorease.com', 'Administrator', 'admin'))
        print("✅ Admin created - admin/admin123")

    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "testuser"')
    if cursor.fetchone()[0] == 0:
        user_password = hashlib.sha256('user123'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?)',
                       ('testuser', user_password, 'user@example.com', 'Test User', 'user'))
        print("✅ User created - testuser/user123")

    conn.commit()
    conn.close()
    print("✅ Database initialized!")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'error': 'Token missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user']
        except:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# --- API Routes ---

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'TailorEase API running!', 'status': 'active'})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'TailorEase API is running'}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
        user = cursor.fetchone()
        conn.close()

        if user:
            token = jwt.encode({
                'user': {
                    'id': user['id'], 
                    'username': user['username'], 
                    'full_name': user['full_name'], 
                    'role': user['role']
                },
                'exp': datetime.utcnow() + timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'role': user['role']
                }
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email, full_name, role) VALUES (?, ?, ?, ?, ?)',
                           (username, hashed_password, data.get('email', ''), data.get('full_name', ''), 'user'))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Registration successful!'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    try:
        data = request.json
        order_id = f"TE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bookings (
                order_id, user_id, customer_name, phone, email, city, address, 
                garment_type, service_type, preferred_date, time_slot, 
                special_instructions, payment_method, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, 
            current_user['id'], 
            data.get('customer_name'), 
            data.get('phone'), 
            data.get('email', ''), 
            data.get('city'), 
            data.get('address'), 
            data.get('garment_type'), 
            data.get('service_type'), 
            data.get('preferred_date'), 
            data.get('time_slot'), 
            data.get('special_instructions', ''), 
            data.get('payment_method', 'UPI / Online'), 
            'Booking Confirmed'
        ))
        
        # Add initial statuses
        statuses = ['Booking Confirmed', 'Tailor Assigned', 'Measurements Taken', 'Fabric Picked Up', 
                   'Stitching in Progress', 'Quality Check', 'Ready for Delivery', 'Out for Delivery', 'Delivered']
        
        for i, status in enumerate(statuses):
            is_done = 1 if i == 0 else 0
            status_time = datetime.now().isoformat() if i == 0 else None
            cursor.execute('''
                INSERT INTO order_status (order_id, status_label, status_time, is_completed)
                VALUES (?, ?, ?, ?)
            ''', (order_id, status, status_time, is_done))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'order_id': order_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings/user', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC', (current_user['id'],))
        bookings = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'bookings': [dict(b) for b in bookings]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings/<order_id>', methods=['GET'])
@token_required
def get_booking(current_user, order_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if current_user.get('role') == 'admin':
            cursor.execute('SELECT * FROM bookings WHERE order_id = ?', (order_id,))
        else:
            cursor.execute('SELECT * FROM bookings WHERE order_id = ? AND user_id = ?', (order_id, current_user['id']))
        
        booking = cursor.fetchone()
        if not booking:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Get timeline
        cursor.execute('SELECT * FROM order_status WHERE order_id = ? ORDER BY id', (order_id,))
        statuses = cursor.fetchall()
        
        timeline = []
        active_found = False
        for status in statuses:
            is_done = bool(status['is_completed'])
            is_active = False
            if not is_done and not active_found:
                is_active = True
                active_found = True
            timeline.append({
                'label': status['status_label'],
                'time': status['status_time'],
                'done': is_done,
                'active': is_active,
                'notes': status['notes'] if status['notes'] else None
            })
        
        conn.close()
        return jsonify({'success': True, 'order': dict(booking), 'timeline': timeline}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/bookings', methods=['GET'])
@token_required
def admin_get_all_bookings(current_user):
    if current_user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
        bookings = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'bookings': [dict(b) for b in bookings]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/bookings/<order_id>/status', methods=['PUT'])
@token_required
def admin_update_status(current_user, order_id):
    if current_user.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE bookings SET status = ?, updated_at = ? WHERE order_id = ?', 
                      (new_status, datetime.now().isoformat(), order_id))
        
        cursor.execute('''
            UPDATE order_status 
            SET is_completed = 1, status_time = ?, updated_by = ?, notes = ? 
            WHERE order_id = ? AND status_label = ?
        ''', (datetime.now().isoformat(), current_user['username'], notes, order_id, new_status))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Status updated'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO contact_messages (name, phone, email, message) VALUES (?, ?, ?, ?)',
                       (data['name'], data.get('phone', ''), data.get('email', ''), data['message']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message sent'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM bookings')
        total = cursor.fetchone()[0]
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM bookings WHERE created_at >= ?', (thirty_days_ago,))
        recent = cursor.fetchone()[0]
        
        conn.close()
        return jsonify({
            'success': True, 
            'total_bookings': total, 
            'recent_bookings': recent,
            'base_customers': 2400 + total
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"\n🚀 TAILOREASE BACKEND RUNNING on port {port}")
    print("👤 Admin: admin / admin123")
    print("👤 User: testuser / user123\n")
    app.run(debug=False, host='0.0.0.0', port=port)
