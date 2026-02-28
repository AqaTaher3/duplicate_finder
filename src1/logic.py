import os
import time
import stat
import shutil
import send2trash  # نیاز به نصب: pip install send2trash
from src1.finder import FileFinder
from src.log_manager import log_manager


class FileHandler:
    def __init__(self, folder_selected, priority_folder, keep_folder, auto_delete=True):
        self.folder_selected = folder_selected
        self.priority_folder = priority_folder
        self.keep_folder = keep_folder
        self.auto_delete = auto_delete
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.failed_deletions = []
        self.successful_deletions = []  # لیست فایل‌های حذف شده موفق
        self.use_recycle_bin = True  # استفاده از سطل بازیافت به جای حذف دائم
        self.logger = log_manager.get_logger("FileHandler")

        # ایجاد پوشه بک‌آپ
        self.backup_dir = os.path.join(folder_selected, "_backup_deleted")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

        self.logger.info(f"FileHandler ساخته شد برای پوشه: {folder_selected}")
        self.load_files()

    def _safe_delete_files(self, files_to_delete, use_recycle_bin=True):
        """حذف امن فایل‌ها با قابلیت بازیابی"""
        deleted_count = 0
        moved_to_trash = 0
        permanent_deleted = 0

        for file_path in files_to_delete:
            try:
                if not os.path.exists(file_path):
                    self.logger.warning(f"فایل وجود ندارد: {file_path}")
                    continue

                # بررسی اینکه آیا فایل در پوشه‌های سیستمی است
                if self._is_system_file(file_path):
                    self.logger.warning(f"فایل سیستمی - رد شد: {file_path}")
                    self.failed_deletions.append((file_path, "فایل سیستمی"))
                    continue

                # ایجاد بک‌آپ قبل از حذف
                backup_path = self._create_backup(file_path)

                if use_recycle_bin and self.use_recycle_bin:
                    # حذف به سطل بازیافت
                    try:
                        send2trash.send2trash(file_path)
                        moved_to_trash += 1
                        deleted_count += 1
                        self.successful_deletions.append((file_path, backup_path))
                        self.logger.info(f"✅ انتقال به سطل بازیافت: {os.path.basename(file_path)}")
                        continue
                    except Exception as e:
                        self.logger.warning(f"خطا در انتقال به سطل بازیافت: {e}")

                # حذف دائم
                try:
                    os.remove(file_path)
                    permanent_deleted += 1
                    deleted_count += 1
                    self.successful_deletions.append((file_path, backup_path))
                    self.logger.info(f"✅ حذف دائم موفق: {os.path.basename(file_path)}")
                except PermissionError:
                    self.logger.warning(f"⚠️ دسترسی denied: {file_path}")
                    if self._force_delete_file(file_path):
                        deleted_count += 1
                        self.logger.info(f"✅ حذف اجباری موفق: {os.path.basename(file_path)}")
                    else:
                        self.logger.error(f"❌ حذف ناموفق: {file_path}")
                        self.failed_deletions.append((file_path, "دسترسی denied"))
                except Exception as e:
                    self.logger.error(f"❌ خطا در حذف {file_path}: {e}")
                    self.failed_deletions.append((file_path, str(e)))

            except Exception as e:
                self.logger.exception(f"❌ خطای غیرمنتظره در حذف {file_path}")
                self.failed_deletions.append((file_path, str(e)))

        # لاگ آمار
        if deleted_count > 0:
            self.logger.info(
                f"🗑️  آمار حذف: {deleted_count} کل, {moved_to_trash} به سطل بازیافت, {permanent_deleted} دائم")

        return deleted_count

    def _apply_auto_deletion(self):
        """اعمال حذف خودکار"""
        if not self.file_sets:
            return

        # منطق حذف خودکار (مثال)
        to_delete = []
        for group in self.file_sets:
            if len(group) > 1:
                # استراتژی: اولین فایل را نگه دار، بقیه حذف شوند
                to_delete.extend(group[1:])

        if to_delete:
            self._safe_delete_files(to_delete, use_recycle_bin=False)

    def _force_delete_file(self, file_path):
        """حذف اجباری فایل"""
        try:
            # تغییر permission
            os.chmod(file_path, stat.S_IWRITE)
            os.remove(file_path)
            return True
        except Exception as e:
            self.logger.error(f"حذف اجباری ناموفق: {e}")
            return False

    def _create_backup(self, file_path):
        """ایجاد بک‌آپ از فایل قبل از حذف"""
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            filename = os.path.basename(file_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # کپی فایل به پوشه بک‌آپ
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"بک‌آپ ایجاد شد: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.warning(f"خطا در ایجاد بک‌آپ: {e}")
            return None

    def restore_from_backup(self, backup_path, original_path=None):
        """بازیابی فایل از بک‌آپ"""
        try:
            if not os.path.exists(backup_path):
                return False, "فایل بک‌آپ یافت نشد"

            if original_path is None:
                # استخراج نام اصلی از نام بک‌آپ
                filename = "_".join(os.path.basename(backup_path).split("_")[2:])
                original_path = os.path.join(os.path.dirname(backup_path), "..", filename)
                original_path = os.path.normpath(original_path)

            # ایجاد پوشه مقصد اگر وجود ندارد
            os.makedirs(os.path.dirname(original_path), exist_ok=True)

            shutil.copy2(backup_path, original_path)
            self.logger.info(f"✅ بازیابی موفق: {os.path.basename(original_path)}")
            return True, "بازیابی موفق"
        except Exception as e:
            self.logger.error(f"خطا در بازیابی: {e}")
            return False, str(e)

    def _is_system_file(self, file_path):
        """بررسی اینکه آیا فایل سیستمی است"""
        system_keywords = ['windows', 'system32', 'program files', '$', 'temp']
        lower_path = file_path.lower()
        return any(keyword in lower_path for keyword in system_keywords)

    def _apply_auto_deletion(self):
        """اعمال حذف خودکار"""
        if not self.file_sets:
            return

        updated_sets = []
        for file_group in self.file_sets:
            if len(file_group) <= 1:
                updated_sets.append(file_group)
                continue

    def load_files(self, prioritize_old=False):
        """بارگذاری فایل‌ها با امکان فیلتر کردن"""
        start_time = time.time()

        try:
            # استفاده از finder بهینه‌سازی شده
            finder = FileFinder(self.folder_selected)

            # تنظیم پوشه‌های استثنا
            exclude_folders = [
                os.path.join(self.folder_selected, "000"),
                os.path.join(self.folder_selected, "_backup_deleted"),
                self.backup_dir
            ]
            finder.exclude_folders = exclude_folders

            self.file_sets = finder.find_files()

            if self.auto_delete:
                self._apply_auto_deletion()  # ✅ یا این متد را تعریف کنید

            print(f"زمان بارگذاری: {time.time() - start_time:.2f} ثانیه")
            return self.file_sets

            elapsed = time.time() - start_time
            self.logger.info(f"بارگذاری فایل‌ها: {len(self.file_sets)} گروه در {elapsed:.2f} ثانیه")

            return self.file_sets

        except Exception as e:
            self.logger.error(f"خطا در بارگذاری فایل‌ها: {e}")
            raise

    def undo_last_deletion(self):
        """بازگرداندن آخرین حذف - IMPLEMENTED"""
        if not self.successful_deletions:
            return False, "هیچ حذفی برای بازگرداندن وجود ندارد"

        try:
            # گرفتن آخرین حذف
            file_path, backup_path = self.successful_deletions[-1]

            # بررسی وجود بک‌آپ
            if not backup_path or not os.path.exists(backup_path):
                return False, "فایل بک‌آپ یافت نشد"

            # ایجاد پوشه مقصد اگر وجود ندارد
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # کپی بک‌آپ به محل اصلی
            shutil.copy2(backup_path, file_path)

            # حذف از لیست موفق‌ها
            self.successful_deletions.pop()

            # حذف فایل بک‌آپ (اختیاری)
            try:
                os.remove(backup_path)
            except:
                pass

            # اضافه کردن به file_sets اگر لازم است
            file_added = False
            for group in self.file_sets:
                if any(f in backup_path for f in group):  # اگر مربوط به این گروه است
                    group.append(file_path)
                    file_added = True
                    break

            if not file_added:
                # ایجاد گروه جدید
                self.file_sets.append([file_path])

            self.logger.info(f"✅ بازگردانی موفق: {os.path.basename(file_path)}")
            return True, "بازگردانی موفق"

        except Exception as e:
            self.logger.error(f"❌ خطا در بازگردانی: {e}")
            return False, str(e)