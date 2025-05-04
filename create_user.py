from app import app, db, User

with app.app_context():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print('تم إنشاء المستخدم بنجاح!')
    else:
        print('المستخدم موجود بالفعل!')
