from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, Admin, Room, Guest, Booking
from config import HOTEL_NAME
from datetime import datetime
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change to a secure random key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def index():
    rooms = Room.query.all()
    bookings = Booking.query.all()
    return render_template('index.html', rooms=rooms, bookings=bookings, hotel_name=HOTEL_NAME)

@app.route('/rooms', methods=['GET', 'POST'])
@login_required
def rooms():
    if request.method == 'POST':
        number = request.form['number']
        type_ = request.form['type']
        price = float(request.form['price'])
        new_room = Room(number=number, type=type_, price=price)
        db.session.add(new_room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('rooms'))
    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms, hotel_name=HOTEL_NAME)

@app.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    if request.method == 'POST':
        guest_name = request.form['guest_name']
        guest_email = request.form['guest_email']
        room_id = int(request.form['room_id'])
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        
        room = Room.query.get(room_id)
        if not room.available:
            flash('Room not available!', 'danger')
            return redirect(url_for('bookings'))
        
        guest = Guest.query.filter_by(email=guest_email).first()
        if not guest:
            guest = Guest(name=guest_name, email=guest_email)
            db.session.add(guest)
            db.session.commit()
        
        booking = Booking(guest_id=guest.id, room_id=room_id, check_in=check_in, check_out=check_out)
        room.available = False
        db.session.add(booking)
        db.session.commit()
        flash('Booking created successfully!', 'success')
        return redirect(url_for('bookings'))
    
    bookings = Booking.query.all()
    rooms = Room.query.filter_by(available=True).all()
    return render_template('bookings.html', bookings=bookings, rooms=rooms, hotel_name=HOTEL_NAME)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('index'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html', hotel_name=HOTEL_NAME)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if Admin.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        admin = Admin(email=email)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', hotel_name=HOTEL_NAME)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)