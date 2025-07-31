import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Lot, Spot, Reservation, Vehicle
from auth import auth_bp
from user import user_bp
from admin import admin_bp
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server/non-notebook use
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64


app = Flask(__name__)
app.secret_key = 'your_secret_key'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)



@app.route('/')
def home():
    return redirect(url_for('auth.login'))



@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash('Admin login required.')
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id) 
    name = user.full_name 
    parking_lots = Lot.query.all()

    total_spots_occupied = 0
    total_spots = 0
    total_revenue_per_minute = 0.0

    lots_data = []
    for lot in parking_lots:
        occupied_spots_count = Spot.query.filter_by(lot_id=lot.lot_id, status='O').count()
        max_spots = lot.max_spots
        total_spots_occupied += occupied_spots_count
        total_spots += max_spots
        lot_revenue = lot.price * occupied_spots_count
        total_revenue_per_minute += lot_revenue

        lots_data.append({
            'id': lot.lot_id,
            'location_name': lot.location_name,
            'pin_code': lot.pin_code,
            'occupied': occupied_spots_count,
            'max_spots': max_spots
        })

    occupancy_percent = (total_spots_occupied / total_spots * 100) if total_spots else 0

    parking_lots = Lot.query.all()
    lot_names = []
    occupied_counts = []
    revenues = []

    for lot in parking_lots:
        lot_names.append(lot.location_name)
        occ = Spot.query.filter_by(lot_id=lot.lot_id, status='O').count()
        occupied_counts.append(occ)
        rev = lot.price * occ
        revenues.append(rev)

    # ---------- Pie Chart (Occupied Spots per Lot) ----------
    pie_img = None
    if lot_names and sum(occupied_counts) > 0:
        fig1, ax1 = plt.subplots(figsize=(5,5))
        ax1.pie(occupied_counts, labels=lot_names, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Occupied Spots Distribution')
        buf = io.BytesIO()
        plt.tight_layout()
        fig1.savefig(buf, format='png')
        buf.seek(0)
        pie_img = base64.b64encode(buf.read()).decode('ascii')
        plt.close(fig1)

    # ---------- Bar Chart (Revenue per Lot) ----------
    bar_img = None
    if lot_names and revenues:
        fig2, ax2 = plt.subplots(figsize=(6,4))
        ax2.bar(lot_names, revenues, color='#27ae60')
        ax2.set_ylabel('Revenue')
        ax2.set_xlabel('Parking Lot')
        ax2.set_title('Revenue by Lot')
        plt.tight_layout()
        buf = io.BytesIO()
        fig2.savefig(buf, format='png')
        buf.seek(0)
        bar_img = base64.b64encode(buf.read()).decode('ascii')
        plt.close(fig2)


    return render_template(
        'admin_dashboard.html',
        username=session.get('username', 'admin'),
        name=name,
        spots_occupied=total_spots_occupied,
        occupancy_percent=round(occupancy_percent, 2),
        revenue_per_minute=round(total_revenue_per_minute, 2),
        parking_lots=lots_data,
        pie_img=pie_img,
        bar_img=bar_img,
    )


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

    active_reservation = Reservation.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    active_spot = active_reservation.spot if active_reservation else None

    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()

    total_time = timedelta()
    total_paid = 0
    for res in reservations:
        if res.leaving_timestamp:
            total_time += res.leaving_timestamp - res.parking_timestamp
        if res.payment_status == 'Paid' and res.amount:
            total_paid += res.amount

    total_minutes = int(total_time.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60

    total_time_parked = f"{hours}h {minutes:02d}m"
    total_amount_paid = f"₹{total_paid:.2f}"
    total_bookings = len(reservations)

    times = []
    durations = []
    for res in reservations:
        if res.leaving_timestamp:  # Only plot completed reservations
            times.append(res.parking_timestamp)  # This is a datetime object
            duration_min = (res.leaving_timestamp - res.parking_timestamp).total_seconds() / 60  # Duration in minutes
            durations.append(duration_min)

    img_b64 = None
    if times and durations:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(times, durations, marker='o', color='green', linewidth=2)
        ax.set_title("Parking Duration per Reservation (minutely)")
        ax.set_xlabel("Date & Time")
        ax.set_ylabel("Duration (minutes)")
        ax.grid(True)
        # Set x-axis to minutes with appropriate format and auto-spacing
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b %H:%M'))  # e.g., "31-Jul 13:45"
        fig.autofmt_xdate(rotation=45)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)

    return render_template(
        'user_dashboard.html',
        user=user,
        active_spot=active_spot,
        reservations=reservations,
        active_reservation = active_reservation,
        total_time_parked=total_time_parked,
        total_amount_paid=total_amount_paid,
        total_bookings=total_bookings,
        duration_line_chart=img_b64,
    )


if __name__ == '__main__':
    app.run(debug=True)
