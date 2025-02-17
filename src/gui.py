import wx
from logic import FileHandler
import os
import datetime

class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(1000, 450))

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

        self.vbox.Add(self.button_sizer, 0, wx.ALL | wx.CENTER, 10)

        self.selected_count_label = wx.StaticText(self.panel, label="Selected files: 0")
        self.selected_count_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.vbox.Add(self.selected_count_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.vbox)

        self.show_current_set()

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
                print(f"⚠️ File not found: {absolute_path}")

        event.Skip()
    def on_delete_selected(self, event):
        if not self.selected_files:
            return

        self.file_handler.delete_selected_files(self.selected_files)  # فراخوانی تابع در منطق
        self.selected_files = []
        self.files_list = self.file_handler.load_files()
        self.show_current_set()
