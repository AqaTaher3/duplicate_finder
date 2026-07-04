# src1/logic.py
import os
import time
import stat
import shutil
from src1.finder import FileFinder
from src.log_manager import log_manager


class FileHandler:
    def __init__(self, folder_selected, priority_folder, keep_folder, backup_deleted,
                 auto_delete=True):
        self.folder_selected = folder_selected
        self.priority_folder = priority_folder
        self.keep_folder = keep_folder
        self.backup_deleted = backup_deleted
        self.auto_delete = auto_delete
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.failed_deletions = []
        self.successful_deletions = []
        self.use_recycle_bin = True
        self.progress_callback = None

        self.logger = log_manager.get_logger("FileHandler")

        # ایجاد پوشه‌ها
        if not os.path.exists(self.backup_deleted):
            os.makedirs(self.backup_deleted)


        self.logger.info(f"FileHandler ساخته شد برای پوشه: {folder_selected}")
        self.load_files()

    def set_progress_callback(self, callback):
        """تنظیم callback برای گزارش پیشرفت"""
        self.progress_callback = callback
        self.logger.info("✅ progress_callback تنظیم شد")

    def _safe_delete_files(self, files_to_delete, use_recycle_bin=True):
        """✅ انتقال فایل‌ها به پوشه backup_deleted به جای حذف"""
        deleted_count = 0
        moved_to_deleted = 0

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

                # ✅ انتقال به پوشه backup_deleted
                if self.backup_deleted:
                    success, message = self.backup_deleted(file_path)
                    if success:
                        moved_to_deleted += 1
                        deleted_count += 1
                        self.successful_deletions.append((file_path, self.backup_deleted))
                        self.logger.info(f"✅ انتقال به backup_deleted: {os.path.basename(file_path)}")
                    else:
                        self.logger.error(f"❌ انتقال ناموفق: {file_path} - {message}")
                        self.failed_deletions.append((file_path, message))
                else:
                    # اگر پوشه backup_deleted تعریف نشده، از روش قبلی استفاده کن
                    self.logger.warning(f"⚠️ پوشه backup_deleted تعریف نشده، استفاده از روش قبلی")

                    # ایجاد بک‌آپ
                    backup_path = self._create_backup(file_path)

                    if use_recycle_bin and self.use_recycle_bin:
                        try:
                            import send2trash
                            send2trash.send2trash(file_path)
                            deleted_count += 1
                            self.successful_deletions.append((file_path, backup_path))
                            self.logger.info(f"✅ انتقال به سطل بازیافت: {os.path.basename(file_path)}")
                            continue
                        except Exception as e:
                            self.logger.warning(f"خطا در انتقال به سطل بازیافت: {e}")

                    # حذف دائم
                    try:
                        os.remove(file_path)
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
                f"🗑️  آمار انتقال: {deleted_count} کل, {moved_to_deleted} به backup_deleted"
            )

        return deleted_count

    # ✅ متد جدید برای انتقال به پوشه backup_deleted
    def _move_to_backup_deleted(self, file_path):
        """انتقال فایل به پوشه backup_deleted با مدیریت نام تکراری"""
        try:
            if not self.backup_deleted:
                return False, "پوشه backup_deleted تعریف نشده است"

            # ایجاد پوشه اگر وجود ندارد
            if not os.path.exists(self.backup_deleted):
                os.makedirs(self.backup_deleted)

            # نام فایل
            filename = os.path.basename(file_path)

            # مسیر کامل در پوشه مقصد
            dest_path = os.path.join(self.backup_deleted, filename)

            # اگر فایل با همین نام وجود دارد، نام جدید ایجاد کن
            if os.path.exists(dest_path):
                # اضافه کردن timestamp به نام فایل
                name, ext = os.path.splitext(filename)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                new_filename = f"{name}_{timestamp}{ext}"
                dest_path = os.path.join(self.backup_deleted, new_filename)
                self.logger.info(f"⚠️ فایل تکراری: {filename} -> {new_filename}")

            # انتقال فایل
            shutil.move(file_path, dest_path)

            self.logger.info(f"✅ فایل منتقل شد: {file_path} -> {dest_path}")
            return True, f"منتقل به {dest_path}"

        except Exception as e:
            self.logger.error(f"❌ خطا در انتقال فایل {file_path}: {e}")
            return False, str(e)

    def _apply_auto_deletion(self):
        """اعمال حذف خودکار با انتقال به backup_deleted"""
        if not self.file_sets:
            return

        to_delete = []
        for group in self.file_sets:
            if len(group) > 1:
                to_delete.extend(group[1:])

        if to_delete:
            self._safe_delete_files(to_delete, use_recycle_bin=False)

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
            if not os.path.exists(self.backup_deleted):
                os.makedirs(self.backup_deleted)

            filename = os.path.basename(file_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.backup_deleted, backup_name)

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
        """بارگذاری فایل‌ها با پشتیبانی از پیشرفت"""
        start_time = time.time()

        try:
            finder = FileFinder(
                self.folder_selected,
                progress_callback=self.progress_callback
            )

            exclude_folders = [
                os.path.join(self.folder_selected, "000"),
                os.path.join(self.folder_selected, "_backup_deleted"),
                self.backup_deleted
            ]
            finder.exclude_folders = [f for f in exclude_folders if f]  # حذف None

            self.file_sets = finder.find_files()

            if self.auto_delete:
                self._apply_auto_deletion()

            elapsed = time.time() - start_time
            self.logger.info(f"بارگذاری فایل‌ها: {len(self.file_sets)} گروه در {elapsed:.2f} ثانیه")

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

            # اگر به backup_deleted منتقل شده بود
            if dest_folder == self.backup_deleted:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.backup_deleted, filename)

                # پیدا کردن فایل در backup_deleted (ممکن است نام تغییر کرده باشد)
                if not os.path.exists(dest_path):
                    # جستجوی فایل‌های مشابه
                    for f in os.listdir(self.backup_deleted):
                        if filename in f:
                            dest_path = os.path.join(self.backup_deleted, f)
                            break
                    else:
                        return False, "فایل در backup_deleted یافت نشد"

                # بازگرداندن به محل اصلی
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                shutil.move(dest_path, file_path)

                self.successful_deletions.pop()
                self.logger.info(f"✅ بازگردانی موفق: {os.path.basename(file_path)}")
                return True, "بازگردانی موفق"
            else:
                # روش قبلی برای بازگردانی از بک‌آپ
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