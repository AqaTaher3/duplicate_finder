import wx
from logic import FileHandler
import os
import datetime


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(1000, 450))  # ارتفاع کاهش یافته

        self.folder_path = folder_path
        self.file_handler = file_handler
        self.current_set = 0  # برای پیگیری گروه فعلی
        self.files_list = []  # مقداردهی اولیه لیست گروه‌های تکراری
        self.selected_files = []  # لیست فایل‌های انتخاب‌شده

        # دریافت گروه‌های فایل‌های تکراری
        self.files_list = self.file_handler.load_files() or []

        # ایجاد GUI با تم تیره
        self.SetBackgroundColour(wx.Colour(43, 58, 68))  # آبی تیره (Dark Blue)
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(43, 69, 60))  # سبز تیره (Dark Green)
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # برچسب وضعیت
        self.status_label = wx.StaticText(self.panel, label="Files remai ning:")
        self.status_label.SetForegroundColour(wx.Colour(230, 210, 181))  # متن کرم باقی مانده
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # لیست فایل‌ها
        self.file_paths_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(700, 200))
        self.file_paths_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_press)  # استفاده از on_key_press
        self.file_paths_ctrl.SetBackgroundColour(wx.Colour(43, 58, 68))  # آبی تیره (Dark Blue)
        self.file_paths_ctrl.SetForegroundColour(wx.Colour(230, 210, 181))  # متن سفید

        # تنظیم فونت بزرگ‌تر
        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.file_paths_ctrl.SetFont(font)

        self.vbox.Add(self.file_paths_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        # دکمه‌ها در یک ردیف
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self.panel, label="Back")
        self.btn_prev.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        self.button_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(self.panel, label="Next")
        self.btn_next.Bind(wx.EVT_BUTTON, self.next_set)
        self.button_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete = wx.Button(self.panel, label="Delete Selected")
        self.btn_delete.Bind(wx.EVT_BUTTON, self.delete_selected_files)
        self.button_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        # نوار وضعیت پایین پنجره
        self.selected_count_label = wx.StaticText(self.panel, label="Selected files: 0")
        self.selected_count_label.SetForegroundColour(wx.Colour(230, 210, 181))  # متن سفید
        self.vbox.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        # نمایش گروه اول فایل‌های تکراری
        self.show_current_set()

    def update_selected_count(self):
        """به‌روزرسانی تعداد فایل‌های انتخاب‌شده"""
        self.selected_count_label.SetLabel(f"Selected files: {len(self.selected_files)}")

    import os
    import datetime

    import os
    import datetime

    def show_current_set(self):
        """نمایش گروه فعلی فایل‌ها با مسیر نسبی و نمایش Data Modified یا در صورت نبود، Data Created"""
        self.file_paths_ctrl.Clear()
        if self.files_list and 0 <= self.current_set < len(self.files_list):
            file_group = self.files_list[self.current_set]

            file_info_list = []  # لیست فایل‌ها همراه با تاریخ‌ها

            for file in file_group:
                # تبدیل مسیر به مسیر نسبی
                relative_path = os.path.relpath(file, self.folder_path)

                try:
                    # دریافت زمان آخرین تغییر (modified time)
                    modified_time = os.path.getmtime(file)
                    modified_date = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    modified_date = None  # در صورت خطا، مقدار None بماند

                try:
                    # دریافت زمان ایجاد (created time)
                    created_time = os.path.getctime(file)
                    created_date = datetime.datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    created_date = None  # در صورت خطا، مقدار None بماند

                # اگر Modified وجود نداشت، Created را جایگزین کن
                file_date = modified_date if modified_date else created_date if created_date else "N/A"

                # اضافه کردن به لیست نمایش
                file_info_list.append(f"{relative_path}   |   {file_date}")

            # نمایش مسیر و تاریخ در GUI
            file_paths = "\n".join(file_info_list)
            self.file_paths_ctrl.SetValue(file_paths)
            self.status_label.SetLabel(f"Files remaining: {len(self.files_list) - self.current_set}")
        else:
            self.file_paths_ctrl.SetValue("No more duplicate files found.")

        # به‌روزرسانی تعداد فایل‌های انتخاب‌شده
        self.update_selected_count()

    def next_set(self, event):
        """نمایش گروه بعدی فایل‌ها"""
        if self.current_set < len(self.files_list) - 1:
            self.current_set += 1
            self.show_current_set()

    def back_to_previous_set(self, event):
        """نمایش گروه قبلی فایل‌ها"""
        if self.current_set > 0:
            self.current_set -= 1
            self.show_current_set()

    def delete_selected_files(self, event):
        """حذف فایل‌های انتخاب‌شده"""
        if not self.selected_files:
            return

        for file_path in self.selected_files:
            try:
                # تبدیل مسیر نسبی به مسیر مطلق
                absolute_path = os.path.join(self.folder_path, file_path)

                if os.path.exists(absolute_path):
                    os.remove(absolute_path)
                    print(f"Deleted: {absolute_path}")
                else:
                    print(f"⚠️ File not found: {absolute_path}")

            except Exception as e:
                print(f"خطا در حذف فایل {absolute_path}: {e}")

        # پاک کردن لیست فایل‌های انتخاب‌شده پس از حذف
        self.selected_files = []
        self.files_list = self.file_handler.load_files()
        self.show_current_set()

        # پاک کردن لیست فایل‌های انتخاب‌شده پس از حذف
        self.selected_files = []
        self.files_list = self.file_handler.load_files()
        self.show_current_set()

    def on_key_press(self, event):
        """مدیریت رویدادهای کیبورد"""
        key_code = event.GetKeyCode()
        cursor_pos = self.file_paths_ctrl.GetInsertionPoint()  # موقعیت کرسر
        line_start = self.file_paths_ctrl.GetRange(0, cursor_pos).rfind("\n") + 1  # ابتدای خط
        line_end = self.file_paths_ctrl.GetValue().find("\n", cursor_pos)  # انتهای خط
        if line_end == -1:
            line_end = len(self.file_paths_ctrl.GetValue())  # اگر خط آخر باشد

        selected_text = self.file_paths_ctrl.GetRange(line_start, line_end)  # متن خط انتخاب‌شده

        if selected_text:  # اگر کاربر چیزی انتخاب کرده باشد
            if key_code == wx.WXK_SPACE:  # دکمه Space برای انتخاب
                if selected_text not in self.selected_files:
                    self.selected_files.append(selected_text)
                    self.update_selected_count()
            elif key_code == wx.WXK_ALT:  # دکمه Alt برای دیسلکت
                if selected_text in self.selected_files:
                    self.selected_files.remove(selected_text)
                    self.update_selected_count()

        event.Skip()  # ادامه پردازش رویدادهای دیگر