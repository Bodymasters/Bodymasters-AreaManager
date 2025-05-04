import pandas as pd

# قراءة ملف CSV
df = pd.read_csv('facility_item_backup.csv')

# عرض الأعمدة وأطوال القيم
for col in df.columns:
    if df[col].dtype == 'object':  # للأعمدة النصية فقط
        max_length = df[col].astype(str).map(len).max()
        print(f"العمود: {col}, أقصى طول: {max_length}")
        if max_length > 100:
            print(f"  القيم الطويلة:")
            long_values = df[df[col].astype(str).map(len) > 100][col]
            for i, value in enumerate(long_values):
                if i < 5:  # عرض أول 5 قيم طويلة فقط
                    print(f"    {value}")