# file: similar_files_frame.py
import wx
import os
import humanize
import datetime
from src3.similar_names import SimilarNameFinder


class SimilarFilesFrame(wx.Frame):
    def __init__(self, parent, folder_path, settings):
        super().__init__(parent, title="مدیریت فایل‌های با نام‌های مشابه", size=(1000, 650))

        self.folder_path = folder_path
        self.settings = settings
        self.groups = []
        self.current_group = 0
        self.selected_files = []  # فایل‌های انتخاب شده برای حذف

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # عنوان و اطلاعات
        self.status_label = wx.StaticText(self.panel, label="فایل‌های با نام‌های مشابه")
        self.status_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # جعبه متن برای نمایش فایل‌ها (مشابه پنجره اصلی)
        self.file_paths_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(700, 300))
        self.file_paths_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key_press)
        self.file_paths_ctrl.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.file_paths_ctrl.SetForegroundColour(wx.Colour(230, 210, 181))

        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.file_paths_ctrl.SetFont(font)

        self.vbox.Add(self.file_paths_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        # دکمه‌های کنترل
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_prev = wx.Button(self.panel, label="گروه قبلی")
        self.btn_prev.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        self.button_sizer.Add(self.btn_prev, 0, wx.ALL | wx.CENTER, 5)

        self.btn_next = wx.Button(self.panel, label="گروه بعدی")
        self.btn_next.Bind(wx.EVT_BUTTON, self.next_set)
        self.button_sizer.Add(self.btn_next, 0, wx.ALL | wx.CENTER, 5)

        self.btn_delete = wx.Button(self.panel, label="🗑️ حذف انتخاب‌ها")
        self.btn_delete.SetBackgroundColour(wx.Colour(220, 53, 69))
        self.btn_delete.SetForegroundColour(wx.WHITE)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        self.button_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 5)

        # دکمه‌های هوشمند
        self.btn_keep_oldest = wx.Button(self.panel, label="💾 نگه‌داری قدیمی‌ترین")
        self.btn_keep_oldest.SetBackgroundColour(wx.Colour(60, 179, 113))
        self.btn_keep_oldest.SetForegroundColour(wx.WHITE)
        self.btn_keep_oldest.Bind(wx.EVT_BUTTON, self.on_keep_oldest)
        self.button_sizer.Add(self.btn_keep_oldest, 0, wx.ALL | wx.CENTER, 5)

        self.btn_keep_largest = wx.Button(self.panel, label="💾 نگه‌داری بزرگترین")
        self.btn_keep_largest.SetBackgroundColour(wx.Colour(60, 179, 113))
        self.btn_keep_largest.SetForegroundColour(wx.WHITE)
        self.btn_keep_largest.Bind(wx.EVT_BUTTON, self.on_keep_largest)
        self.button_sizer.Add(self.btn_keep_largest, 0, wx.ALL | wx.CENTER, 5)

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        # نمایش تعداد انتخاب‌ها
        self.selected_count_label = wx.StaticText(self.panel, label="انتخاب شده: 0 فایل")
        self.selected_count_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        # شروع جستجو
        self.start_search()

        # رویدادها
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # راهنمای کلیدها
        help_text = wx.StaticText(self.panel, label="راهنما: Space = انتخاب/لغو • Delete = حذف مستقیم")
        help_text.SetForegroundColour(wx.Colour(180, 180, 180))
        self.vbox.Add(help_text, 0, wx.ALL | wx.CENTER, 5)

    def start_search(self):
        """شروع جستجوی فایل‌های مشابه"""
        self.status_label.SetLabel("در حال جستجوی فایل‌های مشابه...")
        wx.Yield()  # آپدیت UI

        try:
            # لیست کامل فرمت‌های تصویری و ویدیویی
            image_video_extensions = {
                "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif",
                "mp4", "avi", "mkv", "mov", "wmv", "flv", "webm",
                "heic", "heif", "svg", "ico", "psd", "raw"
            }

            # ایجاد شیء جستجو
            finder = SimilarNameFinder(
                self.folder_path,
                min_similarity=self.settings['min_similarity'],
                min_length=self.settings['min_length'],
                exclude_extensions=image_video_extensions  # ✅ پاس دادن لیست کامل
            )

            # جستجو
            self.groups = finder.find_similar_files()

            if self.groups:
                self.current_group = 0
                self.show_current_group()
                self.status_label.SetLabel(f"✅ یافت شد: {len(self.groups)} گروه فایل مشابه")
            else:
                self.status_label.SetLabel("❌ فایل مشابهی یافت نشد")
                self.file_paths_ctrl.SetValue("هیچ فایل با نام مشابه یافت نشد.")

        except Exception as e:
            wx.MessageBox(f"خطا در جستجو: {str(e)}", "خطا", wx.OK | wx.ICON_ERROR)
            self.status_label.SetLabel("❌ خطا در جستجو")

    def show_current_group(self):
        """نمایش گروه فعلی"""
        self.file_paths_ctrl.Clear()
        self.selected_files = []  # ریست انتخاب‌ها
        self.update_selected_count()

        if self.groups and 0 <= self.current_group < len(self.groups):
            file_group = self.groups[self.current_group]

            file_info_list = []

            for file in file_group:
                relative_path = os.path.relpath(file, self.folder_path)

                try:
                    size = os.path.getsize(file)
                    size_str = humanize.naturalsize(size, binary=True)

                    modified_time = os.path.getmtime(file)
                    modified_date = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    size_str = "نامشخص"
                    modified_date = "نامشخص"

                # علامت اگر انتخاب شده
                prefix = "✓ " if file in self.selected_files else "  "

                file_info_list.append(f"{prefix}{relative_path}   |   {size_str}   |   {modified_date}")

            file_paths = "\n".join(file_info_list)
            self.file_paths_ctrl.SetValue(file_paths)

            # آپدیت وضعیت
            remaining = len(self.groups) - self.current_group - 1
            self.status_label.SetLabel(
                f"گروه {self.current_group + 1} از {len(self.groups)} ({remaining} گروه باقی‌مانده)")
        else:
            self.file_paths_ctrl.SetValue("هیچ گروهی برای نمایش وجود ندارد.")
            self.status_label.SetLabel("کار تمام شد!")

    def update_selected_count(self):
        """به‌روزرسانی تعداد انتخاب‌ها"""
        self.selected_count_label.SetLabel(f"انتخاب شده: {len(self.selected_files)} فایل")

    def next_set(self, event):
        """گروه بعدی"""
        if self.current_group < len(self.groups) - 1:
            self.current_group += 1
            self.show_current_group()

    def back_to_previous_set(self, event):
        """گروه قبلی"""
        if self.current_group > 0:
            self.current_group -= 1
            self.show_current_group()

    def on_key_press(self, event):
        """مدیریت کلیدهای صفحه‌کلید (Space برای انتخاب)"""
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
            # استخراج مسیر فایل (حذف ✓ و سایر اطلاعات)
            line_content = selected_line.replace("✓ ", "").strip()
            parts = line_content.split("   |   ")
            if parts:
                relative_path = parts[0].strip()
                absolute_path = os.path.join(self.folder_path, relative_path)

                # بررسی وجود فایل
                if os.path.exists(absolute_path):
                    if key_code == wx.WXK_SPACE:
                        # انتخاب/عدم‌انتخاب با Space
                        if absolute_path in self.selected_files:
                            self.selected_files.remove(absolute_path)
                        else:
                            self.selected_files.append(absolute_path)

                        # آپدیت نمایش
                        self.show_current_group()

                        # صدای کلیک (اختیاری)
                        event.Skip()
                        return

                    elif key_code == wx.WXK_DELETE:
                        # حذف مستقیم با Delete
                        self.delete_file(absolute_path)
                        event.Skip()
                        return

        event.Skip()

    def delete_file(self, file_path):
        """حذف یک فایل"""
        try:
            os.remove(file_path)
            print(f"✅ حذف شد: {os.path.basename(file_path)}")

            # حذف از لیست گروه فعلی
            if self.current_group < len(self.groups):
                group = self.groups[self.current_group]
                if file_path in group:
                    group.remove(file_path)

                    # اگر گروه خالی شد یا فقط یک فایل ماند
                    if len(group) <= 1:
                        del self.groups[self.current_group]
                        if self.current_group >= len(self.groups):
                            self.current_group = max(0, len(self.groups) - 1)

            # آپدیت نمایش
            self.show_current_group()

        except Exception as e:
            print(f"❌ خطا در حذف {file_path}: {e}")
            wx.MessageBox(f"خطا در حذف فایل:\n{str(e)}", "خطا", wx.OK | wx.ICON_ERROR)

    def on_delete_selected(self, event):
        """حذف فایل‌های انتخاب شده"""
        if not self.selected_files:
            wx.MessageBox("هیچ فایلی انتخاب نشده است!", "خطا", wx.OK | wx.ICON_WARNING)
            return

        # تأیید حذف
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
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"✅ حذف شد: {os.path.basename(file_path)}")
                else:
                    print(f"⚠️ فایل وجود ندارد: {file_path}")
            except PermissionError:
                # تلاش برای تغییر دسترسی و حذف مجدد
                try:
                    import stat
                    os.chmod(file_path, stat.S_IWRITE)
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"✅ حذف شد (با تغییر دسترسی): {os.path.basename(file_path)}")
                except Exception as e:
                    failed_files.append((os.path.basename(file_path), str(e)))
                    print(f"❌ حذف ناموفق: {file_path} - {e}")
            except Exception as e:
                failed_files.append((os.path.basename(file_path), str(e)))
                print(f"❌ خطا در حذف {file_path}: {e}")

        # حذف فایل‌های حذف شده از لیست گروه
        if self.current_group < len(self.groups):
            group = self.groups[self.current_group]
            remaining_files = [f for f in group if os.path.exists(f)]

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
            failed_list = "\n".join([f"• {name}: {error}" for name, error in failed_files[:5]])
            result_msg += f"\n\n⚠️ {len(failed_files)} فایل حذف نشد:\n{failed_list}"
            if len(failed_files) > 5:
                result_msg += f"\n... و {len(failed_files) - 5} فایل دیگر"

        wx.MessageBox(result_msg, "نتیجه حذف", wx.OK | wx.ICON_INFORMATION)

        # به‌روزرسانی نمایش
        self.selected_files = []
        self.show_current_group()

    def on_keep_oldest(self, event):
        """نگه‌داری قدیمی‌ترین فایل و حذف بقیه"""
        if self.current_group >= len(self.groups):
            return

        group = self.groups[self.current_group]
        if len(group) <= 1:
            return

        # یافتن قدیمی‌ترین فایل بر اساس تاریخ تغییر
        oldest_file = None
        oldest_time = float('inf')

        for file_path in group:
            try:
                mtime = os.path.getmtime(file_path)
                if mtime < oldest_time:
                    oldest_time = mtime
                    oldest_file = file_path
            except:
                pass

        if not oldest_file:
            wx.MessageBox("نمی‌توان تاریخ فایل‌ها را بررسی کرد.", "خطا", wx.OK | wx.ICON_ERROR)
            return

        # انتخاب همه به جز قدیمی‌ترین
        self.selected_files = [f for f in group if f != oldest_file]

        # حذف فایل‌های انتخاب شده
        self.on_delete_selected(event)

    def on_keep_largest(self, event):
        """نگه‌داری بزرگترین فایل و حذف بقیه"""
        if self.current_group >= len(self.groups):
            return

        group = self.groups[self.current_group]
        if len(group) <= 1:
            return

        # یافتن بزرگترین فایل
        largest_file = None
        largest_size = -1

        for file_path in group:
            try:
                size = os.path.getsize(file_path)
                if size > largest_size:
                    largest_size = size
                    largest_file = file_path
            except:
                pass

        if not largest_file:
            wx.MessageBox("نمی‌توان حجم فایل‌ها را بررسی کرد.", "خطا", wx.OK | wx.ICON_ERROR)
            return

        # انتخاب همه به جز بزرگترین
        self.selected_files = [f for f in group if f != largest_file]

        # حذف فایل‌های انتخاب شده
        self.on_delete_selected(event)

    def on_close(self, event):
        """وقتی پنجره بسته می‌شود"""
        # نمایش پیام خداحافظی
        if hasattr(self, 'groups') and self.groups:
            remaining = sum(len(g) for g in self.groups)
            wx.MessageBox(
                f"کار به پایان رسید!\n\n📊 آمار:\n• گروه‌های باقی‌مانده: {len(self.groups)}\n• فایل‌های باقی‌مانده: {remaining}",
                "پایان کار", wx.OK | wx.ICON_INFORMATION)

        event.Skip()

    def _get_normalized_name(self, file_path: str) -> str:
        """دریافت نام نرمال شده یک فایل (برای دیباگ)"""
        try:
            # ایجاد یک instance موقت از SimilarNameFinder
            from src3.similar_names import SimilarNameFinder
            finder = SimilarNameFinder(
                self.folder_path,
                min_similarity=self.settings['min_similarity'],
                min_length=self.settings['min_length']
            )
            return finder._normalize_filename(os.path.basename(file_path))
        except:
            return ""