from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
from datetime import datetime
# from ml_model.predict_advanced import predict_damage
from ml_model.predict_yolo import predict_damage
# Add these new imports (around line 8-10, after existing imports)
from ml_model.insurance_calculator import (
    calculate_insurance_claim,
    calculate_claim_probability,
    generate_insurance_report_data,
    INSURANCE_POLICIES
)
from ml_model.pdf_generator import generate_insurance_pdf












app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Shop profiles table
    c.execute('''CREATE TABLE IF NOT EXISTS shop_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        shop_name TEXT NOT NULL,
        address TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        is_approved INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Spare parts table
    c.execute('''CREATE TABLE IF NOT EXISTS spare_parts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER,
        part_name TEXT NOT NULL,
        price REAL NOT NULL,
        car_model TEXT,
        availability INTEGER DEFAULT 1,
        image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shop_profiles(id)
    )''')
    
    # Damage reports table
    c.execute('''CREATE TABLE IF NOT EXISTS damage_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        image_path TEXT NOT NULL,
        damaged_parts TEXT,
        total_cost REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Notifications table
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        shop_id INTEGER,
        part_name TEXT,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (shop_id) REFERENCES shop_profiles(id)
    )''')
    
    # Create default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        admin_password = generate_password_hash('admin123')
        c.execute("INSERT INTO users (username, email, password, user_type) VALUES (?, ?, ?, ?)",
                 ('admin', 'admin@system.com', admin_password, 'admin'))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper function to check login
def login_required(user_type=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if user_type and session.get('user_type') != user_type:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# ============================================================================
# ROUTES - General
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')  # 'user' or 'shop_owner'
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            c.execute("INSERT INTO users (username, email, password, user_type) VALUES (?, ?, ?, ?)",
                     (username, email, hashed_password, user_type))
            user_id = c.lastrowid
            
            # If shop owner, create shop profile
            if user_type == 'shop_owner':
                shop_name = data.get('shop_name')
                address = data.get('address')
                contact = data.get('contact_number')
                c.execute("INSERT INTO shop_profiles (user_id, shop_name, address, contact_number) VALUES (?, ?, ?, ?)",
                         (user_id, shop_name, address, contact))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Registration successful!'})
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'message': 'Username or email already exists!'})
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, password, user_type FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['user_type'] = user[2]
            
            if user[2] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[2] == 'shop_owner':
                return redirect(url_for('shop_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials!'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ============================================================================
# ROUTES - User Dashboard
# ============================================================================

@app.route('/user/dashboard')
@login_required('user')
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/api/upload_damage_image', methods=['POST'])
def upload_damage_image_updated():
    """Updated to handle binary classification results"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image uploaded'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No image selected'})
    
    if file:
        from datetime import datetime
        from werkzeug.utils import secure_filename
        import os
        
        filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Call updated AI model for prediction
        try:
            from ml_model.predict_advanced import predict_damage
            prediction_result = predict_damage(filepath)
            
            # Save to database
            import sqlite3, json
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("""INSERT INTO damage_reports 
                        (user_id, image_path, damaged_parts, total_cost) 
                        VALUES (?, ?, ?, ?)""",
                     (session['user_id'], filepath, 
                      json.dumps(prediction_result.get('damaged_parts', [])), 
                      prediction_result.get('total_cost', 0)))
            conn.commit()
            conn.close()
            
            # Format response
            return jsonify({
                'success': True,
                'is_damaged': prediction_result['is_damaged'],
                'confidence': prediction_result['confidence'],
                'damaged_parts': prediction_result.get('damaged_parts', []),
                'part_costs': prediction_result.get('part_costs', {}),
                'parts_total': prediction_result.get('parts_total', 0),
                'labor_cost': prediction_result.get('labor_cost', 0),
                'total_cost': prediction_result.get('total_cost', 0),
                'severity': prediction_result.get('severity', 'unknown'),
                'message': prediction_result.get('message', '')
            })
            
        except Exception as e:
            import traceback
            print(f"Prediction error: {e}")
            print(traceback.format_exc())
            return jsonify({
                'success': False, 
                'message': f'Prediction error: {str(e)}'
            })


@app.route('/api/get_all_parts', methods=['GET'])
def get_all_parts():
    search_query = request.args.get('search', '').lower()
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """
        SELECT sp.*, shop.shop_name, shop.address, shop.contact_number
        FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE shop.is_approved = 1 AND sp.availability = 1
    """
    
    if search_query:
        query += f" AND LOWER(sp.part_name) LIKE '%{search_query}%'"
    
    c.execute(query)
    parts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'parts': parts})


@app.route('/user/all-parts')
@login_required('user')
def all_parts_page():
    """Separate page for browsing all spare parts"""
    return render_template('all_parts.html')

@app.route('/api/shop/update_part', methods=['POST'])
@login_required('shop_owner')
def update_part():
    """Update spare part details"""
    data = request.get_json()
    part_id = data.get('part_id')
    part_name = data.get('part_name')
    price = data.get('price')
    car_model = data.get('car_model', '')
    availability = data.get('availability', 1)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Verify ownership
    c.execute("""
        SELECT sp.id FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE sp.id = ? AND shop.user_id = ?
    """, (part_id, session['user_id']))
    
    if not c.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized or part not found'})
    
    # Update part
    c.execute("""
        UPDATE spare_parts 
        SET part_name = ?, price = ?, car_model = ?, availability = ?
        WHERE id = ?
    """, (part_name, float(price), car_model, availability, part_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Part updated successfully!'})


@app.route('/api/search_parts_by_damage', methods=['POST'])
def search_parts_by_damage():
    data = request.get_json()
    damaged_parts = data.get('damaged_parts', [])
    
    if not damaged_parts:
        return jsonify({'success': False, 'message': 'No damaged parts provided'})
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Create placeholders for SQL IN clause
    placeholders = ','.join(['?' for _ in damaged_parts])
    query = f"""
        SELECT sp.*, shop.shop_name, shop.address, shop.contact_number
        FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE shop.is_approved = 1 AND sp.availability = 1
        AND LOWER(sp.part_name) IN ({','.join(['?' for _ in damaged_parts])})
    """
    
    c.execute(query, [part.lower() for part in damaged_parts])
    parts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'parts': parts})

@app.route('/api/notify_shop', methods=['POST'])
@login_required('user')
def notify_shop():
    data = request.get_json()
    shop_id = data.get('shop_id')
    part_name = data.get('part_name')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get user details
    c.execute("SELECT username, email FROM users WHERE id=?", (session['user_id'],))
    user_info = c.fetchone()
    
    message = f"User {user_info[0]} ({user_info[1]}) is interested in: {part_name}"
    
    c.execute("INSERT INTO notifications (user_id, shop_id, part_name, message) VALUES (?, ?, ?, ?)",
             (session['user_id'], shop_id, part_name, message))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Shop owner notified successfully!'})






# ============================================================================
# ROUTES - Shop Owner Dashboard
# ============================================================================

@app.route('/shop/dashboard')
@login_required('shop_owner')
def shop_dashboard():
    return render_template('shop_dashboard.html')

@app.route('/api/shop/get_profile', methods=['GET'])
@login_required('shop_owner')
def get_shop_profile():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM shop_profiles WHERE user_id=?", (session['user_id'],))
    profile = dict(c.fetchone())
    conn.close()
    return jsonify({'success': True, 'profile': profile})

@app.route('/api/shop/upload_part', methods=['POST'])
@login_required('shop_owner')
def upload_part():
    # Get shop_id
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM shop_profiles WHERE user_id=?", (session['user_id'],))
    shop_id = c.fetchone()[0]
    
    part_name = request.form.get('part_name')
    price = request.form.get('price')
    car_model = request.form.get('car_model', '')
    
    # Handle image upload
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(f"part_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = filepath
    
    c.execute("INSERT INTO spare_parts (shop_id, part_name, price, car_model, image_path) VALUES (?, ?, ?, ?, ?)",
             (shop_id, part_name, float(price), car_model, image_path))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Part uploaded successfully!'})

@app.route('/api/shop/get_parts', methods=['GET'])
@login_required('shop_owner')
def get_shop_parts():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT sp.* FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE shop.user_id=?
    """, (session['user_id'],))
    parts = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'parts': parts})

@app.route('/api/shop/get_notifications', methods=['GET'])
@login_required('shop_owner')
def get_shop_notifications():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT n.*, u.username, u.email FROM notifications n
        JOIN users u ON n.user_id = u.id
        JOIN shop_profiles shop ON n.shop_id = shop.id
        WHERE shop.user_id=?
        ORDER BY n.created_at DESC
    """, (session['user_id'],))
    notifications = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'notifications': notifications})


@login_required('shop_owner')
def delete_part():
    """Delete spare part"""
    data = request.get_json()
    part_id = data.get('part_id')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Verify ownership
    c.execute("""
        SELECT sp.id, sp.image_path 
        FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE sp.id = ? AND shop.user_id = ?
    """, (part_id, session['user_id']))

    result = c.fetchone()
    if not result:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Unauthorized or part not found'
        })

    # Delete part from DB
    c.execute("DELETE FROM spare_parts WHERE id = ?", (part_id,))
    conn.commit()
    conn.close()

    # Delete image file if exists
    if result[1] and os.path.exists(result[1]):
        try:
            os.remove(result[1])
        except Exception:
            pass

    return jsonify({
        'success': True,
        'message': 'Part deleted successfully!'
    })

# ============================================================================
# ROUTES - Admin Dashboard
# ============================================================================

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/api/admin/get_users', methods=['GET'])
@login_required('admin')
def get_all_users():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username, email, user_type, created_at FROM users WHERE user_type != 'admin'")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/get_shops', methods=['GET'])
@login_required('admin')
def get_all_shops():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT shop.*, u.username, u.email FROM shop_profiles shop
        JOIN users u ON shop.user_id = u.id
    """)
    shops = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'shops': shops})

@app.route('/api/admin/approve_shop', methods=['POST'])
@login_required('admin')
def approve_shop():
    data = request.get_json()
    shop_id = data.get('shop_id')
    is_approved = data.get('is_approved', 1)
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE shop_profiles SET is_approved=? WHERE id=?", (is_approved, shop_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Shop status updated!'})

@app.route('/api/admin/delete_part', methods=['POST'])
@login_required('admin')
def delete_part():
    data = request.get_json()
    part_id = data.get('part_id')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM spare_parts WHERE id=?", (part_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Part deleted successfully!'})

@app.route('/api/admin/get_all_parts', methods=['GET'])
@login_required('admin')
def admin_get_all_parts():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT sp.*, shop.shop_name FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
    """)
    parts = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify({'success': True, 'parts': parts})


    # ============================================================================
# INSURANCE ROUTES - ADD THESE AT THE END OF YOUR ROUTES
# ============================================================================

@app.route('/api/calculate_insurance', methods=['POST'])
def calculate_insurance():
    """Calculate insurance claim breakdown"""
    try:
        data = request.get_json()
        
        total_cost = data.get('total_cost', 0)
        policy_type = data.get('policy_type', 'comprehensive')
        severity = data.get('severity', 'moderate')
        num_damaged_parts = data.get('num_damaged_parts', 0)
        
        # Calculate insurance breakdown
        insurance_calc = calculate_insurance_claim(
            total_cost, policy_type, severity, num_damaged_parts
        )
        
        # Calculate claim probability
        claim_prob = calculate_claim_probability(
            severity, num_damaged_parts, total_cost, policy_type
        )
        
        return jsonify({
            'success': True,
            'insurance': insurance_calc,
            'claim_probability': claim_prob
        })
        
    except Exception as e:
        print(f"Error calculating insurance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/generate_insurance_pdf', methods=['POST'])
def generate_insurance_pdf_route():
    """Generate insurance claim PDF report"""
    try:
        data = request.get_json()
        
        # Extract data
        prediction_result = data.get('prediction_result', {})
        insurance_calc = data.get('insurance_calc', {})
        claim_probability = data.get('claim_probability', {})
        user_info = data.get('user_info', {})
        vehicle_info = data.get('vehicle_info', {})
        
        # Generate report data
        report_data = generate_insurance_report_data(
            prediction_result,
            insurance_calc,
            claim_probability,
            user_info,
            vehicle_info
        )
        
        # Generate PDF
        pdf_filename = f"insurance_claim_{report_data['report_id']}.pdf"
        pdf_path = os.path.join('static', 'reports', pdf_filename)
        
        # Ensure reports directory exists
        os.makedirs(os.path.join('static', 'reports'), exist_ok=True)
        
        # Generate PDF
        generate_insurance_pdf(report_data, pdf_path)
        
        return jsonify({
            'success': True,
            'pdf_url': f'/static/reports/{pdf_filename}',
            'report_id': report_data['report_id']
        })
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/get_insurance_policies', methods=['GET'])
def get_insurance_policies():
    """Get available insurance policy types"""
    return jsonify({
        'success': True,
        'policies': INSURANCE_POLICIES
    })




if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/api/get_parts_with_location', methods=['GET'])
def get_parts_with_location():
    """Get all parts with shop location for distance calculation"""
    search_query = request.args.get('search', '').lower()
    user_lat = request.args.get('lat', type=float)
    user_lng = request.args.get('lng', type=float)
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = """
        SELECT sp.*, shop.shop_name, shop.address, shop.contact_number
        FROM spare_parts sp
        JOIN shop_profiles shop ON sp.shop_id = shop.id
        WHERE shop.is_approved = 1 AND sp.availability = 1
    """
    
    if search_query:
        query += f" AND LOWER(sp.part_name) LIKE '%{search_query}%'"
    
    c.execute(query)
    parts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    # Add distance calculation if user location provided
    if user_lat and user_lng:
        from math import radians, sin, cos, sqrt, atan2
        
        def calculate_distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two points using Haversine formula"""
            R = 6371  # Earth's radius in kilometers
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            return round(distance, 2)
        
        # For demo: assign random coordinates near user
        # In production, you'd store shop coordinates in database
        import random
        for part in parts:
            # Generate random nearby coordinates (within ~10km)
            shop_lat = user_lat + random.uniform(-0.1, 0.1)
            shop_lng = user_lng + random.uniform(-0.1, 0.1)
            part['distance_km'] = calculate_distance(user_lat, user_lng, shop_lat, shop_lng)
    
    return jsonify({'success': True, 'parts': parts})