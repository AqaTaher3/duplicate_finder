import os

def delete_empty_folders(directory):
    for foldername, subfolders, filenames in os.walk(directory, topdown=False):
        # اگر فولدر هیچ فایل و زیرپوشه‌ای نداشته باشد، حذفش کن
        if not subfolders and not filenames:
            try:
                os.rmdir(foldername)
                print(f"Deleted empty folder: {foldername}")
            except OSError as e:
                print(f"Could not delete {foldername}: {e}")

# مسیر موردنظر را اینجا بده
path = r"C:\Users\HP\Music\music\RRrrrrrrr"
delete_empty_folders(path)
