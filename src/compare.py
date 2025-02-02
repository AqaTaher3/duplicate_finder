import os
import shutil


def remove_duplicate_folders(main_path, another_path):
    if not os.path.exists(main_path) or not os.path.exists(another_path):
        print("یکی از مسیرها وجود ندارد.")
        return

    # پیمایش فولدرهای اول و دوم به صورت بازگشتی
    for root, dirs, files in os.walk(main_path, topdown=False):
        relative_path = os.path.relpath(root, main_path)
        corresponding_path = os.path.join(another_path, relative_path)

        if os.path.exists(corresponding_path):
            # بررسی محتویات فولدرها
            main_files = set(os.listdir(root))
            another_files = set(os.listdir(corresponding_path))

            if main_files == another_files:
                try:
                    shutil.rmtree(corresponding_path)  # حذف فولدر کامل
                    print(f"folder removed : {corresponding_path}")
                except Exception as e:
                    print(f"eror in removing folder{corresponding_path}: {e}")
            else:
                # حذف فایل‌های مشابه
                duplicate_files = main_files & another_files
                for file in duplicate_files:
                    file_path = os.path.join(corresponding_path, file)
                    try:
                        os.remove(file_path)
                        print(f"files removed: {file_path}")
                    except Exception as e:
                        print(f"eror in removing files{file_path}: {e}")


# مثال استفاده
main_path = r"C:\Users\HP\Music\00_Books\000_my_new_Library"
another_path = r"C:\Users\HP\Calibre Library"

remove_duplicate_folders(main_path, another_path)
