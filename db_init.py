from app import app, db
import bcrypt
from models import User

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
        admin_user = User(username='admin', password=hashed, role='admin', full_name='admi')
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created: admin/admin123')
