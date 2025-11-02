import os
import sys
import ctypes
import platform


def is_admin():
    """بررسی دسترسی Administrator"""
    try:
        if platform.system() == 'Windows':
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.getuid() == 0
    except:
        return False


def run_as_admin():
    """اجرای مجدد با دسترسی بالا"""
    if platform.system() == 'Windows':
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    sys.exit(0)


def should_delete_folder(filenames):
    """بررسی آیا پوشه باید حذف شود"""
    if not filenames:
        return True  # پوشه کاملاً خالی

    # بررسی وجود فقط فایل‌های OPF/JPG
    for f in filenames:
        lower_f = f.lower()
        if not (lower_f.endswith('.opf') or lower_f.endswith('.jpg')):
            return False
    return True


def delete_empty_parents(folder_path):
    """حذف پوشه‌های والد خالی"""
    parent = os.path.dirname(folder_path)

    while parent != folder_path:  # تا رسیدن به ریشه
        try:
            if not os.listdir(parent):  # اگر پوشه خالی است
                os.rmdir(parent)
                print(f"حذف پوشه والد خالی: {parent}")
                folder_path = parent
                parent = os.path.dirname(parent)
            else:
                break
        except OSError:
            break


def clean_directory(directory):
    """حذف پوشه‌های هدف و والدهای خالی"""
    if not os.path.exists(directory):
        print(f"مسیر {directory} وجود ندارد!")
        return

    deleted_count = 0

    for root, dirs, files in os.walk(directory, topdown=False):
        if should_delete_folder(files):
            try:
                # حذف تمام فایل‌ها
                for f in files:
                    os.remove(os.path.join(root, f))

                # حذف پوشه
                os.rmdir(root)
                deleted_count += 1
                print(f"حذف پوشه: {root}")

                # بررسی پوشه‌های والد
                delete_empty_parents(root)

            except PermissionError:
                print(f"خطای دسترسی در: {root}")
            except OSError as e:
                print(f"خطا در حذف {root}: {e}")

    print(f"تعداد پوشه‌های حذف شده: {deleted_count}")


def main():
    if platform.system() == "Windows" and not is_admin():
        run_as_admin()
        return

    target_dir = r"C:\Users\HP\Music\000_PriorityFolder"
    print(f"در حال پردازش: {target_dir}")
    clean_directory(target_dir)
    input("پردازش کامل شد. برای خروج Enter بزنید...")


if __name__ == "__main__":
    main()