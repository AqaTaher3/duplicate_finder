from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import shutil
import stat
import time
from datetime import datetime
from tqdm import tqdm
import math
import json
import xxhash
import ctypes
from src2.delete_empty_folders import delete_empty_folders


class SmartMusicSync:
    STATE_FILENAME = ".sync_state.json"

    def __init__(self, source_dir, dest_dir, exclude_ext=None, exclude_dir_substrings=None, max_workers=4):
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.exclude_ext = exclude_ext or []
        self.exclude_dir_substrings = exclude_dir_substrings or []
        self.max_workers = max_workers
        self.sync_log = "sync_log.txt"
        self.stats = {
            'copied': 0,
            'deleted': 0,
            'skipped': 0,
            'total_files': 0,
            'total_size': 0,
            'start_time': None
        }
        self.state = {
            "hashes": {},
            "meta": {},
            "hash_algo": "xxh64"
        }
        self.load_state()
        # قفل برای دسترسی thread-safe به state
        self.state_lock = threading.Lock()

    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def format_time(self, seconds):
        if seconds < 60:
            return f"{seconds:.1f} ثانیه"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} دقیقه"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} ساعت"

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        print(log_entry.strip())
        with open(self.sync_log, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def load_state(self):
        state_path = os.path.join(self.dest_dir, self.STATE_FILENAME)
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception as e:
                self.log_message(f"خطا در بارگذاری فایل وضعیت: {e}")
        else:
            self.state = {
                "hashes": {},
                "meta": {},
                "hash_algo": "xxh64"
            }

    def save_state(self):
        state_path = os.path.join(self.dest_dir, self.STATE_FILENAME)
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"خطا در ذخیره فایل وضعیت: {e}")

    def calculate_file_hash(self, file_path):
        """محاسبه هش فایل"""
        try:
            hasher = xxhash.xxh64()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):  # افزایش بافر به 64KB
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.log_message(f"خطا در محاسبه هش فایل {file_path}: {e}")
            return None

    def get_file_hash_with_cache(self, file_path, is_source_file=False):
        """دریافت هش فایل با کش کردن - thread-safe"""
        try:
            # تعیین کلید برای کش
            if is_source_file:
                rel_path = os.path.relpath(file_path, self.source_dir)
            else:
                # برای فایل‌های مقصد یا دیگر فایل‌ها
                if file_path.startswith(self.dest_dir):
                    rel_path = os.path.relpath(file_path, self.dest_dir)
                else:
                    rel_path = file_path

            with self.state_lock:
                # بررسی کش
                if rel_path in self.state["hashes"]:
                    meta = self.state.get("meta", {}).get(rel_path)
                    if meta:
                        try:
                            st = os.stat(file_path)
                            if st.st_mtime == meta.get("mtime") and st.st_size == meta.get("size"):
                                return self.state["hashes"][rel_path]
                        except Exception:
                            pass

                # محاسبه هش جدید
                file_hash = self.calculate_file_hash(file_path)

                if file_hash:
                    # ذخیره در کش
                    st = os.stat(file_path)
                    self.state["hashes"][rel_path] = file_hash
                    if "meta" not in self.state:
                        self.state["meta"] = {}
                    self.state["meta"][rel_path] = {
                        "mtime": st.st_mtime,
                        "size": st.st_size
                    }

                return file_hash
        except Exception as e:
            self.log_message(f"خطا در get_file_hash برای {file_path}: {e}")
            return None

    def quick_compare_files(self, source_file, dest_file):
        """مقایسه سریع دو فایل با استفاده از metadata"""
        try:
            src_stat = os.stat(source_file)
            dst_stat = os.stat(dest_file)

            # اول سایز را چک کن (سریعترین)
            if src_stat.st_size != dst_stat.st_size:
                return False, "سایز متفاوت"

            # سپس زمان تغییر
            if src_stat.st_mtime != dst_stat.st_mtime:
                return False, "تاریخ تغییر متفاوت"

            # اگر هر دو یکی بودند، احتمالاً فایل یکسان است
            return True, "یکسان"
        except Exception as e:
            return False, f"خطا در مقایسه: {e}"

    def get_all_files(self, directory, is_source=False):
        """اسکن تمام فایل‌های دایرکتوری"""
        print(f"🔍 در حال اسکن تمام فایل‌ها در: {directory}")

        all_files = []
        for root, dirs, files in os.walk(directory):
            rel_root = os.path.relpath(root, directory)

            # حذف پوشه‌هایی که شامل هرکدوم از رشته‌های exclude_dir_substrings باشند
            if any(substr in part for substr in self.exclude_dir_substrings for part in rel_root.split(os.sep)):
                dirs[:] = []
                continue

            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in self.exclude_ext:
                    continue
                full_path = os.path.join(root, file)
                all_files.append(full_path)

        files_info = {}
        for full_path in tqdm(all_files, desc="📁 اسکن فایل‌ها", unit="file", ncols=100):
            try:
                # مسیر نسبی نسبت به دایرکتوری جاری
                rel_path = os.path.relpath(full_path, directory)
                stat = os.stat(full_path)
                files_info[rel_path] = {
                    'full_path': full_path,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'is_source': is_source  # اضافه کردن پرچم منبع بودن
                }
            except Exception as e:
                self.log_message(f"خطا در خواندن فایل {full_path}: {e}")

        return files_info

    def get_partial_hash(self, file_path, chunk_size=65536):
        """محاسبه هش فقط روی بخش ابتدایی فایل (مثلاً 64KB)"""
        try:
            hasher = xxhash.xxh64()
            with open(file_path, "rb") as f:
                chunk = f.read(chunk_size)
                hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.log_message(f"خطا در محاسبه هش جزئی فایل {file_path}: {e}")
            return None

    def process_file_comparison(self, item):
        rel_path, source_info = item
        source_file = source_info['full_path']
        dest_file = os.path.join(self.dest_dir, rel_path)

        if not os.path.exists(dest_file):
            return (rel_path, source_info, "جدید", True)

        source_size = source_info.get('size') or os.path.getsize(source_file)
        dest_size = os.path.getsize(dest_file)
        if source_size != dest_size:
            return (rel_path, source_info, "اندازه متفاوت", True)

        source_mtime = source_info.get('mtime') or os.path.getmtime(source_file)
        dest_mtime = os.path.getmtime(dest_file)
        if abs(source_mtime - dest_mtime) > 1:
            return (rel_path, source_info, "تاریخ متفاوت", True)

        # حالا به جای هش کامل، هش جزئی بگیریم
        source_partial_hash = self.get_partial_hash(source_file)
        dest_partial_hash = self.get_partial_hash(dest_file)

        if source_partial_hash != dest_partial_hash:
            return (rel_path, source_info, "هش جزئی متفاوت", True)
        else:
            # اگر هش جزئی برابر بود، می‌توان به‌عنوان "برابر" قبول کرد
            return (rel_path, source_info, "برابر (هش جزئی)", False)

    def is_admin(self):
        """بررسی دسترسی ادمین"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def remove_empty_dirs(self, path):
        """حذف پوشه‌های خالی با دادن دسترسی کامل"""
        if not os.path.isdir(path):
            return

        for root, dirs, files in os.walk(path, topdown=False):
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    # بررسی خالی بودن پوشه
                    if not os.listdir(dir_path):
                        try:
                            # اول سعی کن با دسترسی عادی حذف کن
                            os.rmdir(dir_path)
                            self.log_message(f"حذف پوشه خالی: {os.path.relpath(dir_path, self.dest_dir)}")
                        except Exception as e:
                            # اگر نشد، دسترسی کامل بده
                            try:
                                # حذف همه محدودیت‌های دسترسی
                                os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # 0777
                                os.rmdir(dir_path)
                                self.log_message(
                                    f"حذف پوشه خالی (دسترسی کامل داده شد): {os.path.relpath(dir_path, self.dest_dir)}")
                            except Exception as e2:
                                self.log_message(f"خطا در حذف پوشه {dir_path}: {e2}")
                    else:
                        # پوشه خالی نیست - ممکن است فایل‌های پنهان داشته باشد
                        pass
                except Exception as e:
                    self.log_message(f"خطا در بررسی پوشه {dir_path}: {e}")

    def force_remove_file(self, file_path):
        """حذف اجباری فایل با دسترسی کامل"""
        try:
            os.remove(file_path)
            return True
        except PermissionError:
            try:
                # دادن دسترسی کامل به فایل
                os.chmod(file_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                os.remove(file_path)
                return True
            except Exception as e:
                self.log_message(f"خطای دسترسی در حذف فایل {file_path}: {e}")
                return False

    def sync_files(self):
        # self.stats['start_time'] = time.time()
        self.log_message(f"شروع سینک از {self.source_dir} به {self.dest_dir}")
        if not self.is_admin():
            print("⚠️  توجه: برنامه بدون دسترسی ادمین اجرا شده.")
            print("   ممکن است برخی پوشه‌های خالی حذف نشوند.")
            print("   برای حذف کامل، برنامه را با Run as administrator اجرا کنید.")
        print("🔄 در حال آماده‌سازی برای سینک...")

        # اسکن فایل‌های منبع و مقصد به صورت موازی
        print("📂 در حال اسکن فایل‌ها...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            source_future = executor.submit(self.get_all_files, self.source_dir, True)
            dest_future = executor.submit(self.get_all_files, self.dest_dir, False)

            source_files = source_future.result()
            dest_files = dest_future.result()

        self.stats['total_files'] = len(source_files)
        self.stats['total_size'] = sum(f['size'] for f in source_files.values())

        print(f"📊 آمار فایل‌ها:")
        print(f"   • منبع: {len(source_files)} فایل ({self.format_size(self.stats['total_size'])})")
        print(f"   • مقصد: {len(dest_files)} فایل")
        print("─" * 60)

        # حذف فایل‌هایی که در منبع نیستند
        files_to_delete = [rel_path for rel_path in dest_files if rel_path not in source_files]
        if files_to_delete:
            print(f"🗑️  در حال حذف {len(files_to_delete)} فایل قدیمی...")
            for rel_path in tqdm(files_to_delete, desc="حذف فایل‌ها", unit="file", ncols=100):
                try:
                    dest_file_path = os.path.join(self.dest_dir, rel_path)
                    os.remove(dest_file_path)

                    # حذف از کش
                    with self.state_lock:
                        if rel_path in self.state["hashes"]:
                            del self.state["hashes"][rel_path]
                        if rel_path in self.state.get("meta", {}):
                            del self.state["meta"][rel_path]

                    self.stats['deleted'] += 1
                    self.log_message(f"حذف شده: {rel_path}")
                except Exception as e:
                    self.log_message(f"خطا در حذف {rel_path}: {e}")

            # حذف پوشه‌های خالی در مقصد بعد از حذف فایل‌ها
            self.remove_empty_dirs(self.dest_dir)

        # بررسی فایل‌های جدید یا تغییر کرده با استفاده از ThreadPool
        print("🔍 در حال بررسی فایل‌های نیازمند به روزرسانی...")
        files_to_copy = []

        # آماده کردن لیست فایل‌ها برای پردازش موازی
        file_items = list(source_files.items())

        # استفاده از ThreadPoolExecutor برای پردازش موازی
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # ارسال همه کارها به executor
            future_to_item = {
                executor.submit(self.process_file_comparison, item): item
                for item in file_items
            }

            # پردازش نتایج با پیشرفت‌بار
            with tqdm(total=len(file_items), desc="بررسی تغییرات", unit="file", ncols=100) as pbar:
                for future in as_completed(future_to_item):
                    rel_path, source_info, reason, needs_copy = future.result()

                    if needs_copy:
                        files_to_copy.append((rel_path, source_info, reason))
                    elif "برابر" in reason:
                        self.stats['skipped'] += 1

                    pbar.update(1)
                    pbar.set_postfix({
                        "کپی": len(files_to_copy),
                        "رد": self.stats['skipped']
                    })

        if files_to_copy:
            total_copy_size = sum(info['size'] for _, info, _ in files_to_copy)
            print(f"📤 در حال کپی {len(files_to_copy)} فایل ({self.format_size(total_copy_size)})...")

            with tqdm(total=total_copy_size, desc="کپی فایل‌ها", unit="B",
                      unit_scale=True, unit_divisor=1024, ncols=100) as pbar:

                for rel_path, source_info, reason in files_to_copy:
                    try:
                        source_file = source_info['full_path']
                        dest_file = os.path.join(self.dest_dir, rel_path)

                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        shutil.copy2(source_file, dest_file)

                        self.stats['copied'] += 1
                        pbar.update(source_info['size'])
                        self.log_message(f"کپی شده ({reason}): {rel_path}")

                    except Exception as e:
                        self.log_message(f"خطا در کپی {rel_path}: {e}")
        else:
            print("✅ همه فایل‌ها به روز هستند!")

        self.show_final_stats()
        self.save_state()

    def show_final_stats(self):
        end_time = time.time()
        # duration = end_time - self.stats['start_time']
        duration = end_time - time.time()

        print("═" * 60)
        print("📈 آمار نهایی سینک")
        print("═" * 60)
        print(f"🕒 مدت زمان: {self.format_time(duration)}")
        print(f"📁 کل فایل‌ها: {self.stats['total_files']} فایل")
        print(f"💾 حجم کل: {self.format_size(self.stats['total_size'])}")
        print(f"🟢 کپی شده: {self.stats['copied']} فایل")
        print(f"🔴 حذف شده: {self.stats['deleted']} فایل")
        print(f"⚪ بدون تغییر: {self.stats['skipped']} فایل")

        if duration > 0:
            speed = self.stats['total_size'] / duration
            speed_per_file = self.stats['total_files'] / duration
            print(f"🚀 سرعت متوسط: {self.format_size(speed)}/ثانیه")
            print(f"📊 سرعت پردازش: {speed_per_file:.1f} فایل/ثانیه")

        print("═" * 60)

        self.log_message(
            f"سینک کامل شد - "
            f"کپی: {self.stats['copied']}, "
            f"حذف: {self.stats['deleted']}, "
            f"بدون تغییر: {self.stats['skipped']}, "
            f"مدت زمان: {self.format_time(duration)}"
        )


def main():
    source_dir = r"Z:/Music"
    dest_dir = r"E:/"

    exclude_formats = [
        ".txt", ".jpg", ".png", ".zip",
        ".dat", ".mp4", ".mpg", ".mkv", ".wmv",
        ".ts", ".avi", ".flv", ".3gp",
        ".mov", ".m4v", ".mpeg", ".vob", "mpeg"
    ]

    exclude_dir_substrings = ["temp", "dontcopy",
                              "000", "Zont_copy"]

    print("═" * 60)
    print("🎵 سینک هوشمند فایل‌ها - نسخه سریع با پردازش موازی")
    print("═" * 60)
    print(f"📁 منبع (هارد): {source_dir}")
    print(f"💾 مقصد (رم): {dest_dir}")
    print(f"🔢 تعداد threadها: 4")
    print("═" * 60)
    print("🚀 شروع فرآیند سینک...")

    delete_empty_folders(dest_dir, dry_run=False, verbose=True)
    sync = SmartMusicSync(
        source_dir, dest_dir,
        exclude_ext=exclude_formats,
        exclude_dir_substrings=exclude_dir_substrings,
        max_workers=4  # تعداد threadها برای پردازش موازی
    )
    sync.sync_files()
    delete_empty_folders(dest_dir, dry_run=False, verbose=True)
    delete_empty_folders(source_dir, dry_run=False, verbose=True)


if __name__ == "__main__":
    main()