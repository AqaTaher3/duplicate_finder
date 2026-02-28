import wx
import datetime
import os
import random
import threading
from src.log_manager import log_manager

json_log_path = 'src/log_file_not_found.json'


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(1400, 800))  # ✅ افزایش سایز پنجره

        self.logger = log_manager.get_logger("FileFinderFrame")
        self.logger.info(f"ایجاد پنجره FileFinderFrame برای: {folder_path}")

        self.folder_path = folder_path
        self.file_handler = file_handler
        self.current_set = 0
        self.files_list = []
        self.selected_files = []
        self.is_processing = False

        # ✅ تغییر: پس‌زمینه روشن‌تر
        self.SetBackgroundColour(wx.Colour(240, 245, 250))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(245, 250, 255))

        # ✅ تغییر: فونت بزرگتر
        default_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.SetFont(default_font)

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # نوار وضعیت
        self.status_bar = self.CreateStatusBar(2)
        self.status_bar.SetStatusWidths([-3, -1])
        self.status_bar.SetStatusText("آماده", 0)

        # ✅ تغییر: رنگ متن نوار وضعیت
        self.status_bar.SetBackgroundColour(wx.Colour(220, 230, 240))
        self.status_bar.SetForegroundColour(wx.Colour(50, 50, 50))

        # نوار پیشرفت
        self.progress_bar = wx.Gauge(self.panel, range=100, size=(300, 25))  # ✅ بزرگتر
        self.progress_bar.Hide()
        self.vbox.Add(self.progress_bar, 0, wx.ALL | wx.CENTER, 5)

        self.status_label = wx.StaticText(self.panel, label="در حال بارگذاری فایل‌ها...")
        self.status_label.SetForegroundColour(wx.Colour(50, 50, 50))  # ✅ متن تیره‌تر
        self.status_label.SetFont(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # کنترل‌های استراتژی
        self.strategy_panel = wx.Panel(self.panel)
        self.strategy_panel.SetBackgroundColour(wx.Colour(220, 230, 240))  # ✅ روشن‌تر
        strategy_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cb_priority_old = wx.CheckBox(self.strategy_panel, label="حذف قدیمی‌ترها (نگهداری جدیدتر)")
        self.cb_priority_new = wx.CheckBox(self.strategy_panel, label="حذف جدیدترها (نگهداری قدیمی)")
        self.cb_random = wx.CheckBox(self.strategy_panel, label="حذف تصادفی (نگهداری یکی)")

        self.cb_priority_old.Bind(wx.EVT_CHECKBOX, self.on_old_checkbox)
        self.cb_priority_new.Bind(wx.EVT_CHECKBOX, self.on_new_checkbox)
        self.cb_random.Bind(wx.EVT_CHECKBOX, self.on_random_checkbox)

        # ✅ تغییر: فونت بزرگتر برای چک‌باکس‌ها
        checkbox_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.cb_priority_old.SetFont(checkbox_font)
        self.cb_priority_new.SetFont(checkbox_font)
        self.cb_random.SetFont(checkbox_font)

        strategy_sizer.Add(self.cb_priority_old, 0, wx.ALL | wx.CENTER, 5)
        strategy_sizer.Add(self.cb_priority_new, 0, wx.ALL | wx.CENTER, 5)
        strategy_sizer.Add(self.cb_random, 0, wx.ALL | wx.CENTER, 5)

        # تنظیمات حذف
        self.cb_use_recycle = wx.CheckBox(self.strategy_panel, label="استفاده از سطل بازیافت")
        self.cb_use_recycle.SetValue(True)
        self.cb_use_recycle.SetFont(checkbox_font)
        strategy_sizer.Add(self.cb_use_recycle, 0, wx.ALL | wx.CENTER, 5)

        self.strategy_panel.SetSizer(strategy_sizer)
        self.vbox.Add(self.strategy_panel, 0, wx.ALL | wx.EXPAND, 5)

        # ✅ تغییر: استفاده از ListCtrl با ستون‌های متعدد
        self.file_list = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
                                     size=(1300, 400))
        self.file_list.SetBackgroundColour(wx.Colour(255, 255, 255))  # ✅ سفید
        self.file_list.SetForegroundColour(wx.Colour(30, 30, 30))

        # ✅ تنظیم فونت بزرگتر برای لیست
        list_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.file_list.SetFont(list_font)

        # ✅ اضافه کردن ستون‌ها
        self.file_list.InsertColumn(0, "انتخاب", width=50)
        self.file_list.InsertColumn(1, "نام فایل", width=250)
        self.file_list.InsertColumn(2, "سایز", width=100)
        self.file_list.InsertColumn(3, "تاریخ ایجاد", width=140)
        self.file_list.InsertColumn(4, "تاریخ تغییر", width=140)
        self.file_list.InsertColumn(5, "آدرس", width=600)

        # ✅ رویداد برای کلیک
        self.file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_item_selected)
        self.file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_list_item_deselected)
        self.file_list.Bind(wx.EVT_LEFT_DOWN, self.on_list_click)  # برای مدیریت چک‌باکس

        self.vbox.Add(self.file_list, 1, wx.ALL | wx.EXPAND, 10)

        # دکمه‌های کنترل
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self.panel, label="⏪ گروه قبلی")
        self.btn_prev.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        self.btn_prev.SetFont(default_font)
        self.button_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(self.panel, label="گروه بعدی ⏩")
        self.btn_next.Bind(wx.EVT_BUTTON, self.next_set)
        self.btn_next.SetFont(default_font)
        self.button_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_check_all = wx.Button(self.panel, label="✅ انتخاب همه")
        self.btn_check_all.Bind(wx.EVT_BUTTON, self.on_check_all)
        self.btn_check_all.SetFont(default_font)
        self.button_sizer.Add(self.btn_check_all, 0, wx.ALL | wx.CENTER, 5)

        self.btn_uncheck_all = wx.Button(self.panel, label="❌ لغو همه")
        self.btn_uncheck_all.Bind(wx.EVT_BUTTON, self.on_uncheck_all)
        self.btn_uncheck_all.SetFont(default_font)
        self.button_sizer.Add(self.btn_uncheck_all, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete = wx.Button(self.panel, label="🗑️ حذف انتخاب‌ها")
        self.btn_delete.SetBackgroundColour(wx.Colour(220, 53, 69))
        self.btn_delete.SetForegroundColour(wx.WHITE)
        self.btn_delete.SetFont(default_font)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        self.button_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 5)

        self.btn_apply_all = wx.Button(self.panel, label="⚡ اعمال به همه گروه‌ها")
        self.btn_apply_all.SetBackgroundColour(wx.Colour(255, 140, 0))
        self.btn_apply_all.SetForegroundColour(wx.WHITE)
        self.btn_apply_all.SetFont(default_font)
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.on_apply_to_all)
        self.button_sizer.Add(self.btn_apply_all, 0, wx.ALL | wx.CENTER, 5)

        self.btn_switch_method = wx.Button(self.panel, label="🔄 تغییر روش")
        self.btn_switch_method.SetBackgroundColour(wx.Colour(70, 130, 180))
        self.btn_switch_method.SetForegroundColour(wx.WHITE)
        self.btn_switch_method.SetFont(default_font)
        self.btn_switch_method.Bind(wx.EVT_BUTTON, self.on_switch_method)
        self.button_sizer.Add(self.btn_switch_method, 0, wx.ALL | wx.CENTER, 5)

        self.btn_undo = wx.Button(self.panel, label="↩️ بازگردانی")
        self.btn_undo.SetFont(default_font)
        self.btn_undo.Bind(wx.EVT_BUTTON, self.on_undo)
        self.button_sizer.Add(self.btn_undo, 0, wx.ALL | wx.CENTER, 5)

        self.btn_debug = wx.Button(self.panel, label="🐛 دیباگ")
        self.btn_debug.SetFont(default_font)
        self.btn_debug.Bind(wx.EVT_BUTTON, self.on_debug)
        self.button_sizer.Add(self.btn_debug, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        # نمایش اطلاعات
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.selected_count_label = wx.StaticText(self.panel, label="انتخاب شده: 0 فایل")
        self.selected_count_label.SetForegroundColour(wx.Colour(50, 50, 50))
        self.selected_count_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        info_sizer.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 5)

        self.group_count_label = wx.StaticText(self.panel, label="گروه: 0/0")
        self.group_count_label.SetForegroundColour(wx.Colour(30, 100, 200))
        self.group_count_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        info_sizer.Add(self.group_count_label, 0, wx.ALL | wx.CENTER, 5)

        self.total_files_label = wx.StaticText(self.panel, label="کل فایل‌ها: 0")
        self.total_files_label.SetForegroundColour(wx.Colour(30, 150, 50))
        self.total_files_label.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        info_sizer.Add(self.total_files_label, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(info_sizer, 0, wx.ALL | wx.CENTER, 10)

        # راهنما
        help_text = wx.StaticText(self.panel,
                                  label="راهنما: کلیک روی سطر اول برای انتخاب/لغو انتخاب • F1 = راهنمای کامل")
        help_text.SetForegroundColour(wx.Colour(100, 100, 100))
        help_text.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        self.vbox.Add(help_text, 0, wx.ALL | wx.CENTER, 5)

        # رویدادهای کلید
        self.Bind(wx.EVT_KEY_DOWN, self.on_frame_key)

        # آیکون
        try:
            if os.path.exists("icon.ico"):
                self.SetIcon(wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO))
        except:
            pass

        self.panel.SetSizer(self.vbox)
        self.Center()
        self.Show()

        # بارگذاری اولیه در پس‌زمینه
        self.load_files_background()

    # ---------- متدهای جدید برای مدیریت ListCtrl ----------

    def on_list_item_selected(self, event):
        """وقتی یک آیتم انتخاب شد"""
        pass  # انتخاب از طریق چک‌باکس مدیریت می‌شود

    def on_list_item_deselected(self, event):
        """وقتی انتخاب یک آیتم لغو شد"""
        pass

    def on_list_click(self, event):
        """مدیریت کلیک روی لیست (برای چک‌باکس)"""
        x, y = event.GetPosition()
        item, flags = self.file_list.HitTest((x, y))

        if item >= 0:
            # بررسی آیا روی ستون اول (چک‌باکس) کلیک شده
            rect = self.file_list.GetItemRect(item)
            checkbox_width = 20  # عرض تقریبی ناحیه چک‌باکس

            if x - rect.x < checkbox_width:
                # تغییر وضعیت چک‌باکس
                self.toggle_checkbox(item)

        event.Skip()

    def toggle_checkbox(self, item_index):
        """تغییر وضعیت چک‌باکس یک ردیف"""
        if not self.files_list or self.current_set >= len(self.files_list):
            return

        file_group = self.files_list[self.current_set]

        if item_index < len(file_group):
            file_path = file_group[item_index]

            # بررسی وضعیت فعلی
            current_state = self.file_list.GetItem(item_index, 0).GetText()
            is_checked = current_state == "✓"

            if is_checked:
                # لغو انتخاب
                self.file_list.SetItem(item_index, 0, "")
                if file_path in self.selected_files:
                    self.selected_files.remove(file_path)
                    self.logger.info(f"❌ لغو انتخاب: {os.path.basename(file_path)}")
            else:
                # انتخاب
                self.file_list.SetItem(item_index, 0, "✓")
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self.logger.info(f"✅ انتخاب: {os.path.basename(file_path)}")

            self.update_selected_count()

    def on_check_all(self, event):
        """انتخاب همه فایل‌های گروه فعلی"""
        if not self.files_list or self.current_set >= len(self.files_list):
            return

        file_group = self.files_list[self.current_set]

        for i in range(len(file_group)):
            self.file_list.SetItem(i, 0, "✓")

        self.selected_files = list(file_group)
        self.update_selected_count()
        self.logger.info(f"✅ انتخاب همه: {len(self.selected_files)} فایل")

    def on_uncheck_all(self, event):
        """لغو انتخاب همه فایل‌های گروه فعلی"""
        for i in range(self.file_list.GetItemCount()):
            self.file_list.SetItem(i, 0, "")

        self.selected_files = []
        self.update_selected_count()
        self.logger.info("❌ لغو انتخاب همه")

    def clear_checkboxes(self):
        """پاک کردن جدول"""
        self.file_list.DeleteAllItems()

    # ---------- متدهای اصلی با تغییرات ----------

    def on_old_checkbox(self, event):
        if self.cb_priority_old.GetValue():
            self.cb_priority_new.SetValue(False)
            self.cb_random.SetValue(False)
        self.show_current_set()
        self.update_selected_count()

    def on_new_checkbox(self, event):
        if self.cb_priority_new.GetValue():
            self.cb_priority_old.SetValue(False)
            self.cb_random.SetValue(False)
        self.show_current_set()
        self.update_selected_count()

    def on_random_checkbox(self, event):
        if self.cb_random.GetValue():
            self.cb_priority_old.SetValue(False)
            self.cb_priority_new.SetValue(False)
        self.show_current_set()
        self.update_selected_count()

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
            self.clear_checkboxes()
            self.update_status_bar("هیچ فایل تکراری یافت نشد")

    def on_load_error(self, error_msg):
        """وقتی خطا در بارگذاری رخ داد"""
        self.progress_bar.Hide()
        self.status_label.SetLabel(f"خطا در بارگذاری: {error_msg}")
        self.update_status_bar(f"خطا: {error_msg}")

    def update_status_bar(self, message, field=0):
        """به‌روزرسانی نوار وضعیت"""
        self.status_bar.SetStatusText(message, field)

    def on_context_menu(self, event):
        """منوی راست کلیک"""
        menu = wx.Menu()
        # آیتم‌های منو...
        self.PopupMenu(menu)
        menu.Destroy()

    def on_frame_key(self, event):
        """مدیریت کلیدهای پنجره"""
        key_code = event.GetKeyCode()

        if key_code == wx.WXK_F1:
            help_text = """
            راهنمای کلیدها:
            • کلیک روی ستون اول (✓): انتخاب/لغو انتخاب فایل
            • Delete: حذف فایل انتخاب شده
            • ← →: رفتن به گروه قبلی/بعدی
            • Ctrl+A: انتخاب همه
            • Ctrl+Shift+A: لغو انتخاب همه
            • F1: نمایش این راهنما
            """
            wx.MessageBox(help_text, "راهنمای برنامه", wx.OK | wx.ICON_INFORMATION)

        elif key_code == wx.WXK_LEFT:
            self.back_to_previous_set(None)

        elif key_code == wx.WXK_RIGHT:
            self.next_set(None)

        elif event.ControlDown() and key_code == 65:  # Ctrl+A
            self.on_check_all(None)

        elif event.ControlDown() and event.ShiftDown() and key_code == 65:  # Ctrl+Shift+A
            self.on_uncheck_all(None)

        event.Skip()

    def on_delete_selected(self, event):
        """حذف فایل‌های انتخاب شده"""
        if not self.selected_files:
            wx.MessageBox("هیچ فایلی انتخاب نشده است!", "خطا", wx.OK | wx.ICON_WARNING)
            return

        # تأیید حذف
        confirm_msg = f"آیا از حذف {len(self.selected_files)} فایل انتخاب شده مطمئن هستید؟"
        dlg = wx.MessageDialog(self, confirm_msg, "تأیید حذف",
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)

        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        # حذف فایل‌ها
        deleted_count = 0
        for file_path in self.selected_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    self.logger.info(f"✅ حذف شد: {os.path.basename(file_path)}")
            except Exception as e:
                self.logger.error(f"❌ خطا در حذف {file_path}: {e}")

        # پاک کردن لیست انتخاب‌ها
        self.selected_files = []

        # بارگذاری مجدد
        self.load_files_background()

        # نمایش نتیجه
        wx.MessageBox(f"{deleted_count} فایل حذف شد", "نتیجه", wx.OK | wx.ICON_INFORMATION)

    def on_apply_to_all(self, event):
        """اعمال استراتژی انتخاب شده روی تمام گروه‌ها"""
        if not self.files_list:
            return

        if not (self.cb_priority_new.GetValue() or self.cb_priority_old.GetValue() or self.cb_random.GetValue()):
            wx.MessageBox("لطفاً ابتدا یکی از گزینه‌های حذف (قدیمی/جدید/تصادفی) را انتخاب کنید.", "خطا",
                          wx.ICON_WARNING)
            return

        # پاک کردن همه انتخاب‌های قبلی برای جلوگیری از تداخل
        self.selected_files = []

        # اعمال روی تک تک گروه‌ها
        for group in self.files_list:
            self.apply_strategy_logic(group)

        # به‌روزرسانی نمایش
        self.show_current_set()
        self.update_selected_count()

        diff = len(self.selected_files)
        wx.MessageBox(f"استراتژی روی تمام فایل‌ها اعمال شد.\nتعداد {diff} فایل برای حذف انتخاب شدند.", "موفقیت",
                      wx.ICON_INFORMATION)

    def on_switch_method(self, event):
        """تغییر روش بررسی"""
        wx.MessageBox("تغییر به روش نام مشابه", "توجه", wx.OK | wx.ICON_INFORMATION)

    def on_undo(self, event):
        """بازگردانی"""
        wx.MessageBox("قابلیت بازگردانی", "توجه", wx.OK | wx.ICON_INFORMATION)

    def on_debug(self, event):
        """رویداد دکمه دیباگ"""
        self.debug_selection()

    def back_to_previous_set(self, event):
        """گروه قبلی"""
        if self.current_set > 0:
            self.current_set -= 1
            self.show_current_set()

    def next_set(self, event):
        """گروه بعدی"""
        if self.current_set < len(self.files_list) - 1:
            self.current_set += 1
            self.show_current_set()

    def debug_selection(self):
        """نمایش اطلاعات دیباگ برای انتخاب‌ها"""
        print("\n=== DEBUG SELECTION ===")
        print(f"Current set: {self.current_set}")
        print(f"Total files in current set: {len(self.files_list[self.current_set]) if self.files_list else 0}")
        print(f"Selected files: {len(self.selected_files)}")

        for i, file in enumerate(self.selected_files):
            print(f"  {i + 1}. {os.path.basename(file)}")

    def format_file_size(self, size_in_bytes):
        """فرمت کردن سایز فایل"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} PB"

    def show_current_set(self):
        """نمایش گروه فعلی با اطلاعات کامل"""
        self.file_list.DeleteAllItems()  # پاک کردن موارد قبلی

        if not self.files_list or self.current_set >= len(self.files_list):
            self.status_label.SetLabel("کار تمام شد!")
            return

        file_group = self.files_list[self.current_set]

        # اعمال استراتژی اگر انتخاب شده
        if self.cb_priority_new.GetValue() or self.cb_priority_old.GetValue() or self.cb_random.GetValue():
            self.apply_strategy_logic(file_group)

        # اضافه کردن فایل‌ها به لیست با اطلاعات کامل
        for i, file_path in enumerate(file_group):
            filename = os.path.basename(file_path)

            try:
                # اطلاعات سایز
                size = os.path.getsize(file_path)
                size_str = self.format_file_size(size)

                # اطلاعات تاریخ ایجاد (ctime)
                ctime = os.path.getctime(file_path)
                cdate_str = datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M')

                # اطلاعات تاریخ تغییر (mtime)
                mtime = os.path.getmtime(file_path)
                mdate_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

                # مسیر کامل
                full_path = file_path

            except Exception as e:
                size_str = "نامشخص"
                cdate_str = "نامشخص"
                mdate_str = "نامشخص"
                full_path = file_path

            # اضافه کردن ردیف به لیست
            index = self.file_list.InsertItem(i, "")  # ستون اول (چک‌باکس) خالی

            # پر کردن سایر ستون‌ها
            self.file_list.SetItem(index, 1, filename)
            self.file_list.SetItem(index, 2, size_str)
            self.file_list.SetItem(index, 3, cdate_str)
            self.file_list.SetItem(index, 4, mdate_str)
            self.file_list.SetItem(index, 5, full_path)

            # اگر فایل انتخاب شده بود، علامت ✓ بزن
            if file_path in self.selected_files:
                self.file_list.SetItem(index, 0, "✓")

        # آپدیت وضعیت
        remaining = len(self.files_list) - self.current_set - 1
        self.status_label.SetLabel(
            f"گروه {self.current_set + 1} از {len(self.files_list)} ({remaining} گروه باقی‌مانده)")

        self.group_count_label.SetLabel(f"گروه: {self.current_set + 1}/{len(self.files_list)}")
        self.total_files_label.SetLabel(f"کل فایل‌ها در این گروه: {len(file_group)}")
        self.update_selected_count()

    def update_selected_count(self):
        """به‌روزرسانی تعداد انتخاب‌ها"""
        self.selected_count_label.SetLabel(f"انتخاب شده: {len(self.selected_files)} فایل")

    def apply_strategy_logic(self, file_group):
        """اعمال استراتژی انتخاب روی یک گروه فایل"""
        if not file_group:
            return

        # ابتدا تمام فایل‌های این گروه را از لیست انتخاب شده‌ها خارج می‌کنیم (ریست کردن گروه)
        for f in file_group:
            if f in self.selected_files:
                self.selected_files.remove(f)

        files_to_select = []

        # اگر هیچ استراتژی انتخاب نشده باشد، کاری نکن
        if not (self.cb_priority_new.GetValue() or self.cb_priority_old.GetValue() or self.cb_random.GetValue()):
            return

        # دریافت زمان فایل‌ها
        files_with_time = []
        for f in file_group:
            try:
                mtime = os.path.getmtime(f)
            except:
                mtime = 0
            files_with_time.append((f, mtime))

        if self.cb_priority_new.GetValue():
            # حذف جدیدترها -> یعنی قدیمی‌ترین را نگه دار
            files_with_time.sort(key=lambda x: x[1])
            files_to_select = [x[0] for x in files_with_time[1:]]

        elif self.cb_priority_old.GetValue():
            # حذف قدیمی‌ترها -> یعنی جدیدترین را نگه دار
            files_with_time.sort(key=lambda x: x[1], reverse=True)
            files_to_select = [x[0] for x in files_with_time[1:]]

        elif self.cb_random.GetValue():
            # حذف تصادفی -> یکی را نگه دار
            if len(file_group) > 1:
                keep_index = random.randint(0, len(file_group) - 1)
                for i, f in enumerate(file_group):
                    if i != keep_index:
                        files_to_select.append(f)

        # اضافه کردن به لیست اصلی انتخاب شده‌ها
        self.selected_files.extend(files_to_select)