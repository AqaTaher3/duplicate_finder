import os
import shutil

source = r"D:\000_Music"
destination = r"G:"

for root, dirs, files in os.walk(source):
    # مسیر نسبی فولدرها نسبت به مسیر مبدا
    relative_path = os.path.relpath(root, source)
    destination_path = os.path.join(destination, relative_path)

    # ایجاد ساختار فولدر در مقصد
    os.makedirs(destination_path, exist_ok=True)
