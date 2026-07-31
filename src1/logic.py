# src1/logic.py
import os
import time
import stat
import shutil
from src1.finder import FileFinder
from src.log_manager import log_manager


class FileHandler:
    def __init__(self, folder_selected, priority_folder, keep_folder, backup_deleted,
                 auto_delete=False):  # ✅ auto_delete=False
        self.folder_selected = folder_selected
        self.priority_folder = priority_folder
        self.keep_folder = keep_folder
        self.backup_dir = backup_deleted
        self.auto_delete = auto_delete  # ✅ پیش‌فرض False
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.failed_deletions = []
        self.successful_deletions = []
        self.use_recycle_bin = True
        self.progress_callback = None

        self.logger = log_manager.get_logger("FileHandler")

        # ایجاد پوشه‌ها
        for folder in [self.backup_dir, self.keep_folder, self.priority_folder]:
            if folder and not os.path.exists(folder):
                os.makedirs(folder)
                self.logger.info(f"✅ پوشه ایجاد شد: {folder}")

        self.logger.info(f"FileHandler ساخته شد برای پوشه: {folder_selected}")
        self.logger.info(f"📁 پوشه اولویت نگهداری: {self.keep_folder}")
        self.logger.info(f"📁 پوشه انتقال فایل های تکراری: {self.backup_dir}")
        self.logger.info(f"🔄 حذف خودکار: {'فعال' if self.auto_delete else 'غیرفعال'}")

        # بارگذاری فایل‌ها بدون حذف خودکار
        self.load_files()

    def set_progress_callback(self, callback):
        """تنظیم callback برای گزارش پیشرفت"""
        self.progress_callback = callback
        self.logger.info("✅ progress_callback تنظیم شد")

    # ✅ متد انتقال به پوشه backup_deleted
    def _move_to_backup_folder(self, file_path):
        """انتقال فایل به پوشه backup_deleted با مدیریت نام تکراری"""
        try:
            if not self.backup_dir:
                return False, "پوشه backup_deleted تعریف نشده است"

            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.backup_dir, filename)

            # اگر فایل با همین نام وجود دارد، timestamp اضافه کن
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                new_filename = f"{name}_{timestamp}{ext}"
                dest_path = os.path.join(self.backup_dir, new_filename)
                self.logger.info(f"⚠️ فایل تکراری: {filename} -> {new_filename}")

            shutil.move(file_path, dest_path)
            self.logger.info(f"✅ فایل منتقل شد: {os.path.basename(file_path)} -> {os.path.basename(dest_path)}")
            return True, f"منتقل به {dest_path}"

        except Exception as e:
            self.logger.error(f"❌ خطا در انتقال فایل {file_path}: {e}")
            return False, str(e)

    def _safe_delete_files(self, files_to_delete, use_recycle_bin=True):
        """انتقال فایل‌ها به پوشه backup_deleted"""
        deleted_count = 0
        moved_to_backup = 0

        for file_path in files_to_delete:
            try:
                if not os.path.exists(file_path):
                    self.logger.warning(f"فایل وجود ندارد: {file_path}")
                    continue

                if self._is_system_file(file_path):
                    self.logger.warning(f"فایل سیستمی - رد شد: {file_path}")
                    self.failed_deletions.append((file_path, "فایل سیستمی"))
                    continue

                # ✅ انتقال به پوشه backup_deleted
                if self.backup_dir:
                    success, message = self._move_to_backup_folder(file_path)
                    if success:
                        moved_to_backup += 1
                        deleted_count += 1
                        self.successful_deletions.append((file_path, self.backup_dir))
                        self.logger.info(f"✅ انتقال به backup_deleted: {os.path.basename(file_path)}")
                    else:
                        self.logger.error(f"❌ انتقال ناموفق: {file_path} - {message}")
                        self.failed_deletions.append((file_path, message))
                else:
                    # Fallback: حذف واقعی
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.info(f"✅ حذف موفق: {os.path.basename(file_path)}")
                    except Exception as e:
                        self.logger.error(f"❌ خطا در حذف {file_path}: {e}")
                        self.failed_deletions.append((file_path, str(e)))

            except Exception as e:
                self.logger.exception(f"❌ خطای غیرمنتظره در حذف {file_path}")
                self.failed_deletions.append((file_path, str(e)))

        if deleted_count > 0:
            self.logger.info(f"🗑️ آمار انتقال: {deleted_count} کل, {moved_to_backup} به backup_deleted")

        return deleted_count

    # ❌ متد _apply_auto_deletion کاملاً حذف شده - دیگر استفاده نمی‌شود

    def _force_delete_file(self, file_path):
        """حذف اجباری فایل"""
        try:
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
                filename = "_".join(os.path.basename(backup_path).split("_")[2:])
                original_path = os.path.join(os.path.dirname(backup_path), "..", filename)
                original_path = os.path.normpath(original_path)

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

    def load_files(self, prioritize_old=False):
        """بارگذاری فایل‌ها - بدون حذف خودکار"""
        start_time = time.time()

        try:
            finder = FileFinder(
                self.folder_selected,
                progress_callback=self.progress_callback
            )

            exclude_folders = [
                os.path.join(self.folder_selected, "000"),
                self.backup_dir,
                self.keep_folder,  # ✅ اضافه کردن keep_folder به استثناها
                self.priority_folder  # ✅ اضافه کردن priority_folder به استثناها
            ]
            finder.exclude_folders = [f for f in exclude_folders if f]

            self.file_sets = finder.find_files()

            # ❌ حذف خودکار غیرفعال است - کاربر در GUI تصمیم می‌گیرد
            # if self.auto_delete:
            #     self._apply_auto_deletion()

            elapsed = time.time() - start_time
            self.logger.info(f"بارگذاری فایل‌ها: {len(self.file_sets)} گروه در {elapsed:.2f} ثانیه")
            self.logger.info("ℹ️ حذف خودکار غیرفعال است - کاربر در GUI تصمیم می‌گیرد")

            return self.file_sets

        except Exception as e:
            self.logger.error(f"خطا در بارگذاری فایل‌ها: {e}")
            raise

    def undo_last_deletion(self):
        """بازگرداندن آخرین حذف - از backup_deleted"""
        if not self.successful_deletions:
            return False, "هیچ حذفی برای بازگرداندن وجود ندارد"

        try:
            file_path, dest_folder = self.successful_deletions[-1]

            if dest_folder == self.backup_dir:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.backup_dir, filename)

                if not os.path.exists(dest_path):
                    for f in os.listdir(self.backup_dir):
                        if filename in f:
                            dest_path = os.path.join(self.backup_dir, f)
                            break
                    else:
                        return False, "فایل در backup_deleted یافت نشد"

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                shutil.move(dest_path, file_path)

                self.successful_deletions.pop()
                self.logger.info(f"✅ بازگردانی موفق: {os.path.basename(file_path)}")
                return True, "بازگردانی موفق"
            else:
                backup_path = dest_folder
                if not backup_path or not os.path.exists(backup_path):
                    return False, "فایل بک‌آپ یافت نشد"

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                shutil.copy2(backup_path, file_path)
                self.successful_deletions.pop()

                try:
                    os.remove(backup_path)
                except:
                    pass

                self.logger.info(f"✅ بازگردانی موفق: {os.path.basename(file_path)}")
                return True, "بازگردانی موفق"

        except Exception as e:
            self.logger.error(f"❌ خطا در بازگردانی: {e}")
            return False, str(e)