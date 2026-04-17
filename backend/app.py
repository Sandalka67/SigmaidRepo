import os
import secrets
import math
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database.models import db, User, EmergencySignal
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__,
            template_folder="../frontend/templates",
            static_folder="../frontend/static")

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sigmaid-super-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sigmaid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()


def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
    R = 6371.0 # Радиус на Земята в км
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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
    return render_template('index.html', stats=stats, has_active=bool(active_event))

@app.route('/map')
@login_required
def map_view():
    return render_template('map.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        if User.query.filter_by(email=email).first():
            return "Email already registered!", 400
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
        return "Invalid email or password.", 401
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

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message("Възстановяване на парола - Signaid", recipients=[email])
            msg.body = f"Кликнете на линка, за да смените паролата си: {reset_link}"
            mail.send(msg)
        return render_template('forgot_password.html', sent=True)
    return render_template('forgot_password.html', sent=False)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or user.reset_token_expiry < datetime.utcnow():
        return render_template('reset_password.html', invalid=True)
    if request.method == 'POST':
        user.set_password(request.form.get('password'))
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('reset_password.html', invalid=False, token=token)


@app.route('/api/signal', methods=['POST'])
@login_required
def create_signal():
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    conditions = data.get('conditions', 'Спешен случай')
    
    new_signal = EmergencySignal(
        user_id=current_user.id,
        lat=lat,
        lng=lng,
        is_active=True,
        emergency_causes=conditions,
        extra_details=data.get('notes', '')
    )
    db.session.add(new_signal)
    db.session.commit()
    all_users = User.query.filter(User.id != current_user.id).all()
    recipients = []
    
    for u in all_users:
        dist = calculate_distance(lat, lng, getattr(u, 'last_lat', None), getattr(u, 'last_lng', None))
        if dist <= 10.0 or dist == float('inf'):
            if u.email:
                recipients.append(u.email)
    
    if recipients:
        try:
            msg = Message(subject=f"🚨 SOS БЛИЗО ДО ВАС: {conditions}!", bcc=recipients)
            signaid_link = url_for('map_view', _external=True)
            google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
            
            msg.body = f"""
            ВНИМАНИЕ! Регистриран е сигнал за помощ близо до вас.
            
            ОТ: {current_user.full_name}
            ТИП: {conditions}
            БЕЛЕЖКИ: {data.get('notes', 'Няма')}
            
            📍 Виж в Signaid: {signaid_link}
            🌍 Отвори в Google Maps: {google_maps_link}
            """
            mail.send(msg)
        except Exception as e:
            print(f"Имейл грешка: {e}")

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
    signal_data = [{
        "lat": sig.lat, "lng": sig.lng,
        "user_name": sig.user.full_name if sig.user else 'Unknown',
        "phone": sig.user.phone if sig.user else 'N/A',
        "causes": sig.emergency_causes,
        "details": sig.extra_details
    } for sig in active_signals]
    return jsonify(signal_data)

if __name__ == '__main__':
    app.run(debug=True)