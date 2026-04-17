import os
import secrets
import math
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, abort
from database.models import db, User, EmergencySignal, Voucher
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@signaid.com").first():
        admin = User(full_name="Admin", email="admin@signaid.com", is_admin=True)
        admin.set_password("admin1234")
        db.session.add(admin)
        db.session.commit()
        print("\nADMIN CREATED: admin@signaid.com / admin1234\n")

    # Seed default vouchers
    if Voucher.query.count() == 0:
        vouchers = [
            Voucher(name="Coffee Voucher ☕", description="Free coffee at partner cafes", price=100, promo_code="COFFEE100"),
            Voucher(name="10% Pharmacy Discount 💊", description="10% off at partner pharmacies", price=200, promo_code="PHARMA10"),
            Voucher(name="Free First Aid Kit 🩺", description="Claim a free first aid kit", price=500, promo_code="AID500"),
            Voucher(name="Mountain Rescue Donation 🏔️", description="Donate to mountain rescue teams", price=150, promo_code="RESCUE150"),
            Voucher(name="Red Cross Donation ❤️", description="Support the Bulgarian Red Cross", price=300, promo_code="REDCROSS300"),
            Voucher(name="Premium Badge 🏅", description="Exclusive premium badge on your profile", price=250, promo_code="BADGE250"),
        ]
        for v in vouchers:
            db.session.add(v)
        db.session.commit()

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]:
        return float('inf')
    R = 6371.0
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

@app.route('/shop')
@login_required
def shop():
    vouchers = Voucher.query.all()
    return render_template('shop.html', vouchers=vouchers)

@app.route('/shop/buy/<int:voucher_id>', methods=['POST'])
@login_required
def buy_voucher(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    if current_user.points < voucher.price:
        flash('Not enough points!', 'danger')
        return redirect(url_for('shop'))
    current_user.points -= voucher.price
    db.session.commit()
    flash(f'🎉 Successfully redeemed "{voucher.name}"! Your promo code: {voucher.promo_code}', 'success')
    return redirect(url_for('shop'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            return "Email already registered!", 400
        new_user = User(email=email, full_name=request.form.get('full_name'), points=50, xp=50)
        new_user.set_password(request.form.get('password'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_panel'))
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
            try:
                msg = Message("Възстановяване на парола - Signaid", recipients=[email])
                msg.body = f"Кликнете на линка, за да смените паролата си: {reset_link}"
                mail.send(msg)
            except Exception as e:
                print(f"\n{'='*50}\nPASSWORD RESET LINK FOR {email}:\n{reset_link}\n{'='*50}\n")
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

# ── ADMIN ──
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    signals = EmergencySignal.query.order_by(EmergencySignal.timestamp.desc()).all()
    vouchers = Voucher.query.all()
    stats = get_stats()
    return render_template('admin.html', users=users, signals=signals, stats=stats, vouchers=vouchers)

@app.route('/admin/add-voucher', methods=['POST'])
@login_required
@admin_required
def admin_add_voucher():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    promo_code = request.form.get('promo_code')
    if name and price and promo_code:
        voucher = Voucher(name=name, description=description, price=int(price), promo_code=promo_code)
        db.session.add(voucher)
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-voucher/<int:voucher_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_voucher(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    db.session.delete(voucher)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-signal/<int:signal_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_signal(signal_id):
    signal = EmergencySignal.query.get_or_404(signal_id)
    db.session.delete(signal)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/resolve-signal/<int:signal_id>', methods=['POST'])
@login_required
@admin_required
def admin_resolve_signal(signal_id):
    signal = EmergencySignal.query.get_or_404(signal_id)
    signal.is_active = False
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return "Cannot delete admin!", 403
    EmergencySignal.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id:
        user.is_admin = not user.is_admin
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# ── API ──
@app.route('/api/signal', methods=['POST'])
@login_required
def create_signal():
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    conditions = data.get('conditions', 'Спешен случай')

    new_signal = EmergencySignal(
        user_id=current_user.id, lat=lat, lng=lng,
        is_active=True, emergency_causes=conditions,
        extra_details=data.get('notes', '')
    )
    db.session.add(new_signal)

    # Award points
    current_user.points = (current_user.points or 0) + 50
    current_user.xp = (current_user.xp or 0) + 50
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
            google_maps_link = f"https://www.google.com/maps?q={lat},{lng}"
            msg.body = f"ВНИМАНИЕ!\nОТ: {current_user.full_name}\nТИП: {conditions}\n🌍 {google_maps_link}"
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
        current_user.points = (current_user.points or 0) + 30
        current_user.xp = (current_user.xp or 0) + 30
        db.session.commit()
    return jsonify({"status": "resolved", "stats": get_stats()})

@app.route('/api/signals')
def get_signals():
    active_signals = EmergencySignal.query.filter_by(is_active=True).all()
    signal_data = [{
        "lat": sig.lat, "lng": sig.lng,
        "user_name": sig.user.full_name if sig.user else 'Unknown',
        "phone": sig.user.phone if sig.user else 'N/A',
        "email": sig.user.email if sig.user else 'N/A',
        "user_health": sig.user.health_conditions if sig.user and sig.user.health_conditions else 'None',
        "user_notes": sig.user.notes if sig.user and sig.user.notes else 'None',
        "causes": sig.emergency_causes if sig.emergency_causes else 'Not specified',
        "details": sig.extra_details if sig.extra_details else 'None',
        "timestamp": sig.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ') if sig.timestamp else None
    } for sig in active_signals]
    return jsonify(signal_data)

if __name__ == '__main__':
    app.run(debug=True)