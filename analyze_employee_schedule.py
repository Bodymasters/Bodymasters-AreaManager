import sqlite3
import pandas as pd

# استخراج بيانات جدول employee_schedule من SQLite
sqlite_conn = sqlite3.connect('app.db')
schedule_df = pd.read_sql_query('SELECT * FROM employee_schedule', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(schedule_df)} سجل من جدول employee_schedule")

# عرض أسماء الأعمدة وأنواع البيانات
print("\nأسماء الأعمدة وأنواع البيانات:")
for col in schedule_df.columns:
    print(f"  العمود: {col}, النوع: {schedule_df[col].dtype}")

# عرض عينة من البيانات
print("\nعينة من البيانات:")
print(schedule_df.head())

# حفظ البيانات في ملف CSV للتحليل
schedule_df.to_csv('employee_schedule_analysis.csv', index=False, encoding='utf-8-sig')
print("\nتم حفظ بيانات جدول employee_schedule في ملف employee_schedule_analysis.csv للتحليل")