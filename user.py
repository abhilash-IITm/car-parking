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
        details = request.form.get('details', '').strip()
        
        if not v_number or not details:
            flash('All fields are required.')
            return render_template('vehicle_register.html')

        if Vehicle.query.filter_by(v_number=v_number, user_id=session['user_id']).first():
            flash('Vehicle number already registered.')
            return render_template('vehicle_register.html')
        
        vehicle = Vehicle(v_number=v_number, details=details, user_id=session['user_id'])
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
        active_reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
        if active_reservation:
            flash('You have already parked at a spot.')
            return redirect(url_for('user_dashboard'))

        vehicle_id = request.form.get('vehicle_id')
        lot_id = request.form.get('lot_id')

        vehicle = Vehicle.query.filter_by(v_id=vehicle_id, user_id=user_id).first()
        lot = Lot.query.get(lot_id)

        if not vehicle or not lot:
            flash('Invalid vehicle or parking lot.')
            return redirect(url_for('user.park_vehicle'))

        occupied_spots_count = Spot.query.filter_by(lot_id=lot.lot_id, status='O').count()

        if occupied_spots_count >= lot.max_spots:
            flash('Parking lot full.')
            return redirect(url_for('user.park_vehicle'))

        available_spot = Spot.query.filter_by(lot_id=lot.lot_id, status='A').first()
        if not available_spot:
            flash('No available parking spots found.')
            return redirect(url_for('user.park_vehicle'))

        available_spot.status = 'O'

        reservation = Reservation(
            spot_id=available_spot.spot_id,
            lot_id=available_spot.lot_id,   # Only one lot_id here
            user_id=user_id,
            vehicle_id=vehicle.v_id,
            parking_timestamp=datetime.utcnow(),
            payment_status='Parked'
        )
        db.session.add(reservation)
        db.session.commit()

        flash('Vehicle parked successfully.')
        return redirect(url_for('user_dashboard'))

    lots = Lot.query.all()
    user_vehicles = Vehicle.query.filter_by(user_id=user_id).all()
    return render_template('parking.html', user=user, lots=lots, vehicles=user_vehicles)



@user_bp.route('/leave/<int:spot_id>', methods=['POST'])
def leave_spot(spot_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    spot = Spot.query.get(spot_id)
    if not spot:
        flash('Invalid spot.')
        return redirect(url_for('user_dashboard'))

    reservation = Reservation.query.filter_by(
        spot_id=spot_id,
        user_id=user_id,
        leaving_timestamp=None
    ).first()

    if not reservation:
        flash('No active reservation found for this spot.')
        return redirect(url_for('user_dashboard'))

    reservation.leaving_timestamp = datetime.utcnow()

    duration_minutes = (reservation.leaving_timestamp - reservation.parking_timestamp).total_seconds() / 60
    price_per_minute = spot.lot.price if spot.lot else 0

    reservation.amount = round(duration_minutes * price_per_minute, 2)
    reservation.payment_status = 'Pending'

    spot.status = 'A'

    db.session.commit()

    flash('You have successfully left the parking spot.')
    return redirect(url_for('user_dashboard'))


@user_bp.route('/pay/<int:reservation_id>', methods=['POST'])
def pay(reservation_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('auth.login'))

    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        flash('Reservation not found.')
        return redirect(url_for('user_dashboard'))

    payment_status = reservation.payment_status

    if payment_status == 'Parked':
        flash('You can only pay after you leave the spot')
        return redirect(url_for('user_dashboard'))


    if payment_status in ['Pending', 'Failed']:
        reservation.payment_status = 'Paid'
        db.session.commit()
        flash('Payment successful. Thank you!')
    else:
        flash(f'This reservation is already {reservation.payment_status}.')

    return redirect(url_for('user_dashboard'))