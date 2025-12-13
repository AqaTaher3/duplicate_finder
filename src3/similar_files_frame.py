import wx
import os
import humanize
from src3.similar_names import SimilarNameFinder


class SimilarFilesFrame(wx.Frame):
    def __init__(self, parent, folder_path, settings):
        super().__init__(parent, title="مدیریت فایل‌های با نام‌های مشابه", size=(1200, 700))

        self.folder_path = folder_path
        self.settings = settings
        self.groups = []
        self.current_group = 0
        self.selected_files = []  # فایل‌های انتخاب شده برای حذف

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # عنوان و اطلاعات
        self.title_label = wx.StaticText(panel, label="فایل‌های با نام‌های مشابه")
        self.title_label.SetForegroundColour(wx.Colour(230, 210, 181))
        title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.title_label.SetFont(title_font)
        self.main_sizer.Add(self.title_label, 0, wx.ALL | wx.CENTER, 10)

        # اطلاعات گروه فعلی
        info_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.group_info = wx.StaticText(panel, label="گروه 0 از 0")
        self.group_info.SetForegroundColour(wx.Colour(200, 200, 200))
        info_sizer.Add(self.group_info, 0, wx.ALL | wx.CENTER, 10)

        self.files_count = wx.StaticText(panel, label="تعداد فایل‌ها: 0")
        self.files_count.SetForegroundColour(wx.Colour(200, 200, 200))
        info_sizer.Add(self.files_count, 0, wx.ALL | wx.CENTER, 10)

        self.total_size = wx.StaticText(panel, label="حجم کل: 0 MB")
        self.total_size.SetForegroundColour(wx.Colour(200, 200, 200))
        info_sizer.Add(self.total_size, 0, wx.ALL | wx.CENTER, 10)

        self.main_sizer.Add(info_sizer, 0, wx.ALL | wx.CENTER, 5)

        # لیست فایل‌ها با جزئیات
        self.create_file_list(panel)

        # دکمه‌های کنترل
        self.create_control_buttons(panel)

        # دکمه‌های عملیاتی
        self.create_action_buttons(panel)

        # وضعیت
        self.status_label = wx.StaticText(panel, label="آماده")
        self.status_label.SetForegroundColour(wx.Colour(180, 180, 180))
        self.main_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(self.main_sizer)

        # شروع جستجو
        self.start_search()

        # رویدادها
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def create_file_list(self, panel):
        """ایجاد لیست فایل‌ها با جزئیات"""
        # استفاده از ListCtrl برای نمایش بهتر
        self.file_list = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN)
        self.file_list.SetBackgroundColour(wx.Colour(60, 70, 80))
        self.file_list.SetForegroundColour(wx.Colour(230, 210, 181))

        # تنظیم ستون‌ها
        self.file_list.InsertColumn(0, "انتخاب", width=50)
        self.file_list.InsertColumn(1, "نام فایل", width=300)
        self.file_list.InsertColumn(2, "مسیر", width=400)
        self.file_list.InsertColumn(3, "حجم", width=100)
        self.file_list.InsertColumn(4, "تاریخ تغییر", width=120)
        self.file_list.InsertColumn(5, "پسوند", width=80)

        self.main_sizer.Add(self.file_list, 1, wx.ALL | wx.EXPAND, 10)

        # رویداد کلیک روی آیتم‌ها
        self.file_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.file_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_item_deselected)

    def create_control_buttons(self, panel):
        """ایجاد دکمه‌های کنترل"""
        control_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(panel, label="⏪ گروه قبلی", size=(120, 40))
        self.btn_prev.Bind(wx.EVT_BUTTON, self.on_prev_group)
        control_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(panel, label="گروه بعدی ⏩", size=(120, 40))
        self.btn_next.Bind(wx.EVT_BUTTON, self.on_next_group)
        control_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_select_all = wx.Button(panel, label="انتخاب همه", size=(100, 40))
        self.btn_select_all.Bind(wx.EVT_BUTTON, self.on_select_all)
        control_sizer.Add(self.btn_select_all, 0, wx.ALL | wx.CENTER, 5)

        self.btn_deselect_all = wx.Button(panel, label="لغو انتخاب", size=(100, 40))
        self.btn_deselect_all.Bind(wx.EVT_BUTTON, self.on_deselect_all)
        control_sizer.Add(self.btn_deselect_all, 0, wx.ALL | wx.CENTER, 5)

        self.main_sizer.Add(control_sizer, 0, wx.ALL | wx.CENTER, 10)

    def create_action_buttons(self, panel):
        """ایجاد دکمه‌های عملیاتی"""
        action_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_preview = wx.Button(panel, label="🔍 پیش‌نمایش", size=(120, 45))
        self.btn_preview.SetBackgroundColour(wx.Colour(70, 130, 180))
        self.btn_preview.SetForegroundColour(wx.WHITE)
        self.btn_preview.Bind(wx.EVT_BUTTON, self.on_preview)
        action_sizer.Add(self.btn_preview, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete_selected = wx.Button(panel, label="🗑️ حذف انتخاب‌ها", size=(140, 45))
        self.btn_delete_selected.SetBackgroundColour(wx.Colour(220, 53, 69))
        self.btn_delete_selected.SetForegroundColour(wx.WHITE)
        self.btn_delete_selected.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        action_sizer.Add(self.btn_delete_selected, 0, wx.ALL | wx.CENTER, 5)

        self.btn_keep_oldest = wx.Button(panel, label="💾 نگه‌داری قدیمی‌ترین", size=(150, 45))
        self.btn_keep_oldest.SetBackgroundColour(wx.Colour(60, 179, 113))
        self.btn_keep_oldest.SetForegroundColour(wx.WHITE)
        self.btn_keep_oldest.Bind(wx.EVT_BUTTON, self.on_keep_oldest)
        action_sizer.Add(self.btn_keep_oldest, 0, wx.ALL | wx.CENTER, 5)

        self.btn_keep_largest = wx.Button(panel, label="💾 نگه‌داری بزرگترین", size=(150, 45))
        self.btn_keep_largest.SetBackgroundColour(wx.Colour(60, 179, 113))
        self.btn_keep_largest.SetForegroundColour(wx.WHITE)
        self.btn_keep_largest.Bind(wx.EVT_BUTTON, self.on_keep_largest)
        action_sizer.Add(self.btn_keep_largest, 0, wx.ALL | wx.CENTER, 5)

        self.btn_skip = wx.Button(panel, label="⏭️ رد کردن گروه", size=(120, 45))
        self.btn_skip.SetBackgroundColour(wx.Colour(108, 117, 125))
        self.btn_skip.SetForegroundColour(wx.WHITE)
        self.btn_skip.Bind(wx.EVT_BUTTON, self.on_skip_group)
        action_sizer.Add(self.btn_skip, 0, wx.ALL | wx.CENTER, 5)

        self.main_sizer.Add(action_sizer, 0, wx.ALL | wx.CENTER, 10)

    def start_search(self):
        """شروع جستجوی فایل‌های مشابه"""
        self.status_label.SetLabel("در حال جستجوی فایل‌های مشابه...")

        # ایجاد دیالوگ پیشرفت
        progress_dlg = wx.ProgressDialog(
            "جستجوی فایل‌های مشابه",
            "در حال بررسی نام فایل‌ها...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME
        )

        def update_progress(progress, message):
            if progress_dlg:
                progress_dlg.Update(progress, message)

        try:
            # ایجاد شیء جستجو
            finder = SimilarNameFinder(
                self.folder_path,
                min_similarity=self.settings['min_similarity'],
                min_length=self.settings['min_length']
            )

            # جستجو
            self.groups = finder.find_similar_files(update_progress)

            if self.groups:
                self.current_group = 0
                self.show_current_group()
                self.status_label.SetLabel(f"✅ یافت شد: {len(self.groups)} گروه فایل مشابه")
            else:
                self.status_label.SetLabel("❌ فایل مشابهی یافت نشد")
                wx.MessageBox("هیچ فایل با نام مشابه یافت نشد.", "اطلاع", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            wx.MessageBox(f"خطا در جستجو: {str(e)}", "خطا", wx.OK | wx.ICON_ERROR)
            self.status_label.SetLabel("❌ خطا در جستجو")
        finally:
            progress_dlg.Destroy()

    def show_current_group(self):
        """نمایش گروه فعلی"""
        if not self.groups or self.current_group >= len(self.groups):
            return

        self.file_list.DeleteAllItems()
        self.selected_files = []

        group = self.groups[self.current_group]
        total_size = 0

        for i, file_path in enumerate(group):
            try:
                # اطلاعات فایل
                size = os.path.getsize(file_path)
                total_size += size

                filename = os.path.basename(file_path)
                dir_path = os.path.dirname(file_path)
                extension = os.path.splitext(filename)[1]

                # تاریخ تغییر
                mtime = os.path.getmtime(file_path)
                from datetime import datetime
                date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

                # افزودن به لیست
                index = self.file_list.InsertItem(i, "")
                self.file_list.SetItem(index, 0, "")
                self.file_list.SetItem(index, 1, filename)
                self.file_list.SetItem(index, 2, dir_path)
                self.file_list.SetItem(index, 3, humanize.naturalsize(size, binary=True))
                self.file_list.SetItem(index, 4, date_str)
                self.file_list.SetItem(index, 5, extension)

                # ستون انتخاب
                self.file_list.SetItemData(index, i)

            except Exception as e:
                print(f"Error showing file {file_path}: {e}")

        # آپدیت اطلاعات گروه
        self.group_info.SetLabel(f"گروه {self.current_group + 1} از {len(self.groups)}")
        self.files_count.SetLabel(f"تعداد فایل‌ها: {len(group)}")
        self.total_size.SetLabel(f"حجم کل: {humanize.naturalsize(total_size, binary=True)}")

    def on_item_selected(self, event):
        """وقتی آیتمی انتخاب می‌شود"""
        index = event.GetIndex()
        if 0 <= index < len(self.groups[self.current_group]):
            # تغییر آیکون انتخاب
            self.file_list.SetItem(index, 0, "✓")

            file_path = self.groups[self.current_group][index]
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)

    def on_item_deselected(self, event):
        """وقتی انتخاب آیتم لغو می‌شود"""
        index = event.GetIndex()
        if 0 <= index < len(self.groups[self.current_group]):
            # حذف آیکون انتخاب
            self.file_list.SetItem(index, 0, "")

            file_path = self.groups[self.current_group][index]
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)

    def on_select_all(self, event):
        """انتخاب همه فایل‌های گروه فعلی"""
        group = self.groups[self.current_group]
        self.selected_files = group.copy()

        for i in range(len(group)):
            self.file_list.SetItem(i, 0, "✓")
            self.file_list.Select(i, 1)

    def on_deselect_all(self, event):
        """لغو انتخاب همه"""
        self.selected_files = []
        for i in range(self.file_list.GetItemCount()):
            self.file_list.SetItem(i, 0, "")
            self.file_list.Select(i, 0)

    def on_prev_group(self, event):
        """گروه قبلی"""
        if self.current_group > 0:
            self.current_group -= 1
            self.show_current_group()

    def on_next_group(self, event):
        """گروه بعدی"""
        if self.current_group < len(self.groups) - 1:
            self.current_group += 1
            self.show_current_group()

    def on_preview(self, event):
        """پیش‌نمایش فایل انتخاب شده"""
        if not self.selected_files:
            wx.MessageBox("لطفاً ابتدا فایلی را انتخاب کنید.", "هشدار", wx.OK | wx.ICON_WARNING)
            return

        # باز کردن فایل با برنامه پیش‌فرض
        for file_path in self.selected_files[:3]:  # حداکثر 3 فایل
            try:
                os.startfile(file_path)
            except:
                wx.MessageBox(f"نمی‌توان فایل را باز کرد: {os.path.basename(file_path)}",
                              "خطا", wx.OK | wx.ICON_ERROR)

    def on_delete_selected(self, event):
        """حذف فایل‌های انتخاب شده"""
        if not self.selected_files:
            wx.MessageBox("هیچ فایلی برای حذف انتخاب نشده است.", "هشدار", wx.OK | wx.ICON_WARNING)
            return

        # تأیید
        confirm_msg = f"آیا از حذف {len(self.selected_files)} فایل انتخاب شده مطمئن هستید؟\nاین عمل غیرقابل بازگشت است!"
        dlg = wx.MessageDialog(self, confirm_msg, "تأیید حذف",
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)

        if dlg.ShowModal() != wx.ID_YES:
            dlg.Destroy()
            return
        dlg.Destroy()

        # حذف فایل‌ها
        deleted_count = 0
        failed_files = []

        for file_path in self.selected_files:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                failed_files.append((os.path.basename(file_path), str(e)))

        # حذف فایل‌های حذف شده از لیست گروه
        group = self.groups[self.current_group]
        remaining_files = [f for f in group if f not in self.selected_files]

        if len(remaining_files) <= 1:
            # اگر 0 یا 1 فایل باقی ماند، گروه را حذف کن
            del self.groups[self.current_group]
            if self.current_group >= len(self.groups):
                self.current_group = max(0, len(self.groups) - 1)
        else:
            # به‌روزرسانی گروه
            self.groups[self.current_group] = remaining_files

        # نمایش نتیجه
        result_msg = f"✅ {deleted_count} فایل با موفقیت حذف شد."
        if failed_files:
            failed_msg = "\n\nفایل‌های حذف نشده:\n"
            for filename, error in failed_files[:5]:
                failed_msg += f"• {filename}: {error}\n"
            result_msg += failed_msg

        wx.MessageBox(result_msg, "نتیجه حذف", wx.OK | wx.ICON_INFORMATION)

        # به‌روزرسانی نمایش
        self.selected_files = []
        self.show_current_group()

    def on_keep_oldest(self, event):
        """نگه‌داری قدیمی‌ترین فایل و حذف بقیه"""
        group = self.groups[self.current_group]
        if len(group) <= 1:
            return

        # یافتن قدیمی‌ترین فایل بر اساس تاریخ تغییر
        oldest_file = min(group, key=lambda x: os.path.getmtime(x))

        # انتخاب همه به جز قدیمی‌ترین
        self.selected_files = [f for f in group if f != oldest_file]

        # اجرای حذف
        self.on_delete_selected(event)

    def on_keep_largest(self, event):
        """نگه‌داری بزرگترین فایل و حذف بقیه"""
        group = self.groups[self.current_group]
        if len(group) <= 1:
            return

        # یافتن بزرگترین فایل
        largest_file = max(group, key=lambda x: os.path.getsize(x))

        # انتخاب همه به جز بزرگترین
        self.selected_files = [f for f in group if f != largest_file]

        # اجرای حذف
        self.on_delete_selected(event)

    def on_skip_group(self, event):
        """رد کردن گروه فعلی"""
        if self.current_group < len(self.groups) - 1:
            self.current_group += 1
            self.show_current_group()
        else:
            self.status_label.SetLabel("آخرین گروه رسیده‌اید")

    def on_close(self, event):
        """وقتی پنجره بسته می‌شود"""
        # ذخیره نتایج
        self.save_results()
        event.Skip()

    def save_results(self):
        """ذخیره نتایج در فایل"""
        try:
            results_file = os.path.join(self.folder_path, "similar_files_results.txt")
            with open(results_file, 'w', encoding='utf-8') as f:
                f.write(f"نتایج جستجوی فایل‌های مشابه\n")
                f.write(f"تاریخ: {wx.DateTime.Now().Format('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"پوشه: {self.folder_path}\n")
                f.write(f"تعداد گروه‌ها: {len(self.groups)}\n")
                f.write("=" * 80 + "\n\n")

                for i, group in enumerate(self.groups):
                    f.write(f"\nگروه {i + 1} ({len(group)} فایل):\n")
                    for file_path in group:
                        size = os.path.getsize(file_path)
                        f.write(f"  • {os.path.basename(file_path)} | {humanize.naturalsize(size)} | {file_path}\n")

            print(f"نتایج در {results_file} ذخیره شد.")
        except Exception as e:
            print(f"خطا در ذخیره نتایج: {e}")