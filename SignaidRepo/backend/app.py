import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database.models import db, User, EmergencySignal
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")

app.config['SECRET_KEY'] = 'sigmaid-super-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sigmaid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.first():
        demo_user = User(
            full_name="Demo User",
            email="demo@test.com",
            phone="555-0199",
            health_conditions="Heart Disease, Hypertension",
            notes="Allergic to Penicillin. Takes blood thinners."
        )
        demo_user.set_password("1234")
        db.session.add(demo_user)
        db.session.commit()

def get_stats():
    return {
        "users": User.query.count(),
        "total_signals": EmergencySignal.query.count(),
        "active_signals": EmergencySignal.query.filter_by(is_active=True).count(),
        "resolved": EmergencySignal.query.filter_by(is_active=False).count()
    }

@app.route('/')
@login_required
def index():
    stats = get_stats()
    active_event = EmergencySignal.query.filter_by(user_id=current_user.id, is_active=True).first()
    has_active = True if active_event else False
    
    return render_template('index.html', stats=stats, has_active=has_active)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        if User.query.filter_by(email=email).first():
            return "Email already registered! Go back and log in.", 400
            
        new_user = User(email=email, full_name=full_name)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
            
        return "Invalid email or password. Please try again.", 401
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.phone = request.form.get('phone')
        current_user.health_conditions = request.form.get('health_conditions')
        current_user.notes = request.form.get('notes')

        db.session.commit()
        
        return redirect(url_for('profile'))
        
    return render_template('profile.html')

@app.route('/api/signal', methods=['POST'])
@login_required
def create_signal():
    data = request.json
    
    new_signal = EmergencySignal(
        user_id=current_user.id,
        lat=data['lat'],
        lng=data['lng'],
        is_active=True,
        emergency_causes=data.get('conditions', ''),
        extra_details=data.get('notes', '')
    )
    db.session.add(new_signal)
    db.session.commit()
    
    return jsonify({"status": "created", "stats": get_stats()})

@app.route('/api/resolve', methods=['POST'])
@login_required
def resolve_signal():
    active_signal = EmergencySignal.query.filter_by(user_id=current_user.id, is_active=True).first()
    if active_signal:
        active_signal.is_active = False
        db.session.commit()
        
    return jsonify({"status": "resolved", "stats": get_stats()})

@app.route('/api/signals')
def get_signals():
    active_signals = EmergencySignal.query.filter_by(is_active=True).all()
    signal_data = []
    
    for sig in active_signals:
        u = sig.user 
        signal_data.append({
            "lat": sig.lat,
            "lng": sig.lng,
            "user_name": u.full_name if u else 'Unknown',
            "phone": u.phone if u else 'N/A',
            "email": u.email if u else 'N/A',
            "user_health": u.health_conditions if u and u.health_conditions else 'None',
            "user_notes": u.notes if u and u.notes else 'None',
            "causes": sig.emergency_causes if sig.emergency_causes else 'Not specified',
            "details": sig.extra_details if sig.extra_details else 'None',
            "timestamp": sig.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') if sig.timestamp else None
        })
        
    return jsonify(signal_data)

if __name__ == '__main__':
    app.run(debug=True)