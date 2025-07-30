from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Vehicle, User, Lot, Spot, Reservation
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/vehicle/register', methods=['GET', 'POST'])
def register_vehicle():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        v_number = request.form.get('v_number', '').strip().upper()
        wheels_no = request.form.get('wheels_no', '').strip()
        
        if not v_number or not wheels_no.isdigit():
            flash('All fields are required.')
            return render_template('vehicle_register.html')
        
        wheels_no = int(wheels_no)
        if wheels_no < 2 or wheels_no > 18:
            flash('Number of wheels must be between 2 and 18.')
            return render_template('vehicle_register.html')

        # Check for duplicate vehicle for this user
        if Vehicle.query.filter_by(v_number=v_number, user_id=session['user_id']).first():
            flash('Vehicle number already registered.')
            return render_template('vehicle_register.html')
        
        vehicle = Vehicle(v_number=v_number, wheels_no=wheels_no, user_id=session['user_id'])
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle registered successfully.')
        return redirect(url_for('user_dashboard'))

    return render_template('vehicle_register.html')


@user_bp.route('/park', methods=['GET', 'POST'])
def park_vehicle():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        lot_id = request.form.get('lot_id')

        vehicle = Vehicle.query.filter_by(id=vehicle_id, user_id=user_id).first()
        lot = Lot.query.get(lot_id)

        if not vehicle or not lot:
            flash('Invalid vehicle or parking lot.')
            return redirect(url_for('user.park_vehicle'))

        current_wheels = db.session.query(db.func.sum(Spot.no_of_wheels)).filter(Spot.lot_id == lot_id).scalar() or 0

        if current_wheels + vehicle.wheels_no > lot.max_wheels:
            flash('Parking lot full for your vehicle’s wheels.')
            return redirect(url_for('user.park_vehicle'))

        new_spot = Spot(
            lot_id=lot.id,
            user_id=user_id,
            vehicle_id=vehicle.id,
            no_of_wheels=vehicle.wheels_no,
            parked_at=datetime.utcnow()
        )
        db.session.add(new_spot)

        reservation = Reservation(
            lot_id=lot.id,
            user_id=user_id,
            vehicle_id=vehicle.id,
            wheels_occupied=vehicle.wheels_no,
            parking_timestamp=new_spot.parked_at,
            payment_status='Pending'
        )
        db.session.add(reservation)
        db.session.commit()

        flash('Vehicle parked successfully.')
        return redirect(url_for('user_dashboard'))

    lots = Lot.query.all()
    return render_template('parking.html', user=user, lots=lots)


@user_bp.route('/leave/<int:spot_id>', methods=['POST'])
def leave_spot(spot_id):
    spot = Spot.query.get(spot_id)
    if not spot or spot.user_id != session.get('user_id'):
        flash('Invalid spot or unauthorized action.')
        return redirect(url_for('user_dashboard'))

    reservation = Reservation.query.filter_by(
        lot_id=spot.lot_id,
        user_id=spot.user_id,
        vehicle_id=spot.vehicle_id,
        leaving_timestamp=None
    ).order_by(Reservation.parking_timestamp.desc()).first()

    if reservation:
        reservation.leaving_timestamp = datetime.utcnow()
        duration = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 60
        price_per_minute = spot.lot.price
        reservation.amount = round(duration * price_per_minute, 2)
        reservation.payment_status = 'Pending'
    else:
        flash('No active reservation found.')

    db.session.delete(spot)
    db.session.commit()

    flash('You have successfully left the parking spot.')
    return redirect(url_for('user_dashboard'))


@user_bp.route('/pay/<int:reservation_id>', methods=['POST'])
def pay(reservation_id):

    reservation = Reservation.query.get(reservation_id)
    if reservation.payment_status.lower() in ['pending', 'failed']:
        reservation.payment_status = 'Paid'
        db.session.commit()
        flash('Payment successful. Thank you!')
    else:
        flash(f'This reservation is already {reservation.payment_status}.')

    return redirect(url_for('user_dashboard'))