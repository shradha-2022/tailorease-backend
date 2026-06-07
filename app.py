# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from datetime import datetime, timedelta
# import sqlite3
# import uuid
# import os
# import json

# app = Flask(__name__, static_folder='.')
# CORS(app)

# # Database file
# DATABASE = 'tailorease.db'

# def init_db():
#     """Initialize SQLite database with all tables"""
#     conn = sqlite3.connect(DATABASE)
#     cursor = conn.cursor()
    
#     # Create bookings table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS bookings (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             order_id TEXT UNIQUE NOT NULL,
#             customer_name TEXT NOT NULL,
#             phone TEXT NOT NULL,
#             email TEXT,
#             city TEXT NOT NULL,
#             address TEXT NOT NULL,
#             garment_type TEXT NOT NULL,
#             service_type TEXT NOT NULL,
#             preferred_date TEXT NOT NULL,
#             time_slot TEXT NOT NULL,
#             special_instructions TEXT,
#             payment_method TEXT DEFAULT 'UPI / Online',
#             status TEXT DEFAULT 'Booking Confirmed',
#             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
#             updated_at TEXT DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
    
#     # Create order_status table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS order_status (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             order_id TEXT NOT NULL,
#             status_label TEXT NOT NULL,
#             status_time TEXT,
#             is_completed INTEGER DEFAULT 0,
#             FOREIGN KEY (order_id) REFERENCES bookings (order_id) ON DELETE CASCADE
#         )
#     ''')
    
#     # Create contact_messages table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS contact_messages (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL,
#             phone TEXT,
#             email TEXT,
#             message TEXT NOT NULL,
#             created_at TEXT DEFAULT CURRENT_TIMESTAMP
#         )
#     ''')
    
#     conn.commit()
    
#     # Check if we need to add sample data
#     cursor.execute('SELECT COUNT(*) FROM bookings')
#     count = cursor.fetchone()[0]
    
#     if count == 0:
#         # Add sample booking
#         sample_order_id = f"TE-{datetime.now().strftime('%Y%m%d')}-SAMP"
#         cursor.execute('''
#             INSERT INTO bookings (order_id, customer_name, phone, city, address, garment_type, service_type, preferred_date, time_slot, status)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (sample_order_id, 'Sample Customer', '9999999999', 'Bangalore', 'Sample Address', 'Blouse', 'Both', 
#               datetime.now().strftime('%Y-%m-%d'), '10:00 AM', 'Stitching in Progress'))
        
#         # Add statuses for sample
#         statuses = ['Booking Confirmed', 'Tailor Assigned', 'Measurements Taken', 'Fabric Picked Up', 
#                    'Stitching in Progress', 'Quality Check', 'Ready for Delivery', 'Out for Delivery', 'Delivered']
        
#         for i, status in enumerate(statuses):
#             is_done = i < 4  # First 4 are done
#             status_time = (datetime.now() - timedelta(days=5-i)).isoformat() if is_done else None
#             cursor.execute('''
#                 INSERT INTO order_status (order_id, status_label, status_time, is_completed)
#                 VALUES (?, ?, ?, ?)
#             ''', (sample_order_id, status, status_time, 1 if is_done else 0))
        
#         conn.commit()
#         print(f"✅ Added sample order: {sample_order_id}")
    
#     conn.close()
#     print("✅ Database initialized successfully!")

# def get_db():
#     conn = sqlite3.connect(DATABASE)
#     conn.row_factory = sqlite3.Row
#     return conn

# @app.route('/')
# def serve_index():
#     return send_from_directory('.', 'index.html')

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     return jsonify({'status': 'ok', 'message': 'TailorEase API is running', 'database': 'SQLite'}), 200

# @app.route('/api/bookings', methods=['POST'])
# def create_booking():
#     try:
#         data = request.json
        
#         # Generate unique order ID
#         order_id = f"TE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
#         conn = get_db()
#         cursor = conn.cursor()
        
#         # Insert booking
#         cursor.execute('''
#             INSERT INTO bookings (
#                 order_id, customer_name, phone, email, city, address, 
#                 garment_type, service_type, preferred_date, time_slot, 
#                 special_instructions, payment_method, status
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             order_id, 
#             data.get('customer_name'), 
#             data.get('phone'), 
#             data.get('email', ''),
#             data.get('city'), 
#             data.get('address'), 
#             data.get('garment_type'), 
#             data.get('service_type'),
#             data.get('preferred_date'), 
#             data.get('time_slot'), 
#             data.get('special_instructions', ''),
#             data.get('payment_method', 'UPI / Online'), 
#             'Booking Confirmed'
#         ))
        
#         # Add all statuses
#         statuses = ['Booking Confirmed', 'Tailor Assigned', 'Measurements Taken', 'Fabric Picked Up', 
#                    'Stitching in Progress', 'Quality Check', 'Ready for Delivery', 'Out for Delivery', 'Delivered']
        
#         for i, status in enumerate(statuses):
#             is_done = 1 if i == 0 else 0  # Only first status is done
#             status_time = datetime.now().isoformat() if i == 0 else None
#             cursor.execute('''
#                 INSERT INTO order_status (order_id, status_label, status_time, is_completed)
#                 VALUES (?, ?, ?, ?)
#             ''', (order_id, status, status_time, is_done))
        
#         conn.commit()
#         conn.close()
        
#         return jsonify({
#             'success': True,
#             'order_id': order_id,
#             'message': 'Booking created successfully'
#         }), 201
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/bookings/<order_id>', methods=['GET'])
# def get_booking(order_id):
#     try:
#         conn = get_db()
#         cursor = conn.cursor()
        
#         # Get booking
#         cursor.execute('SELECT * FROM bookings WHERE order_id = ?', (order_id,))
#         booking = cursor.fetchone()
        
#         if not booking:
#             conn.close()
#             return jsonify({'success': False, 'error': 'Order not found'}), 404
        
#         # Get status updates
#         cursor.execute('''
#             SELECT * FROM order_status 
#             WHERE order_id = ? 
#             ORDER BY id
#         ''', (order_id,))
#         statuses = cursor.fetchall()
        
#         timeline = []
#         active_found = False
#         for status in statuses:
#             is_done = bool(status['is_completed'])
#             is_active = False
#             if not is_done and not active_found:
#                 is_active = True
#                 active_found = True
            
#             timeline.append({
#                 'label': status['status_label'],
#                 'time': status['status_time'],
#                 'done': is_done,
#                 'active': is_active
#             })
        
#         conn.close()
        
#         booking_dict = dict(booking)
        
#         return jsonify({
#             'success': True,
#             'order': booking_dict,
#             'timeline': timeline
#         }), 200
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/contact', methods=['POST'])
# def submit_contact():
#     try:
#         data = request.json
        
#         conn = get_db()
#         cursor = conn.cursor()
        
#         cursor.execute('''
#             INSERT INTO contact_messages (name, phone, email, message)
#             VALUES (?, ?, ?, ?)
#         ''', (data['name'], data.get('phone', ''), data.get('email', ''), data['message']))
        
#         conn.commit()
#         conn.close()
        
#         return jsonify({'success': True, 'message': 'Message sent successfully'}), 201
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# @app.route('/api/stats', methods=['GET'])
# def get_stats():
#     try:
#         conn = get_db()
#         cursor = conn.cursor()
        
#         cursor.execute('SELECT COUNT(*) FROM bookings')
#         total = cursor.fetchone()[0]
        
#         thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
#         cursor.execute('''
#             SELECT COUNT(*) FROM bookings 
#             WHERE created_at >= ?
#         ''', (thirty_days_ago,))
#         recent = cursor.fetchone()[0]
        
#         conn.close()
        
#         return jsonify({
#             'success': True,
#             'total_bookings': total,
#             'recent_bookings': recent,
#             'base_customers': 2400 + total
#         }), 200
        
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# if __name__ == '__main__':
#     init_db()
#     print("\n" + "="*60)
#     print("🚀 TAILOREASE BACKEND SERVER")
#     print("="*60)
#     print(f"📁 Database: {os.path.abspath(DATABASE)}")
#     print(f"🌐 Server: http://localhost:5000")
#     print("\n📋 API Endpoints:")
#     print("   POST   http://localhost:5000/api/bookings  - Create booking")
#     print("   GET    http://localhost:5000/api/bookings/<id> - Track order")
#     print("   POST   http://localhost:5000/api/contact   - Send message")
#     print("   GET    http://localhost:5000/api/stats     - Get statistics")
#     print("\n💡 Sample Order ID to track: Check the console after creating a booking")
#     print("="*60 + "\n")
    
#     app.run(debug=True, port=5000)





# updated code
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import uuid
import os
import hashlib
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tailorease-super-secret-key-change-this'

# Configure CORS properly for Netlify
CORS(app, 
     origins=[
         "https://relaxed-dodol-6a31b9.netlify.app",
         "http://localhost:5000",
         "http://localhost:5500"
     ], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

DATABASE = 'tailorease.db'

def init_db():
    """Initialize database with correct schema"""
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
    
    # Bookings table with user_id column
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
    
    # Check if admin exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    admin_count = cursor.fetchone()[0]
    
    if admin_count == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password, email, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'admin@tailorease.com', 'Administrator', 'admin'))
        print("✅ Default admin created - Username: admin, Password: admin123")
    
    # Create default test user
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = "testuser"')
    user_count = cursor.fetchone()[0]
    
    if user_count == 0:
        user_password = hashlib.sha256('user123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, password, email, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('testuser', user_password, 'user@example.com', 'Test User', 'user'))
        print("✅ Default user created - Username: testuser, Password: user123")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============ ROOT ROUTE ============

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'TailorEase API is running!',
        'status': 'active',
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /api/health',
            'login': 'POST /api/auth/login',
            'register': 'POST /api/auth/register',
            'logout': 'POST /api/auth/logout',
            'me': 'GET /api/auth/me',
            'create_booking': 'POST /api/bookings',
            'my_bookings': 'GET /api/bookings/user',
            'track_order': 'GET /api/bookings/<order_id>',
            'admin_bookings': 'GET /api/admin/bookings',
            'update_status': 'PUT /api/admin/bookings/<order_id>/status',
            'contact': 'POST /api/contact',
            'stats': 'GET /api/stats'
        }
    })

# ============ HEALTH ROUTE ============

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({'status': 'ok', 'message': 'TailorEase API is running', 'database': 'SQLite'}), 200

# ============ AUTH ROUTES ============

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
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
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            return jsonify({
                'success': True,
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

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        full_name = data.get('full_name', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, full_name, 'user'))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Registration successful! Please login.'}), 201
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    if request.method == 'OPTIONS':
        return '', 200
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
def get_current_user():
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'full_name': session.get('full_name', ''),
                'role': session['role']
            }
        }), 200
    return jsonify({'success': False, 'error': 'Not logged in'}), 401

# ============ BOOKING ROUTES ============

@app.route('/api/bookings', methods=['POST', 'OPTIONS'])
def create_booking():
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
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
            order_id, session['user_id'], data.get('customer_name'), data.get('phone'), 
            data.get('email', ''), data.get('city'), data.get('address'), 
            data.get('garment_type'), data.get('service_type'), data.get('preferred_date'), 
            data.get('time_slot'), data.get('special_instructions', ''),
            data.get('payment_method', 'UPI / Online'), 'Booking Confirmed'
        ))
        
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

@app.route('/api/bookings/user', methods=['GET', 'OPTIONS'])
def get_user_bookings():
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],))
        bookings = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'bookings': [dict(b) for b in bookings]}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings/<order_id>', methods=['GET', 'OPTIONS'])
def get_booking(order_id):
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Please login first'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        if session.get('role') == 'admin':
            cursor.execute('SELECT * FROM bookings WHERE order_id = ?', (order_id,))
        else:
            cursor.execute('SELECT * FROM bookings WHERE order_id = ? AND user_id = ?', (order_id, session['user_id']))
        
        booking = cursor.fetchone()
        if not booking:
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
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

# ============ ADMIN ROUTES ============

@app.route('/api/admin/bookings', methods=['GET', 'OPTIONS'])
def admin_get_all_bookings():
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' not in session or session.get('role') != 'admin':
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

@app.route('/api/admin/bookings/<order_id>/status', methods=['PUT', 'OPTIONS'])
def admin_update_status(order_id):
    if request.method == 'OPTIONS':
        return '', 200
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    try:
        data = request.json
        new_status = data.get('status')
        notes = data.get('notes', '')
        expected_date = data.get('expected_completion_date', '')
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bookings 
            SET status = ?, updated_at = ?, admin_notes = ?, expected_completion_date = ?
            WHERE order_id = ?
        ''', (new_status, datetime.now().isoformat(), notes, expected_date, order_id))
        
        cursor.execute('''
            UPDATE order_status 
            SET is_completed = 1, status_time = ?, updated_by = ?, notes = ?
            WHERE order_id = ? AND status_label = ?
        ''', (datetime.now().isoformat(), session['username'], notes, order_id, new_status))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Status updated'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ OTHER ROUTES ============

@app.route('/api/contact', methods=['POST', 'OPTIONS'])
def submit_contact():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_messages (name, phone, email, message)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data.get('phone', ''), data.get('email', ''), data['message']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message sent successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
def get_stats():
    if request.method == 'OPTIONS':
        return '', 200
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

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("🚀 TAILOREASE BACKEND SERVER RUNNING")
    print("="*60)
    print("📍 http://localhost:5000")
    print("\n👤 Default Logins:")
    print("   Admin: admin / admin123")
    print("   User:  testuser / user123")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)