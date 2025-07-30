from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Vehicle, User

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

        # Ensure no duplicate vehicle for the user
        if Vehicle.query.filter_by(v_number=v_number, user_id=session['user_id']).first():
            flash('A vehicle with this number is already registered to you.')
            return render_template('vehicle_register.html')
        
        vehicle = Vehicle(v_number=v_number, wheels_no=wheels_no, user_id=session['user_id'])
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle registered successfully.')
        return redirect(url_for('user_dashboard'))

    return render_template('vehicle_register.html')
