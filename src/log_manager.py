# file: log_manager.py
import logging
import logging.handlers
import os
import sys
import atexit
from datetime import datetime
import multiprocessing


class LogManager:
    """مدیریت متمرکز لاگ‌گیری برای تمام ماژول‌ها"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, app_name="FileCleaner", log_dir="logs"):
        # جلوگیری از راه‌اندازی مجدد در فرایندهای child
        if self._initialized:
            return

        self.app_name = app_name
        self.log_dir = log_dir
        self._initialized = True

        # فقط در فرایند اصلی راه‌اندازی کن
        if self._is_main_process():
            self._setup_logging()
            atexit.register(self.log_shutdown)
        else:
            # در فرایندهای child سیستم ساده‌تر
            self._setup_simple_logging()

    def _is_main_process(self):
        """بررسی آیا در فرایند اصلی هستیم"""
        try:
            return multiprocessing.current_process().name == 'MainProcess'
        except:
            return True  # اگر multiprocessing کار نکرد، فرض کن اصلی هستیم

    def _setup_logging(self):
        """راه‌اندازی کامل سیستم لاگ‌گیری در فرایند اصلی"""

        # ایجاد پوشه لاگ‌ها اگر وجود ندارد
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # ایجاد logger اصلی
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)

        # جلوگیری از انتشار به loggerهای والد
        self.logger.propagate = False

        # فرمت لاگ
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s.%(funcName)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 1. File Handler با Rotation
        log_file = os.path.join(self.log_dir, f"{self.app_name}_{datetime.now().strftime('%Y%m')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=12,  # نگهداری 12 فایل قبلی
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # 2. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        # 3. Error File Handler (فقط خطاها)
        error_file = os.path.join(self.log_dir, "errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=6,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # حذف handlerهای قدیمی (اگر وجود دارند)
        if self.logger.handlers:
            self.logger.handlers.clear()

        # اضافه کردن handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)

    def _setup_simple_logging(self):
        """راه‌اندازی لاگ‌گیری ساده برای فرایندهای child"""
        self.logger = logging.getLogger(f"{self.app_name}.child")
        self.logger.setLevel(logging.WARNING)  # فقط خطاها و هشدارها

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

    def get_logger(self, module_name=None):
        """دریافت logger برای ماژول خاص"""
        if not hasattr(self, 'logger'):
            self._setup_simple_logging()

        if module_name:
            name = f"{self.app_name}.{module_name}"
            # اگر در child process هستیم، پسوند child اضافه کن
            if not self._is_main_process():
                name = f"{name}.child"
            return logging.getLogger(name)

        return self.logger

    def log_operation(self, operation, details):
        """لاگ‌گیری عملیات مهم"""
        if self._is_main_process():
            self.logger.info(f"OPERATION: {operation} | DETAILS: {details}")

    def log_file_deletion(self, file_path, success, error_msg=None):
        """لاگ‌گیری حذف فایل"""
        status = "SUCCESS" if success else "FAILED"
        message = f"DELETE: {file_path} | STATUS: {status}"
        if error_msg:
            message += f" | ERROR: {error_msg}"

        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)

    def log_startup(self):
        """لاگ‌گیری شروع برنامه - فقط در فرایند اصلی"""
        if not self._is_main_process():
            return

        import platform
        import getpass

        system_info = {
            'os': platform.system(),
            'version': platform.version(),
            'user': getpass.getuser(),
            'python': platform.python_version(),
            'timestamp': datetime.now().isoformat()
        }

        self.logger.info("=" * 50)
        self.logger.info(f"APPLICATION STARTED - {self.app_name}")
        self.logger.info(f"System Info: {system_info}")
        self.logger.info("=" * 50)

    def log_shutdown(self):
        """لاگ‌گیری خاموشی برنامه - فقط در فرایند اصلی"""
        if not self._is_main_process():
            return

        self.logger.info("=" * 50)
        self.logger.info(f"APPLICATION SHUTDOWN - {self.app_name}")
        self.logger.info("=" * 50)


# Singleton Instance
log_manager = LogManager()