from app import app, db, User, Club, Employee, Facility
from datetime import datetime, date

# Create database tables
with app.app_context():
    db.create_all()

    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)

        # Add sample data
        club1 = Club(name='نادي الرياض', location='الرياض - حي النزهة', manager_name='أحمد محمد', phone='0501234567')
        club2 = Club(name='نادي جدة', location='جدة - حي الروضة', manager_name='خالد عبدالله', phone='0551234567')

        db.session.add(club1)
        db.session.add(club2)

        # Add employees
        emp1 = Employee(name='محمد علي', position='مدرب', phone='0512345678',
                       email='mohamed@example.com', hire_date=date(2023, 1, 15), club_id=1)
        emp2 = Employee(name='فهد سعيد', position='مدرب', phone='0523456789',
                       email='fahad@example.com', hire_date=date(2023, 3, 10), club_id=1)
        emp3 = Employee(name='سارة أحمد', position='موظفة استقبال', phone='0534567890',
                       email='sara@example.com', hire_date=date(2023, 2, 20), club_id=2)

        db.session.add(emp1)
        db.session.add(emp2)
        db.session.add(emp3)

        # Add facilities
        facilities = [
            "مسبح",
            "ملعب كرة قدم",
            "صالة رياضية",
            "ملعب تنس",
            "ساونا",
            "جاكوزي"
        ]

        for facility_name in facilities:
            facility = Facility(name=facility_name)
            db.session.add(facility)

        # Commit changes
        db.session.commit()

        print('تم إنشاء قاعدة البيانات وإضافة البيانات الأولية بنجاح!')
