import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User
from auth import auth_bp

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
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        flash('Access denied.')
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
