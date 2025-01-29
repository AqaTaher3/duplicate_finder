import wx
from logic import FileHandler
import os


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(800, 400))

        self.folder_path = folder_path
        self.file_handler = file_handler
        self.current_set = 0
        self.files_list = self.file_handler.load_files() or []
        self.selected_files = []  # لیست فایل‌های انتخاب‌شده

        # ایجاد GUI با تم تیره
        self.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # برچسب وضعیت
        self.status_label = wx.StaticText(self.panel, label="Files remaining:")
        self.status_label.SetForegroundColour(wx.Colour(255, 255, 255))
        self.vbox.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        # لیست فایل‌ها در `wx.ListCtrl`
        self.file_list_ctrl = wx.ListCtrl(self.panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.file_list_ctrl.InsertColumn(0, "File Paths", width=700)
        self.file_list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.vbox.Add(self.file_list_ctrl, 1, wx.ALL | wx.EXPAND, 10)

        # دکمه‌ها
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

        # نمایش تعداد فایل‌های انتخاب‌شده
        self.selected_count_label = wx.StaticText(self.panel, label="Selected files: 0")
        self.selected_count_label.SetForegroundColour(wx.Colour(255, 255, 255))
        self.vbox.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        # نمایش اولین گروه فایل‌ها
        self.show_current_set()

    def update_selected_count(self):
        """به‌روزرسانی تعداد فایل‌های انتخاب‌شده"""
        self.selected_count_label.SetLabel(f"Selected files: {len(self.selected_files)}")

    def show_current_set(self):
        """یک گروه از فایل‌های تکراری را نمایش می‌دهد."""
        self.file_list_ctrl.DeleteAllItems()
        if self.files_list and 0 <= self.current_set < len(self.files_list):
            file_group = self.files_list[self.current_set]
            for file_path in file_group:
                index = self.file_list_ctrl.InsertItem(self.file_list_ctrl.GetItemCount(), file_path)
                if file_path in self.selected_files:
                    self.file_list_ctrl.SetItemBackgroundColour(index, wx.Colour(0, 0, 255))  # رنگ آبی برای انتخاب‌شده‌ها
            self.status_label.SetLabel(f"Files remaining: {len(self.files_list) - self.current_set}")
        else:
            index = self.file_list_ctrl.InsertItem(0, "No more duplicate files found.")
            self.file_list_ctrl.SetItemBackgroundColour(index, wx.Colour(100, 100, 100))

    def next_set(self, event):
        """نمایش گروه بعدی فایل‌های تکراری."""
        if self.current_set < len(self.files_list) - 1:
            self.current_set += 1
            self.show_current_set()

    def back_to_previous_set(self, event):
        """نمایش گروه قبلی فایل‌های تکراری."""
        if self.current_set > 0:
            self.current_set -= 1
            self.show_current_set()

    def delete_selected_files(self, event):
        """حذف فایل‌های انتخاب‌شده."""
        if not self.selected_files:
            return

        for file_path in self.selected_files:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"خطا در حذف فایل {file_path}: {e}")

        self.selected_files = []
        self.files_list = self.file_handler.load_files()
        self.show_current_set()

    def on_item_selected(self, event):
        """مدیریت انتخاب فایل‌ها در `wx.ListCtrl`"""
        index = event.GetIndex()
        item_text = self.file_list_ctrl.GetItemText(index)

        if item_text in self.selected_files:
            self.selected_files.remove(item_text)
            self.file_list_ctrl.SetItemBackgroundColour(index, wx.Colour(70, 70, 70))  # رنگ اصلی
        else:
            self.selected_files.append(item_text)
            self.file_list_ctrl.SetItemBackgroundColour(index, wx.Colour(0, 0, 255))  # رنگ آبی برای انتخاب‌شده‌ها

        self.update_selected_count()
