from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Vehicle
import bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u_name = request.form.get('u_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip().encode('utf-8')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')

        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        new_user = User(u_name=u_name,username=username, password=hashed, role='user')
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You may log in.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip().encode('utf-8')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password, user.password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('index.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('auth.login'))
