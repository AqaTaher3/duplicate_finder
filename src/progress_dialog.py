# src/progress_dialog.py - نسخه اصلاح شده

import wx
import threading
import time
from src.log_manager import log_manager


class ProgressDialog(wx.Dialog):
    """پنجره نمایش پیشرفت با قابلیت اجرای تابع در ترد جداگانه"""

    def __init__(self, parent, title="در حال پردازش", message="لطفاً صبر کنید..."):
        super().__init__(parent, title=title, size=(550, 180),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.logger = log_manager.get_logger("ProgressDialog")
        self.is_cancelled = False
        self.is_finished = False
        self.progress = 0
        self.status_message = ""
        self._lock = threading.Lock()
        self._is_modal = False  # ✅ اضافه شده برای پیگیری وضعیت Modal

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        vbox = wx.BoxSizer(wx.VERTICAL)

        # عنوان و پیام
        self.title_label = wx.StaticText(panel, label=title)
        self.title_label.SetForegroundColour(wx.Colour(230, 210, 181))
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        vbox.Add(self.title_label, 0, wx.ALL | wx.CENTER, 5)

        # پیام وضعیت
        self.message_label = wx.StaticText(panel, label=message)
        self.message_label.SetForegroundColour(wx.Colour(200, 200, 200))
        font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.message_label.SetFont(font)
        vbox.Add(self.message_label, 0, wx.ALL | wx.CENTER, 5)

        # نوار پیشرفت
        self.progress_bar = wx.Gauge(panel, range=100, size=(500, 25))
        vbox.Add(self.progress_bar, 0, wx.ALL | wx.EXPAND, 10)

        # توضیحات وضعیت دقیق
        self.status_text = wx.StaticText(panel, label="آماده‌سازی...")
        self.status_text.SetForegroundColour(wx.Colour(180, 180, 180))
        self.status_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        vbox.Add(self.status_text, 0, wx.ALL | wx.CENTER, 5)

        # دکمه‌ها
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_cancel = wx.Button(panel, label="لغو", size=(80, 30))
        self.btn_cancel.SetBackgroundColour(wx.Colour(220, 53, 69))
        self.btn_cancel.SetForegroundColour(wx.WHITE)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        btn_sizer.Add(self.btn_cancel, 0, wx.ALL | wx.CENTER, 5)

        vbox.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 5)

        panel.SetSizer(vbox)
        self.Center()

        # ✅ تایمر را فقط در صورت Modal بودن فعال کن
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        # تایمر را بعد از ShowModal شروع می‌کنیم

        self.logger.info("✅ پنجره پیشرفت ساخته شد")

    def update(self, progress=None, message=None, status=None):
        """به‌روزرسانی پیشرفت (از ترد دیگر قابل صدا زدن است)"""
        with self._lock:
            if progress is not None:
                self.progress = min(100, max(0, int(progress)))
            if status is not None:
                self.status_message = status
            if message is not None:
                # به‌روزرسانی پیام اصلی
                wx.CallAfter(self.message_label.SetLabel, message)

    def _update_ui(self):
        """به‌روزرسانی UI (در تایمر)"""
        with self._lock:
            if self.progress != self.progress_bar.GetValue():
                self.progress_bar.SetValue(self.progress)

            if self.status_message:
                self.status_text.SetLabel(self.status_message)
                self.status_message = ""  # پاک کردن بعد از نمایش

    def on_timer(self, event):
        """تایمر برای به‌روزرسانی"""
        try:
            self._update_ui()

            # ✅ فقط در صورت Modal بودن و تمام شدن، ببند
            if self.is_finished and self._is_modal:
                self.timer.Stop()
                self.EndModal(wx.ID_OK)
        except Exception as e:
            # خطای EndModal را نادیده بگیر
            self.logger.debug(f"خطا در تایمر: {e}")

    def on_cancel(self, event):
        """لغو عملیات"""
        self.is_cancelled = True
        self.status_text.SetLabel("⚠️ در حال لغو...")
        self.logger.warning("⚠️ کاربر عملیات را لغو کرد")

    def finish(self):
        """پایان عملیات"""
        self.is_finished = True

    def close(self):
        """بستن دیالوگ"""
        try:
            if self._is_modal:
                wx.CallAfter(self.EndModal, wx.ID_OK)
            else:
                wx.CallAfter(self.Destroy)
        except Exception as e:
            self.logger.debug(f"خطا در بستن: {e}")
            wx.CallAfter(self.Destroy)

    def ShowModal(self):
        """نمایش به صورت Modal با شروع تایمر"""
        self._is_modal = True
        self.timer.Start(50)  # شروع تایمر
        self.logger.info("✅ دیالوگ Modal شد و تایمر شروع شد")
        return super().ShowModal()

    def run_with_progress(self, target_func, *args, **kwargs):
        """اجرای تابع در ترد جداگانه با نمایش پیشرفت"""
        self.is_finished = False
        self.is_cancelled = False

        def thread_func():
            try:
                result = target_func(*args, **kwargs)
                if not self.is_cancelled:
                    wx.CallAfter(self.finish)
                return result
            except Exception as e:
                self.logger.error(f"خطا در ترد: {e}")
                wx.CallAfter(self.status_text.SetLabel, f"❌ خطا: {str(e)}")
                wx.CallAfter(self.finish)
                raise

        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()

        # ✅ نمایش Modal با مدیریت خطا
        try:
            self.ShowModal()
        except Exception as e:
            self.logger.error(f"خطا در ShowModal: {e}")
            self.Destroy()
            raise

        # بررسی نتیجه
        if self.is_cancelled:
            raise Exception("عملیات توسط کاربر لغو شد")

        return thread