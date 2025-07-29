import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Lot, Spot, Reservation, Vehicle
from auth import auth_bp
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(auth_bp)


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

    user = User.query.filter_by(username=session.get('username')).first()
    # You can add more user-specific reservation or parking info here, e.g. active spots or history.

    active_spots = Spot.query.filter_by(user_id=user.id).all()
    reservations = Reservation.query.filter_by(user_id=user.id).all()

    return render_template('user_dashboard.html',
                            user=user,
                            active_spots=active_spots,
                            reservations=reservations)


# Parking a vehicle (simplified example)
# @app.route('/park', methods=['POST'])
# def park_vehicle():
#     if 'user_id' not in session:
#         flash('Please login first.')
#         return redirect(url_for('auth.login'))

#     user_id = session['user_id']
#     vehicle_id = request.form.get('vehicle_id')
#     lot_id = request.form.get('lot_id')

#     vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
#     lot = Lot.query.get(lot_id)

#     if not vehicle or not lot:
#         flash('Invalid vehicle or lot selected.')
#         return redirect(url_for('user_dashboard'))

#     # Check available wheels capacity
#     current_occupied_wheels = db.session.query(db.func.sum(Spot.no_of_wheels)).filter(Spot.lot_id == lot_id).scalar() or 0

#     if current_occupied_wheels + vehicle.wheels_no > lot.max_wheels:
#         flash('Parking lot is full for your vehicle’s wheels count.')
#         return redirect(url_for('user_dashboard'))

#     # Create Spot record representing parked vehicle
#     spot = Spot(lot_id=lot.id, user_id=user_id, vehicle_id=vehicle.id, no_of_wheels=vehicle.wheels_no)
#     db.session.add(spot)

#     # Create Reservation record with pending payment & leaving_timestamp = None initially
#     reservation = Reservation(
#         lot_id=lot.id,
#         user_id=user_id,
#         vehicle_id=vehicle.id,
#         wheels_occupied=vehicle.wheels_no,
#         parking_timestamp=datetime.utcnow(),
#         payment_status='Pending'
#     )
#     db.session.add(reservation)
#     db.session.commit()

#     flash('Vehicle parked successfully.')
#     return redirect(url_for('user_dashboard'))


# # Vacate spot / leave parking
# @app.route('/leave/<int:spot_id>', methods=['POST'])
# def leave_spot(spot_id):
#     spot = Spot.query.get(spot_id)

#     # Check ownership or admin rights here as needed

#     if not spot:
#         flash('Invalid spot.')
#         return redirect(url_for('user_dashboard'))

#     # Find active reservation for this spot (w/o leaving timestamp)
#     reservation = Reservation.query.filter_by(
#         lot_id=spot.lot_id,
#         user_id=spot.user_id,
#         vehicle_id=spot.vehicle_id,
#         leaving_timestamp=None
#     ).order_by(Reservation.parking_timestamp.desc()).first()

#     if reservation:
#         reservation.leaving_timestamp = datetime.utcnow()
#         duration_minutes = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 60

#         lot_price = spot.lot.price
#         reservation.amount = round(duration_minutes * lot_price, 2)
#         reservation.payment_status = 'Pending'  # Update as payment processed
#     else:
#         flash('No active reservation found.')

#     db.session.delete(spot)
#     db.session.commit()

#     flash('You have successfully left the parking spot.')
#     return redirect(url_for('user_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
