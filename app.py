import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Lot, Spot, Reservation, Vehicle
from auth import auth_bp
from user import user_bp
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)


@app.route('/')
def home():
    return redirect(url_for('auth.login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('auth.login'))

    admin_user = User.query.filter_by(username=session.get('username')).first()

    total_wheels_occupied = db.session.query(db.func.sum(Spot.no_of_wheels)).scalar() or 0

    total_max_wheels = db.session.query(db.func.sum(Lot.max_wheels)).scalar() or 1  # avoid div zero

    occupancy_percent = round((total_wheels_occupied / total_max_wheels) * 100, 2)

    revenue_per_minute = 5
    parking_lots = []
    lots = Lot.query.all()
    for lot in lots:
        occupied_wheels = db.session.query(db.func.sum(Spot.no_of_wheels)).filter(Spot.lot_id == lot.id).scalar() or 0
        revenue_per_minute += lot.price * occupied_wheels
        parking_lots.append({
            "location_name": lot.location_name,
            "pin_code": lot.pin_code,
            "occupied_wheels": occupied_wheels,
            "max_wheels": lot.max_wheels
        })

    return render_template(
        'admin_dashboard.html',
        name=admin_user.u_name or admin_user.username,
        username=admin_user.username,
        total_wheels_occupied=total_wheels_occupied,
        occupancy_percent=occupancy_percent,
        revenue_per_minute=round(revenue_per_minute, 2),
        parking_lots=parking_lots
    )

@app.route('/admin/parking_lot/create', methods=['GET', 'POST'])
def create_parking_lot():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        location_name = request.form.get('location_name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_wheels = request.form.get('max_wheels')

        new_lot = Lot(
            location_name=location_name,
            price=float(price),
            address=address,
            pin_code=pin_code,
            max_wheels=int(max_wheels)
        )
        db.session.add(new_lot)
        db.session.commit()
        flash('Parking lot created successfully.')
        return redirect(url_for('admin_dashboard')) 

    return render_template('create_lot.html')

@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash('Access denied.')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))

    active_spot = Spot.query.filter_by(user_id=user_id).first()
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()
    
    total_time = timedelta()
    total_paid = 0
    for res in reservations:
        if res.leaving_timestamp is not None:
            total_time += res.leaving_timestamp - res.parking_timestamp
        else:
            continue

        if res.payment_status == 'Paid':
            total_paid += res.amount
    
    total_minutes = int(total_time.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60



    
    total_time_parked = f"{hours}h {minutes:02d}m"
    total_amount_paid = f"${total_paid}"
    total_bookings = len(reservations)

    return render_template(
        'user_dashboard.html',
        user=user,
        active_spot=active_spot,
        reservations=reservations,
        total_time_parked=total_time_parked,
        total_amount_paid=total_amount_paid,
        total_bookings=total_bookings
    )

if __name__ == '__main__':
    app.run(debug=True)
