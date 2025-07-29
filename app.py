import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# @app.before_first_request
# def init_db():
#     db.create_all()
#     admin = User.query.filter_by(role='admin').first()
#     if not admin:
#         hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
#         admin_user = User(username='admin', password=hashed, role='admin')
#         db.session.add(admin_user)
#         db.session.commit()
#         print('Admin user created: admin/admin123')

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip().encode('utf-8')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
        else:
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            new_user = User(username=username, password=hashed, role='user')
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You may log in.')
            return redirect(url_for('login'))
    return render_template('register.html') 

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

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
