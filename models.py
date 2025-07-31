from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=True) # renamed from u_name
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    vehicles = db.relationship('Vehicle', backref='user', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    v_id = db.Column(db.Integer, primary_key=True)
    v_number = db.Column(db.String(20), unique=True, nullable=False)
    details = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Lot(db.Model):
    __tablename__ = 'lots'
    lot_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False) # price per unit time
    address = db.Column(db.String(200), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    max_spots = db.Column(db.Integer, nullable=False)
    spots = db.relationship('Spot', backref='lot', cascade='all, delete-orphan')


class Spot(db.Model):
    __tablename__ = 'spots'
    spot_id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('lots.lot_id'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='A') # 'A'=Available, 'O'=Occupied


class Reservation(db.Model):
    __tablename__ = 'reservations'
    r_id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('spots.spot_id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('lots.lot_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.v_id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True, default=None)
    amount = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='Parked')
    lot = db.relationship('Lot', backref='reservations')
    spot = db.relationship('Spot', backref='reservations')
    vehicle = db.relationship('Vehicle')


    def __repr__(self):
        return f"<Reservation {self.r_id} User:{self.user_id} Spot:{self.spot_id} Amount:{self.amount} Status:{self.payment_status}>"
