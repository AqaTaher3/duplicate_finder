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

    def on_old_checkbox(self, event):
        if self.cb_priority_old.GetValue():
            self.cb_priority_new.SetValue(False)
            self.cb_random.SetValue(False)
        # رفرش کردن صفحه برای اعمال تغییرات
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

    # بعد از متدهای قبلی که اضافه کردید، این متدها را هم اضافه کنید:

    def on_key_press(self, event):
        """مدیریت کلیدهای صفحه‌کلید"""
        key_code = event.GetKeyCode()

        # موقعیت کرسر
        cursor_pos = self.file_paths_ctrl.GetInsertionPoint()
        text = self.file_paths_ctrl.GetValue()

        # پیدا کردن خط فعلی
        line_start = text.rfind("\n", 0, cursor_pos) + 1
        line_end = text.find("\n", cursor_pos)
        if line_end == -1:
            line_end = len(text)

        selected_line = text[line_start:line_end].strip()

        if selected_line:
            # استخراج مسیر فایل
            line_content = selected_line.replace("✓ ", "").strip()
            parts = line_content.split("   |   ")
            if parts:
                relative_path = parts[0].strip()
                absolute_path = os.path.join(self.folder_path, relative_path)

                # بررسی وجود فایل
                if os.path.exists(absolute_path):
                    if key_code == wx.WXK_SPACE:
                        # انتخاب با Space
                        if absolute_path not in self.selected_files:
                            self.selected_files.append(absolute_path)
                            print(f"File selected: {absolute_path}")
                        else:
                            self.selected_files.remove(absolute_path)
                            print(f"File deselected: {absolute_path}")

                        self.show_current_set()
                        self.update_selected_count()

                    elif key_code == wx.WXK_DELETE:
                        # حذف مستقیم با Delete
                        reply = wx.MessageBox(
                            f"آیا می‌خواهید فایل را حذف کنید؟\n{os.path.basename(absolute_path)}",
                            "تأیید حذف",
                            wx.YES_NO | wx.ICON_WARNING
                        )
                        if reply == wx.YES:
                            try:
                                os.remove(absolute_path)
                                print(f"✅ حذف شد: {os.path.basename(absolute_path)}")
                                # بارگذاری مجدد لیست
                                self.load_files_background()
                            except Exception as e:
                                print(f"❌ خطا در حذف: {e}")

        event.Skip()

    def on_context_menu(self, event):
        """منوی راست کلیک"""
        menu = wx.Menu()

        # آیتم‌های منو
        select_item = menu.Append(wx.ID_ANY, "انتخاب فایل")
        deselect_item = menu.Append(wx.ID_ANY, "لغو انتخاب")
        menu.AppendSeparator()
        delete_item = menu.Append(wx.ID_ANY, "🗑️ حذف فایل")
        menu.AppendSeparator()
        open_item = menu.Append(wx.ID_ANY, "📂 باز کردن پوشه")
        properties_item = menu.Append(wx.ID_ANY, "📋 اطلاعات فایل")

        # نمایش منو
        self.PopupMenu(menu)
        menu.Destroy()

    def on_frame_key(self, event):
        """مدیریت کلیدهای پنجره"""
        key_code = event.GetKeyCode()

        if key_code == wx.WXK_F1:
            # نمایش راهنما
            help_text = """
            راهنمای کلیدها:
            • Space: انتخاب/لغو انتخاب فایل
            • Delete: حذف فایل انتخاب شده
            • ← →: رفتن به گروه قبلی/بعدی
            • F1: نمایش این راهنما
            """
            wx.MessageBox(help_text, "راهنمای برنامه", wx.OK | wx.ICON_INFORMATION)

        elif key_code == wx.WXK_LEFT:
            self.back_to_previous_set(None)

        elif key_code == wx.WXK_RIGHT:
            self.next_set(None)

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
                    print(f"✅ حذف شد: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"❌ خطا در حذف {file_path}: {e}")

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

        count_before = len(self.selected_files)

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

    def show_current_set(self):
        """نمایش گروه فعلی"""
        self.file_paths_ctrl.Clear()
        if self.files_list and 0 <= self.current_set < len(self.files_list):
            file_group = self.files_list[self.current_set]
            self.apply_strategy_logic(file_group)

            file_info_list = []

            for file in file_group:
                relative_path = os.path.relpath(file, self.folder_path)

                try:
                    modified_time = os.path.getmtime(file)
                    modified_date = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    modified_date = "نامشخص"

                # علامت اگر انتخاب شده
                prefix = "✓ " if file in self.selected_files else "  "
                file_info_list.append(f"{prefix}{relative_path}   |   {modified_date}")

            file_paths = "\n".join(file_info_list)
            self.file_paths_ctrl.SetValue(file_paths)

            # آپدیت وضعیت
            remaining = len(self.files_list) - self.current_set - 1
            self.status_label.SetLabel(
                f"گروه {self.current_set + 1} از {len(self.files_list)} ({remaining} گروه باقی‌مانده)")
        else:
            self.file_paths_ctrl.SetValue("هیچ گروهی برای نمایش وجود ندارد.")
            self.status_label.SetLabel("کار تمام شد!")

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
            # حذف جدیدترها -> یعنی قدیمی‌ترین را نگه دار (مرتب‌سازی صعودی زمان)
            # اولین آیتم (index 0) قدیمی‌ترین است، پس آن را حذف نمی‌کنیم. بقیه را انتخاب می‌کنیم.
            files_with_time.sort(key=lambda x: x[1])
            files_to_select = [x[0] for x in files_with_time[1:]]

        elif self.cb_priority_old.GetValue():
            # حذف قدیمی‌ترها -> یعنی جدیدترین را نگه دار (مرتب‌سازی نزولی زمان)
            # اولین آیتم جدیدترین است، آن را نگه می‌داریم.
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
