from app import app, db, User, Club

# الحصول على جميع المستخدمين
users = User.query.all()

print("=== معلومات المستخدمين والنوادي ===")
for user in users:
    print(f"المستخدم: {user.name} (ID: {user.id}, اسم المستخدم: {user.username}, مسؤول: {user.is_admin})")
    print(f"النوادي المرتبطة: {len(user.clubs)}")
    for club in user.clubs:
        print(f"  - {club.name} (ID: {club.id})")
    print("---")

# الحصول على جميع النوادي
clubs = Club.query.all()
print("\n=== معلومات النوادي والمستخدمين ===")
for club in clubs:
    print(f"النادي: {club.name} (ID: {club.id})")
    print(f"المستخدمين المرتبطين: {len(club.users)}")
    for user in club.users:
        print(f"  - {user.name} (ID: {user.id}, اسم المستخدم: {user.username}, مسؤول: {user.is_admin})")
    print("---")
