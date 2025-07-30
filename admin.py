from flask import Blueprint, render_template, redirect, url_for, flash, session, abort, request
from models import db, Lot, Spot
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
        max_wheels = request.form.get('max_wheels')

        try:
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
        user = spot.user
        vehicle = spot.vehicle
        time_parked = datetime.utcnow() - spot.parked_at
        minutes_parked = max(int(time_parked.total_seconds() / 60), 0)

        revenue = round(minutes_parked * lot.price, 2)

        lot_vehicles.append({
            'vehicle_number': vehicle.v_number,
            'username': user.username,
            'wheels_no': spot.no_of_wheels,
            'parked_at': spot.parked_at,
            'minutes_parked': minutes_parked,
            'revenue': revenue
        })

    return render_template('lot_list.html', lot=lot, lot_vehicles=lot_vehicles)

# @admin_bp.route('/lot/<int:lot_id>')
# def lot_list(lot_id):
#     if session.get('role') != 'admin':
#         flash('Access denied.')
#         return redirect(url_for('auth.login'))

#     if request.method == 'POST':
#         location_name = request.form.get('location_name')
#         price = request.form.get('price')
#         address = request.form.get('address')
#         pin_code = request.form.get('pin_code')
#         max_wheels = request.form.get('max_wheels')


#         try:
#             new_lot = Lot(
#                 location_name=location_name,
#                 price=float(price),
#                 address=address,
#                 pin_code=pin_code,
#                 max_wheels=int(max_wheels)
#             )
#             db.session.add(new_lot)
#             db.session.commit()
#             flash('Parking lot created successfully.')
#             return redirect(url_for('admin.admin_dashboard'))
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Error creating parking lot: {str(e)}')
#             return render_template('create_lot.html')

#     return render_template('create_lot.html')