import os
import errno


def making_folders(folder_selected):
    """ایجاد پوشه‌های لازم با مدیریت خطا"""
    folders_created = []

    try:
        # پوشه‌های اصلی
        base_000 = os.path.join(folder_selected, "000")
        priority_folder = os.path.join(base_000, "PriorityFolder")
        corrupted_folder = os.path.join(base_000, "Corrupted_folder")
        keep_folder = os.path.join(folder_selected, "Keep_folder")

        folders_to_create = [
            (base_000, "پوشه پایه 000"),
            (priority_folder, "پوشه اولویت"),
            (corrupted_folder, "پوشه فایل‌های خراب"),
            (keep_folder, "پوشه نگهداری")
        ]

        for folder_path, folder_name in folders_to_create:
            try:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path, exist_ok=True)
                    print(f"✅ {folder_name} ایجاد شد: {folder_path}")
                    folders_created.append(folder_path)
                else:
                    print(f"ℹ️  {folder_name} از قبل وجود دارد: {folder_path}")
                    folders_created.append(folder_path)
            except OSError as e:
                if e.errno == errno.EACCES:
                    print(f"⚠️  دسترسی به {folder_path} مجاز نیست")
                else:
                    print(f"❌ خطا در ایجاد {folder_name}: {e}")
            except Exception as e:
                print(f"❌ خطای غیرمنتظره در ایجاد {folder_name}: {e}")

        return [keep_folder, priority_folder, corrupted_folder]

    except Exception as e:
        print(f"❌ خطای شدید در ایجاد پوشه‌ها: {e}")
        # بازگرداندن پوشه‌هایی که ایجاد شده‌اند
        return [keep_folder if 'keep_folder' in locals() and keep_folder else None,
                priority_folder if 'priority_folder' in locals() and priority_folder else None,
                corrupted_folder if 'corrupted_folder' in locals() and corrupted_folder else None]