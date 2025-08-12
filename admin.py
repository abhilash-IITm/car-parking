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

@admin_bp.route('/lot/<int:lot_id>/edit', methods=['GET', 'POST'])
def edit_parking_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('auth.login'))

    lot = Lot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        try:
            new_max_spots = int(request.form['max_spots'])
            new_price = float(request.form['price'])
            new_address = request.form['address'].strip()
        except (ValueError, KeyError):
            flash('Invalid input detected. Please check your entries.')
            return render_template('edit_lot.html', lot=lot)

        
        lot.price = new_price
        lot.address = new_address

        
        if new_max_spots > lot.max_spots:
            num_new_spots = new_max_spots - lot.max_spots
            for _ in range(num_new_spots):
                new_spot = Spot(lot_id=lot.lot_id, status='A')
                db.session.add(new_spot)
            lot.max_spots = new_max_spots
            db.session.commit()
            flash(f'Lot updated successfully. {num_new_spots} new spot(s) added.')

        
        elif new_max_spots < lot.max_spots:
            to_remove = lot.max_spots - new_max_spots

            
            available_spots = Spot.query.filter_by(lot_id=lot.lot_id, status='A').all()

            spots_to_delete = []
            for spot in available_spots:
                
                related_reservations = Reservation.query.filter_by(spot_id=spot.spot_id).all()
                for res in related_reservations:
                    db.session.delete(res)
                spots_to_delete.append(spot)
                if len(spots_to_delete) == to_remove:
                    break

            if len(spots_to_delete) < to_remove:
                flash('Cannot reduce spots: not enough available spots that can be deleted. Some spots may be occupied or have reservations.')
                return render_template('edit_lot.html', lot=lot)

            
            for spot in spots_to_delete:
                db.session.delete(spot)

            
            lot.max_spots = new_max_spots
            db.session.commit()
            flash(f'Lot updated successfully. {to_remove} spot(s) and related reservations removed.')

        else:
            
            db.session.commit()
            flash('Lot details updated.')

        return redirect(url_for('admin.lot_list', lot_id=lot.lot_id))

    
    return render_template('edit_lot.html', lot=lot)

@admin_bp.route('/lot/<int:lot_id>/delete', methods=['GET','POST'])
def delete_parking_lot(lot_id):
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('auth.login'))
    
    lot = Lot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        active_reservation = Reservation.query.filter_by(lot_id = lot_id, leaving_timestamp=None).first()
        if active_reservation:
            flash('you cannot delete the lot. Still occupied.')
            return redirect(url_for('admin.lot_list', lot_id=lot_id))
        
        reservations = Reservation.query.filter_by(lot_id=lot_id)
        for res in reservations:
            db.session.delete(res)
        
        spots = Spot.query.filter_by(lot_id=lot_id)
        for spot in spots:
            db.session.delete(spot)

        db.session.delete(lot)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))


@admin_bp.route('/search_spot')
def search_spot():
    spot_id = request.args.get('spot_id', type=int)
    if not spot_id:
        flash("Please enter a valid Spot ID.")
        return redirect(url_for('admin.admin_dashboard'))

    spot = Spot.query.filter_by(spot_id=spot_id).first()
    if not spot:
        flash("Invalid spot id.")
        return redirect(url_for('admin.admin_dashboard'))

    lot = Lot.query.filter_by(lot_id=spot.lot_id).first()
    if not lot:
        flash("Parking lot not found for this spot.")
        return redirect(url_for('admin.admin_dashboard'))

    info = {
        'spot_id': spot.spot_id,
        'status': spot.status,
        'location': lot.location_name,
        'price': lot.price
    }

    return render_template('spot.html', info=info, lot=lot)

@admin_bp.route('/users')
def view_users():
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('auth.login'))

    
    users = User.query.filter(User.role != 'admin').all()

    
    users_data = []
    for user in users:
        vehicle_count = len(user.vehicles) if user.vehicles else 0
        
        active_spots_count = Reservation.query.filter_by(user_id=user.id, leaving_timestamp=None).count()
        users_data.append({
            'username': user.username,
            'full_name': user.full_name,
            'vehicle_count': vehicle_count,
            'active_spots': active_spots_count
        })

    return render_template('users.html', users=users_data)


@admin_bp.route('/parking_history',methods=['GET','POST'])
def parking_history():
    
    history=[]
    if session.get('role') != 'admin':
        flash('Access denied. Admins only.')
        return redirect(url_for('admin.dashboard'))
    
    reservations = Reservation.query.filter_by()

    for res in reservations:
        parktime = res.parking_timestamp
        leavetime = res.leaving_timestamp
        amount = res.amount
        status = res.payment_status
        user_details = User.query.filter_by(id = res.user_id).first()
        u_name = user_details.full_name
        u_username = user_details.username
        history.append({
            "full_name": u_name,
            "username": u_username,
            "parking_time": parktime,
            "leaving_time": leavetime,
            "amount": amount,
            "status": status
        })

    return render_template('history.html',reservation=history)