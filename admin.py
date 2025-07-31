from flask import Blueprint, render_template, redirect, url_for, flash, session, abort, request
from models import db, Lot, Spot, Reservation, User
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/parking_lot/create', methods=['GET', 'POST'])
def create_parking_lot():
    if session.get('role') != 'admin':
        flash('Access denied.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        location_name = request.form.get('location_name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots = request.form.get('max_spots')

        try:
            new_lot = Lot(
                location_name=location_name,
                price=float(price),
                address=address,
                pin_code=pin_code,
                max_spots=int(max_spots)
            )
            db.session.add(new_lot)
            db.session.flush()
            i = 0
            while i <= int(max_spots):
                new_spot = Spot(
                    lot_id = new_lot.lot_id,
                    status = 'A'
                )
                db.session.add(new_spot)
                i += 1
            db.session.commit()
            
            flash('Parking lot created successfully.')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating parking lot: {str(e)}')
            return render_template('create_lot.html')

    return render_template('create_lot.html')


@admin_bp.route('/lot/<int:lot_id>')
def lot_list(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('auth.login'))

    lot = Lot.query.get(lot_id)
    if not lot:
        abort(404)

    spots = Spot.query.filter_by(lot_id=lot_id).all()

    lot_vehicles = []
    for spot in spots:
        if spot.status == 'O':
            reservation = Reservation.query.filter_by(spot_id=spot.spot_id).first()
            username = reservation.user.username
            vehicle = reservation.vehicle.v_number
            details = reservation.vehicle.details
            parked_at = reservation.parking_timestamp
            time_parked = datetime.utcnow() - parked_at
            minutes_parked = max(int(time_parked.total_seconds() / 60), 0)
    
            revenue = round(minutes_parked * lot.price, 2)
    
            lot_vehicles.append({
                'vehicle_number': vehicle,
                'username': username,
                'details': details,
                'parked_at': parked_at,
                'minutes_parked': minutes_parked,
                'revenue': revenue
            })

    return render_template('lot_list.html', lot=lot, lot_vehicles=lot_vehicles)