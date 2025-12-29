import wx
import datetime
import os
import random
import threading
from src2.writing_on_json import prepend_text_to_json
from src.log_manager import log_manager

json_log_path = 'src/log_file_not_foung.json'


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(1100, 600))

        self.logger = log_manager.get_logger("FileFinderFrame")
        self.logger.info(f"ایجاد پنجره FileFinderFrame برای: {folder_path}")

        self.folder_path = folder_path
        self.file_handler = file_handler
        self.current_set = 0
        self.files_list = []
        self.selected_files = []
        self.is_processing = False

        # بارگذاری اولیه در پس‌زمینه
        self.load_files_background()

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(43, 69, 60))
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # نوار وضعیت
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-3, -1])
        self.status_bar.SetStatusText("آماده", 0)

        # نوار پیشرفت
        self.progress_bar = wx.Gauge(self.panel, range=100, size=(300, 20))
        self.progress_bar.Hide()
        self.vbox.Add(self.progress_bar, 0, wx.ALL | wx.CENTER, 5)

        self.status_label = wx.StaticText(self.panel, label="در حال بارگذاری فایل‌ها...")
        self.status_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # کنترل‌های استراتژی
        self.strategy_panel = wx.Panel(self.panel)
        self.strategy_panel.SetBackgroundColour(wx.Colour(50, 50, 50))
        strategy_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cb_priority_old = wx.CheckBox(self.strategy_panel, label="حذف قدیمی‌ترها (نگهداری جدیدتر)")
        self.cb_priority_new = wx.CheckBox(self.strategy_panel, label="حذف جدیدترها (نگهداری قدیمی)")
        self.cb_random = wx.CheckBox(self.strategy_panel, label="حذف تصادفی (نگهداری یکی)")

        self.cb_priority_old.Bind(wx.EVT_CHECKBOX, self.on_old_checkbox)
        self.cb_priority_new.Bind(wx.EVT_CHECKBOX, self.on_new_checkbox)
        self.cb_random.Bind(wx.EVT_CHECKBOX, self.on_random_checkbox)

        strategy_sizer.Add(self.cb_priority_old, 0, wx.ALL | wx.CENTER, 5)
        strategy_sizer.Add(self.cb_priority_new, 0, wx.ALL | wx.CENTER, 5)
        strategy_sizer.Add(self.cb_random, 0, wx.ALL | wx.CENTER, 5)

        # تنظیمات حذف
        self.cb_use_recycle = wx.CheckBox(self.strategy_panel, label="استفاده از سطل بازیافت")
        self.cb_use_recycle.SetValue(True)
        strategy_sizer.Add(self.cb_use_recycle, 0, wx.ALL | wx.CENTER, 5)

        self.strategy_panel.SetSizer(strategy_sizer)
        self.vbox.Add(self.strategy_panel, 0, wx.ALL | wx.EXPAND, 5)

        # جعبه متن اصلی
        self.file_paths_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                                           size=(800, 300))
        self.file_paths_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.file_paths_ctrl.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.file_paths_ctrl.SetBackgroundColour(wx.Colour(30, 40, 50))
        self.file_paths_ctrl.SetForegroundColour(wx.Colour(230, 210, 181))

        font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.file_paths_ctrl.SetFont(font)

        self.vbox.Add(self.file_paths_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        # دکمه‌ها
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self.panel, label="⏪ گروه قبلی")
        self.btn_prev.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        self.button_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(self.panel, label="گروه بعدی ⏩")
        self.btn_next.Bind(wx.EVT_BUTTON, self.next_set)
        self.button_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete = wx.Button(self.panel, label="🗑️ حذف انتخاب‌ها")
        self.btn_delete.SetBackgroundColour(wx.Colour(220, 53, 69))
        self.btn_delete.SetForegroundColour(wx.WHITE)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        self.button_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 5)

        self.btn_apply_all = wx.Button(self.panel, label="⚡ اعمال به همه گروه‌ها")
        self.btn_apply_all.SetBackgroundColour(wx.Colour(255, 140, 0))
        self.btn_apply_all.SetForegroundColour(wx.WHITE)
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.on_apply_to_all)
        self.button_sizer.Add(self.btn_apply_all, 0, wx.ALL | wx.CENTER, 5)

        self.btn_switch_method = wx.Button(self.panel, label="🔄 تغییر روش")
        self.btn_switch_method.SetBackgroundColour(wx.Colour(70, 130, 180))
        self.btn_switch_method.SetForegroundColour(wx.WHITE)
        self.btn_switch_method.Bind(wx.EVT_BUTTON, self.on_switch_method)
        self.button_sizer.Add(self.btn_switch_method, 0, wx.ALL | wx.CENTER, 5)

        self.btn_undo = wx.Button(self.panel, label="↩️ بازگردانی")
        self.btn_undo.Bind(wx.EVT_BUTTON, self.on_undo)
        self.button_sizer.Add(self.btn_undo, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        # نمایش اطلاعات
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.selected_count_label = wx.StaticText(self.panel, label="انتخاب شده: 0 فایل")
        self.selected_count_label.SetForegroundColour(wx.Colour(230, 210, 181))
        info_sizer.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 5)

        self.group_count_label = wx.StaticText(self.panel, label="گروه: 0/0")
        self.group_count_label.SetForegroundColour(wx.Colour(180, 180, 255))
        info_sizer.Add(self.group_count_label, 0, wx.ALL | wx.CENTER, 5)

        self.total_files_label = wx.StaticText(self.panel, label="کل فایل‌ها: 0")
        self.total_files_label.SetForegroundColour(wx.Colour(180, 255, 180))
        info_sizer.Add(self.total_files_label, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(info_sizer, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        # راهنما
        help_text = wx.StaticText(self.panel,
                                  label="راهنما: Space = انتخاب • Alt = لغو انتخاب • Delete = حذف مستقیم • F1 = راهنمای کامل")
        help_text.SetForegroundColour(wx.Colour(150, 150, 150))
        self.vbox.Add(help_text, 0, wx.ALL | wx.CENTER, 5)

        # رویدادهای کلید
        self.Bind(wx.EVT_KEY_DOWN, self.on_frame_key)

        # آیکون
        try:
            if os.path.exists("icon.ico"):
                self.SetIcon(wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO))
        except:
            pass

        self.Center()
        self.Show()

    def load_files_background(self):
        """بارگذاری فایل‌ها در پس‌زمینه"""

        def load_thread():
            try:
                self.files_list = self.file_handler.load_files() or []
                wx.CallAfter(self.on_files_loaded)
            except Exception as e:
                wx.CallAfter(self.on_load_error, str(e))

        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def on_files_loaded(self):
        """وقتی فایل‌ها بارگذاری شدند"""
        self.progress_bar.Hide()
        self.status_label.SetLabel(f"تعداد گروه‌های تکراری: {len(self.files_list)}")

        if self.files_list:
            self.show_current_set()
            self.update_status_bar(f"آماده - {len(self.files_list)} گروه یافت شد")
        else:
            self.file_paths_ctrl.SetValue("✅ هیچ فایل تکراری یافت نشد!")
            self.update_status_bar("هیچ فایل تکراری یافت نشد")

    def on_load_error(self, error_msg):
        """وقتی خطا در بارگذاری رخ داد"""
        self.progress_bar.Hide()
        self.status_label.SetLabel(f"خطا در بارگذاری: {error_msg}")
        self.file_paths_ctrl.SetValue(f"خطا در بارگذاری فایل‌ها:\n{error_msg}")
        self.update_status_bar(f"خطا: {error_msg}")

    def update_status_bar(self, message, field=0):
        """به‌روزرسانی نوار وضعیت"""
        self.status_bar.SetStatusText(message, field)

    # بقیه متدها...