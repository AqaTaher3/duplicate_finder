import wx
import datetime
import os
import random
from src2.writing_on_json import prepend_text_to_json

json_log_path = 'src/log_file_not_foung.json'


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(1000, 520))

        self.folder_path = folder_path
        self.file_handler = file_handler
        self.current_set = 0
        self.files_list = []
        self.selected_files = []

        self.files_list = self.file_handler.load_files() or []

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(43, 69, 60))
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(self.panel, label="Files remaining:")
        self.status_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # چک‌باکس‌ها برای انتخاب استراتژی حذف
        self.checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.cb_priority_old = wx.CheckBox(self.panel, label="Delete older files (keep newer) - ALL FILES")
        self.cb_priority_new = wx.CheckBox(self.panel, label="Delete newer files (keep older) - ALL FILES")
        self.cb_random = wx.CheckBox(self.panel, label="Delete random (keep one random) - ALL FILES")

        # اطمینان از انتخاب فقط یکی از چک‌باکس‌ها
        self.cb_priority_old.Bind(wx.EVT_CHECKBOX, self.on_old_checkbox)
        self.cb_priority_new.Bind(wx.EVT_CHECKBOX, self.on_new_checkbox)
        self.cb_random.Bind(wx.EVT_CHECKBOX, self.on_random_checkbox)

        self.checkbox_sizer.Add(self.cb_priority_old, 0, wx.ALL | wx.CENTER, 5)
        self.checkbox_sizer.Add(self.cb_priority_new, 0, wx.ALL | wx.CENTER, 5)
        self.checkbox_sizer.Add(self.cb_random, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.checkbox_sizer, 0, wx.ALL | wx.CENTER, 10)

        self.file_paths_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(700, 200))
        self.file_paths_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.file_paths_ctrl.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.file_paths_ctrl.SetForegroundColour(wx.Colour(230, 210, 181))

        font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.file_paths_ctrl.SetFont(font)

        self.vbox.Add(self.file_paths_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self.panel, label="Back")
        self.btn_prev.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        self.button_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(self.panel, label="Next")
        self.btn_next.Bind(wx.EVT_BUTTON, self.next_set)
        self.button_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete = wx.Button(self.panel, label="Delete Selected")
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        self.button_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 5)

        # دکمه جدید برای اعمال روی تمام فایل‌ها
        self.btn_apply_all = wx.Button(self.panel, label="Apply to ALL Duplicate Groups")
        self.btn_apply_all.Bind(wx.EVT_BUTTON, self.on_apply_to_all)
        self.button_sizer.Add(self.btn_apply_all, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        self.selected_count_label = wx.StaticText(self.panel, label="Selected files: 0")
        self.selected_count_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        self.show_current_set()

    def on_old_checkbox(self, event):
        """وقتی چک‌باکس حذف فایل‌های قدیمی زده شد"""
        if self.cb_priority_old.GetValue():
            self.cb_priority_new.SetValue(False)
            self.cb_random.SetValue(False)

    def on_new_checkbox(self, event):
        """وقتی چک‌باکس حذف فایل‌های جدید زده شد"""
        if self.cb_priority_new.GetValue():
            self.cb_priority_old.SetValue(False)
            self.cb_random.SetValue(False)

    def on_random_checkbox(self, event):
        """وقتی چک‌باکس حذف رندوم زده شد"""
        if self.cb_random.GetValue():
            self.cb_priority_old.SetValue(False)
            self.cb_priority_new.SetValue(False)

    def on_apply_to_all(self, event):
        """اعمال استراتژی انتخاب شده روی تمام گروه‌های تکراری"""
        if not any([self.cb_priority_old.GetValue(), self.cb_priority_new.GetValue(), self.cb_random.GetValue()]):
            wx.MessageBox("لطفاً یکی از گزینه‌های حذف را انتخاب کنید!", "خطا", wx.OK | wx.ICON_WARNING)
            return

        if not self.files_list:
            wx.MessageBox("هیچ فایل تکراری یافت نشد!", "اطلاع", wx.OK | wx.ICON_INFORMATION)
            return

        # تأیید کاربر
        confirm_msg = "آیا مطمئن هستید که می‌خواهید این عمل روی تمام گروه‌های تکراری اعمال شود؟\nاین عمل غیرقابل بازگشت است!"
        dlg = wx.MessageDialog(self, confirm_msg, "تأیید عملیات", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)

        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        total_deleted = 0
        total_groups = len(self.files_list)

        # ایجاد دیالوگ پیشرفت
        progress_dlg = wx.ProgressDialog(
            "در حال پردازش تمام فایل‌ها",
            "در حال اعمال استراتژی حذف روی تمام گروه‌های تکراری...",
            maximum=total_groups,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        )

        try:
            for i, file_group in enumerate(self.files_list):
                if len(file_group) <= 1:
                    continue

                # به‌روزرسانی پیشرفت
                progress_dlg.Update(i, f"پردازش گروه {i + 1} از {total_groups}")

                files_to_delete = []

                if self.cb_priority_old.GetValue():
                    # حذف فایل‌های قدیمی
                    files_with_time = self.get_files_sorted_by_time(file_group, newest_first=True)
                    if len(files_with_time) > 1:
                        files_to_keep = [files_with_time[0][0]]  # جدیدترین فایل
                        files_to_delete = [f[0] for f in files_with_time[1:]]  # بقیه فایل‌ها

                elif self.cb_priority_new.GetValue():
                    # حذف فایل‌های جدید
                    files_with_time = self.get_files_sorted_by_time(file_group, newest_first=False)
                    if len(files_with_time) > 1:
                        files_to_keep = [files_with_time[0][0]]  # قدیمی‌ترین فایل
                        files_to_delete = [f[0] for f in files_with_time[1:]]  # بقیه فایل‌ها

                elif self.cb_random.GetValue():
                    # حذف رندوم
                    files_with_time = self.get_files_sorted_by_time(file_group, newest_first=True)
                    if len(files_with_time) > 1:
                        random.shuffle(files_with_time)  # مخلوط کردن لیست
                        files_to_keep = [files_with_time[0][0]]  # یک فایل رندوم برای نگهداری
                        files_to_delete = [f[0] for f in files_with_time[1:]]  # بقیه فایل‌ها

                # حذف فایل‌ها
                if files_to_delete:
                    deleted_in_group = self.file_handler.delete_files_silent(files_to_delete)
                    total_deleted += deleted_in_group

            progress_dlg.Update(total_groups)

            # نمایش فایل‌های حذف نشده
            failed_deletions = self.file_handler.get_failed_deletions()
            if failed_deletions:
                failed_count = len(failed_deletions)
                failed_list = "\n".join([os.path.basename(f) for f in failed_deletions[:5]])  # 5 تای اول
                failed_msg = f"\n\n⚠️ {failed_count} فایل حذف نشدند (مشکل دسترسی)\nنمونه:\n{failed_list}"
                if failed_count > 5:
                    failed_msg += f"\n... و {failed_count - 5} فایل دیگر"
            else:
                failed_msg = ""

            # بارگذاری مجدد لیست فایل‌ها
            self.files_list = self.file_handler.load_files()
            self.current_set = 0
            self.show_current_set()

            # نمایش نتیجه نهایی
            remaining_groups = len(self.files_list)
            wx.MessageBox(
                f"✅ عملیات کامل شد!\n\n"
                f"🗑️ تعداد کل فایل‌های حذف شده: {total_deleted}\n"
                f"📊 تعداد گروه‌های تکراری باقیمانده: {remaining_groups}"
                f"{failed_msg}",
                "عملیات کامل",
                wx.OK | wx.ICON_INFORMATION
            )

            # پاک کردن لیست خطاها برای اجرای بعدی
            self.file_handler.clear_failed_deletions()

        except Exception as e:
            wx.MessageBox(f"خطا در پردازش: {str(e)}", "خطا", wx.OK | wx.ICON_ERROR)
        finally:
            progress_dlg.Destroy()

    def get_files_sorted_by_time(self, file_group, newest_first=True):
        """مرتب‌سازی فایل‌ها بر اساس تاریخ"""
        files_with_time = []
        for file_path in file_group:
            try:
                if os.path.exists(file_path):
                    mtime = os.path.getmtime(file_path)
                    ctime = os.path.getctime(file_path)
                    # استفاده از قدیمی‌ترین تاریخ بین modification و creation
                    file_time = min(mtime, ctime)
                    files_with_time.append((file_path, file_time))
            except Exception as e:
                print(f"Error getting time for {file_path}: {e}")
                continue

        # مرتب‌سازی بر اساس تاریخ
        files_with_time.sort(key=lambda x: x[1], reverse=newest_first)
        return files_with_time

    def update_selected_count(self):
        self.selected_count_label.SetLabel(f"Selected files: {len(self.selected_files)}")

    def show_current_set(self):
        self.file_paths_ctrl.Clear()
        if self.files_list and 0 <= self.current_set < len(self.files_list):
            file_group = self.files_list[self.current_set]

            file_info_list = []

            for file in file_group:
                relative_path = os.path.relpath(file, self.folder_path)

                try:
                    modified_time = os.path.getmtime(file)
                    modified_date = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    modified_date = None

                try:
                    created_time = os.path.getctime(file)
                    created_date = datetime.datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    created_date = None

                file_date = modified_date if modified_date else created_date if created_date else "N/A"

                file_info_list.append(f"{relative_path}   |   {file_date}")

            file_paths = "\n".join(file_info_list)
            self.file_paths_ctrl.SetValue(file_paths)
            self.status_label.SetLabel(f"Files remaining: {len(self.files_list) - self.current_set}")
        else:
            self.file_paths_ctrl.SetValue("No more duplicate files found.")

        self.update_selected_count()

    def next_set(self, event):
        if self.current_set < len(self.files_list) - 1:
            self.current_set += 1
            self.show_current_set()

    def back_to_previous_set(self, event):
        if self.current_set > 0:
            self.current_set -= 1
            self.show_current_set()

    def on_key_press(self, event):
        key_code = event.GetKeyCode()
        cursor_pos = self.file_paths_ctrl.GetInsertionPoint()
        line_start = self.file_paths_ctrl.GetRange(0, cursor_pos).rfind("\n") + 1
        line_end = self.file_paths_ctrl.GetValue().find("\n", cursor_pos)
        if line_end == -1:
            line_end = len(self.file_paths_ctrl.GetValue())

        selected_text = self.file_paths_ctrl.GetRange(line_start, line_end)

        if selected_text:
            # استخراج مسیر فایل از متن انتخاب شده
            file_path = selected_text.split("   |   ")[0].strip()

            # تبدیل مسیر نسبی به مطلق
            absolute_path = os.path.join(self.folder_path, file_path)

            # بررسی وجود فایل قبل از اضافه کردن به لیست
            if os.path.exists(absolute_path):
                if key_code == wx.WXK_SPACE:
                    if absolute_path not in self.selected_files:
                        self.selected_files.append(absolute_path)
                        self.update_selected_count()
                elif key_code == wx.WXK_ALT:
                    if absolute_path in self.selected_files:
                        self.selected_files.remove(absolute_path)
                        self.update_selected_count()
            else:
                prepend_text_to_json(json_log_path, absolute_path)

        event.Skip()

    def on_delete_selected(self, event):
        if not self.selected_files:
            wx.MessageBox("هیچ فایلی انتخاب نشده است!", "خطا", wx.OK | wx.ICON_WARNING)
            return

        # حذف دستی فایل‌های انتخاب شده (فقط فایل‌های انتخاب شده)
        self.file_handler.delete_selected_files(self.selected_files, prioritize_old=False)
        self.selected_files = []
        self.files_list = self.file_handler.load_files()
        self.show_current_set()