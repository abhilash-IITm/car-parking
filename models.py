from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    u_name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hash
    role = db.Column(db.String(20), nullable=False)

    vehicles = db.relationship('Vehicle', backref='user', cascade='all, delete-orphan')
    spots = db.relationship('Spot', backref='user', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='user', cascade='all, delete-orphan')


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    v_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wheels_no = db.Column(db.Integer, nullable=False)


class Lot(db.Model):
    __tablename__ = 'lots'
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)  # price per unit time
    address = db.Column(db.String(200), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    max_wheels = db.Column(db.Integer, nullable=False)

    spots = db.relationship('Spot', backref='lot', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='lot', cascade='all, delete-orphan')


class Spot(db.Model):
    __tablename__ = 'spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('lots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    no_of_wheels = db.Column(db.Integer, nullable=False)
    parked_at = db.Column(db.DateTime, default=datetime.utcnow)

    vehicle = db.relationship('Vehicle', backref='active_spots')


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('lots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    wheels_occupied = db.Column(db.Integer, nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='Pending')  # e.g. Pending, Paid, Failed

    vehicle = db.relationship('Vehicle', backref='reservations')
    
    def __repr__(self):
        return f"<Reservation {self.id} User:{self.user_id} Lot:{self.lot_id} Amount:{self.amount} Status:{self.payment_status}>"
