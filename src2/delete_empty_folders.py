import os
import time
from pathlib import Path


def delete_empty_folders(directory, dry_run=False, verbose=True):
    """
    حذف پوشه‌های خالی به صورت بازگشتی

    پارامترها:
        directory: مسیر پوشه اصلی
        dry_run: اگر True باشد، فقط گزارش می‌دهد اما حذف نمی‌کند
        verbose: نمایش جزئیات

    بازگشت:
        tuple: (تعداد پوشه‌های حذف شده، لیست پوشه‌های حذف شده)
    """
    if not os.path.exists(directory):
        if verbose:
            print(f"❌ پوشه وجود ندارد: {directory}")
        return 0, []

    deleted_count = 0
    backup_deleteds = []

    try:
        while True:
            folders_deleted_in_pass = 0

            # پیمایش از پایین به بالا (عمیق‌ترین پوشه‌ها اول)
            for root, dirs, files in os.walk(directory, topdown=False):
                current_path = Path(root)

                # نادیده گرفتن پوشه‌های خاص
                if any(ignore in str(current_path).lower() for ignore in ['system', 'windows', '$recycle']):
                    continue

                # شرط 1: پوشه کاملاً خالی
                if not dirs and not files:
                    try:
                        if not dry_run:
                            os.rmdir(root)
                        folders_deleted_in_pass += 1
                        backup_deleteds.append(root)
                        if verbose:
                            print(f"🗑️  {'(DRY RUN) ' if dry_run else ''}پوشه خالی حذف شد: {root}")
                    except OSError as e:
                        if verbose:
                            print(f"⚠️  خطا در حذف پوشه خالی {root}: {e}")

                # شرط 2: فقط فایل metadata.opf
                elif not dirs and len(files) == 1 and files[0].lower() == 'metadata.opf':
                    opf_path = os.path.join(root, files[0])
                    try:
                        if not dry_run:
                            os.remove(opf_path)
                            os.rmdir(root)
                        folders_deleted_in_pass += 1
                        backup_deleteds.append(root)
                        if verbose:
                            print(f"🗑️  {'(DRY RUN) ' if dry_run else ''}پوشه فقط OPF حذف شد: {root}")
                    except OSError as e:
                        if verbose:
                            print(f"⚠️  خطا در حذف پوشه OPF {root}: {e}")

                # شرط 3: فقط فایل‌های موقت یا سیستمی
                elif not dirs and all(f.lower().endswith(('.tmp', '.temp', '.log', '.db')) for f in files):
                    try:
                        if not dry_run:
                            for f in files:
                                os.remove(os.path.join(root, f))
                            os.rmdir(root)
                        folders_deleted_in_pass += 1
                        backup_deleteds.append(root)
                        if verbose:
                            print(f"🗑️  {'(DRY RUN) ' if dry_run else ''}پوشه فایل‌های موقت حذف شد: {root}")
                    except OSError as e:
                        if verbose:
                            print(f"⚠️  خطا در حذف پوشه موقت {root}: {e}")

            deleted_count += folders_deleted_in_pass

            # اگر در این پاس هیچ پوشه‌ای حذف نشد، حلقه را بشکن
            if folders_deleted_in_pass == 0:
                break

        # بررسی پوشه اصلی (اگر خالی شد)
        try:
            if not os.listdir(directory):
                if not dry_run:
                    os.rmdir(directory)
                    backup_deleteds.append(directory)
                if verbose:
                    print(f"🗑️  {'(DRY RUN) ' if dry_run else ''}پوشه اصلی خالی حذف شد: {directory}")
        except OSError as e:
            if verbose:
                print(f"⚠️  خطا در حذف پوشه اصلی {directory}: {e}")

        if verbose:
            print(f"\n📊 خلاصه:")
            print(f"   کل پوشه‌های حذف شده: {deleted_count}")
            print(f"   حالت آزمایشی: {'بله' if dry_run else 'خیر'}")

        return deleted_count, backup_deleteds

    except Exception as e:
        print(f"❌ خطای غیرمنتظره در حذف پوشه‌های خالی: {e}")
        return deleted_count, backup_deleteds


def find_empty_folders(directory):
    """یافتن پوشه‌های خالی بدون حذف آنها"""
    return delete_empty_folders(directory, dry_run=True, verbose=False)


# تست تابع
if __name__ == "__main__":
    test_dir = r"D:\English"

    if os.path.exists(test_dir):
        print(f"🔍 بررسی پوشه: {test_dir}")
        count, folders = delete_empty_folders(test_dir, dry_run=True, verbose=True)
        print(f"\n✅ یافت شد {count} پوشه خالی")

        if input("\nآیا می‌خواهید واقعاً حذف شوند؟ (y/n): ").lower() == 'y':
            count, _ = delete_empty_folders(test_dir, dry_run=False, verbose=True)
            print(f"✅ {count} پوشه حذف شدند")
    else:
        print(f"❌ پوشه تست وجود ندارد: {test_dir}")