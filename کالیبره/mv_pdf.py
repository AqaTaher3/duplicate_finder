import os
import shutil

# مسیر مبدا (پوشه‌ای که می‌خواهید فایل‌های PDF از آنجا پیدا شوند)
source_dir = r"C:\Users\HP\Music\000_PriorityFolder"

# مسیر مقصد (پوشه‌ای که می‌خواهید فایل‌های PDF در آنجا ذخیره شوند)
destination_dir = r"C:\Users\HP\Music\pdf"

# بررسی و ایجاد پوشه مقصد در صورت عدم وجود
if not os.path.exists(destination_dir):
    os.makedirs(destination_dir)

# پیمایش در پوشه مبدا و انتقال فایل‌های PDF به پوشه مقصد
for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file.lower().endswith('.epub'):  # بررسی فرمت PDF
            source_file = os.path.join(root, file)
            destination_file = os.path.join(destination_dir, file)

            # انتقال فایل از مبدا به مقصد
            shutil.move(source_file, destination_file)
            print(f"انتقال فایل: {file}")

print("✅ تمامی فایل‌های PDF به پوشه مقصد منتقل شدند.")
