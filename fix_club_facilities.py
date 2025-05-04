import os
import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 1. التحقق من وجود جدول club_facilities
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='club_facilities'")
if not cursor.fetchone():
    print("جدول club_facilities غير موجود! سيتم إنشاؤه...")
    cursor.execute("""
    CREATE TABLE club_facilities (
        club_id INTEGER NOT NULL,
        facility_id INTEGER NOT NULL,
        PRIMARY KEY (club_id, facility_id),
        FOREIGN KEY (club_id) REFERENCES club (id),
        FOREIGN KEY (facility_id) REFERENCES facility (id)
    )
    """)
    conn.commit()
    print("تم إنشاء جدول club_facilities بنجاح!")

# 2. الحصول على قائمة النوادي
cursor.execute("SELECT id, name FROM club")
clubs = cursor.fetchall()
print(f"تم العثور على {len(clubs)} نادي")

# 3. الحصول على قائمة المرافق
cursor.execute("SELECT id, name FROM facility")
facilities = cursor.fetchall()
print(f"تم العثور على {len(facilities)} مرفق")

# 4. التحقق من العلاقات بين النوادي والمرافق
for club_id, club_name in clubs:
    cursor.execute("SELECT facility_id FROM club_facilities WHERE club_id = ?", (club_id,))
    club_facilities = cursor.fetchall()
    club_facility_ids = [f[0] for f in club_facilities]
    
    print(f"\nالنادي: {club_name} (معرف: {club_id})")
    print(f"عدد المرافق المرتبطة: {len(club_facilities)}")
    
    # إذا لم يكن هناك مرافق مرتبطة، قم بربط جميع المرافق بالنادي
    if len(club_facilities) == 0:
        print("لا توجد مرافق مرتبطة بهذا النادي. سيتم ربط جميع المرافق...")
        for facility_id, facility_name in facilities:
            cursor.execute("INSERT INTO club_facilities (club_id, facility_id) VALUES (?, ?)", 
                          (club_id, facility_id))
            print(f"تم ربط المرفق '{facility_name}' بالنادي '{club_name}'")
    else:
        print("المرافق المرتبطة:")
        for facility_id, facility_name in facilities:
            if facility_id in club_facility_ids:
                print(f"- {facility_name} (معرف: {facility_id})")
            else:
                # إضافة المرافق غير المرتبطة
                cursor.execute("INSERT INTO club_facilities (club_id, facility_id) VALUES (?, ?)", 
                              (club_id, facility_id))
                print(f"تم ربط المرفق '{facility_name}' بالنادي '{club_name}'")

# 5. التحقق من بنود المرافق للنادي
for club_id, club_name in clubs:
    cursor.execute("""
    SELECT cfi.id, f.name, fi.name 
    FROM club_facility_item cfi
    JOIN facility f ON cfi.facility_id = f.id
    JOIN facility_item fi ON cfi.facility_item_id = fi.id
    WHERE cfi.club_id = ? AND cfi.is_active = 1
    """, (club_id,))
    
    club_facility_items = cursor.fetchall()
    print(f"\nالنادي: {club_name} (معرف: {club_id})")
    print(f"عدد بنود المرافق النشطة: {len(club_facility_items)}")
    
    if len(club_facility_items) > 0:
        print("بنود المرافق النشطة:")
        for item_id, facility_name, item_name in club_facility_items:
            print(f"- {facility_name}: {item_name} (معرف: {item_id})")
    
    # إذا لم يكن هناك بنود مرافق، قم بإضافة بنود افتراضية
    if len(club_facility_items) == 0:
        print("لا توجد بنود مرافق نشطة لهذا النادي. سيتم إضافة بنود افتراضية...")
        
        # الحصول على جميع المرافق المرتبطة بالنادي
        cursor.execute("""
        SELECT f.id, f.name 
        FROM facility f
        JOIN club_facilities cf ON f.id = cf.facility_id
        WHERE cf.club_id = ?
        """, (club_id,))
        
        club_facilities = cursor.fetchall()
        
        for facility_id, facility_name in club_facilities:
            # الحصول على بنود المرفق
            cursor.execute("SELECT id, name FROM facility_item WHERE facility_id = ?", (facility_id,))
            facility_items = cursor.fetchall()
            
            if len(facility_items) == 0:
                # إذا لم يكن هناك بنود للمرفق، قم بإضافة بند افتراضي
                cursor.execute("INSERT INTO facility_item (name, is_active, facility_id) VALUES (?, 1, ?)", 
                              (f"بند افتراضي لـ {facility_name}", facility_id))
                facility_item_id = cursor.lastrowid
                print(f"تم إضافة بند افتراضي للمرفق '{facility_name}'")
                
                # ربط البند بالنادي
                cursor.execute("""
                INSERT INTO club_facility_item (club_id, facility_id, facility_item_id, is_active)
                VALUES (?, ?, ?, 1)
                """, (club_id, facility_id, facility_item_id))
                print(f"تم ربط البند الافتراضي بالنادي '{club_name}'")
            else:
                # ربط جميع بنود المرفق بالنادي
                for item_id, item_name in facility_items:
                    # التحقق من وجود البند في جدول club_facility_item
                    cursor.execute("""
                    SELECT id FROM club_facility_item 
                    WHERE club_id = ? AND facility_id = ? AND facility_item_id = ?
                    """, (club_id, facility_id, item_id))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO club_facility_item (club_id, facility_id, facility_item_id, is_active)
                        VALUES (?, ?, ?, 1)
                        """, (club_id, facility_id, item_id))
                        print(f"تم ربط البند '{item_name}' بالنادي '{club_name}'")

# حفظ التغييرات
conn.commit()
print("\nتم إصلاح العلاقات بين النوادي والمرافق بنجاح!")

# إغلاق الاتصال
conn.close()
