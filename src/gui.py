import wx
from logic import FileHandler
import os


class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_selected, handler):
        super().__init__(parent, title=title, size=(800, 600))
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []  # Store selected files
        self.font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.handler = handler

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(45, 45, 48))  # Dark background

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(panel, label="Files remaining: ")
        self.status_label.SetFont(self.font)
        self.status_label.SetForegroundColour(wx.Colour(255, 255, 255))
        vbox.Add(self.status_label, flag=wx.ALL | wx.EXPAND, border=10)

        self.tree = wx.TreeCtrl(panel)
        self.tree.SetFont(self.font)
        self.tree.SetBackgroundColour(wx.Colour(45, 45, 48))
        self.tree.SetForegroundColour(wx.Colour(255, 255, 255))
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activated)
        self.tree.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        vbox.Add(self.tree, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.selected_count_label = wx.StaticText(panel, label="Selected files: 0")
        self.selected_count_label.SetFont(self.font)
        self.selected_count_label.SetForegroundColour(wx.Colour(255, 255, 255))
        vbox.Add(self.selected_count_label, flag=wx.ALL | wx.EXPAND, border=10)

        button_panel = wx.Panel(panel)
        button_panel.SetBackgroundColour(wx.Colour(45, 45, 48))
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.back_button = wx.Button(button_panel, label="Back")
        self.back_button.SetFont(self.font)
        self.back_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.back_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.back_button.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        button_sizer.Add(self.back_button, flag=wx.RIGHT, border=10)

        self.delete_button = wx.Button(button_panel, label="Delete Selected Files")
        self.delete_button.SetFont(self.font)
        self.delete_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.delete_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected_files)
        button_sizer.Add(self.delete_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.next_button = wx.Button(button_panel, label="Next")
        self.next_button.SetFont(self.font)
        self.next_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.next_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.next_button.Bind(wx.EVT_BUTTON, self.next_set)
        button_sizer.Add(self.next_button, flag=wx.LEFT, border=10)

        button_panel.SetSizer(button_sizer)
        vbox.Add(button_panel, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)

        # Add the text control after the sizer has been set
        self.file_paths_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(500, 400))
        vbox.Add(self.file_paths_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.Show()
        self.run_find_files()

    def run_find_files(self):
        self.files_list = self.handler.load_files()  # بارگذاری فایل‌ها
        if not self.files_list:  # بررسی اینکه لیست فایل‌ها خالی نباشد
            wx.MessageBox("No files found or an error occurred while loading files.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            self.show_current_set()  # نمایش فایل‌ها در GUI

    def show_current_set(self):
        if self.files_list:
            # مسیرها را به صورت جداگانه نمایش بده
            file_paths = "\n".join(self.files_list)  # جدا کردن مسیرها با خط جدید
            self.file_paths_ctrl.SetValue(file_paths)  # نمایش مسیرها در wx.TextCtrl
        else:
            wx.MessageBox("No files found or an error occurred while loading files.", "Error", wx.OK | wx.ICON_ERROR)

    def next_set(self, event):
        if self.current_set < len(self.files_list) - 1:
            self.current_set += 1
            self.show_current_set()

    def back_to_previous_set(self, event):
        if self.current_set > 0:
            self.current_set -= 1
            self.show_current_set()

    def delete_selected_files(self, event):
        for file in self.selected_files:
            try:
                os.remove(file)
                print(f"File ---------->  {file}  -----------> Deleted")
                wx.MessageBox(f"File Deleted: {file}", "Info", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                print(f"Error Deleting File: {file}\n{str(e)}")
                wx.MessageBox(f"Error Deleting File: {file}\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)
        self.selected_files.clear()
        self.update_selected_count()

    def on_item_activated(self, event):
        item = self.tree.GetSelection()
        if item.IsOk():
            file_path = self.tree.GetItemText(item)
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
                self.tree.SetItemTextColour(item, wx.Colour(0, 0, 255))  # Blue for selection
            else:
                self.selected_files.remove(file_path)
                self.tree.SetItemTextColour(item, wx.Colour(255, 255, 255))  # White for deselection
            self.update_selected_count()

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            item = self.tree.GetSelection()
            if item.IsOk():
                file_path = self.tree.GetItemText(item)
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self.tree.SetItemTextColour(item, wx.Colour(0, 0, 255))  # Blue for selection
                else:
                    self.selected_files.remove(file_path)
                    self.tree.SetItemTextColour(item, wx.Colour(255, 255, 255))  # White for deselection
                self.update_selected_count()
        elif event.GetKeyCode() == wx.WXK_ALT:
            item = self.tree.GetSelection()
            if item.IsOk():
                file_path = self.tree.GetItemText(item)
                if file_path in self.selected_files:
                    self.selected_files.remove(file_path)
                    self.tree.SetItemTextColour(item, wx.Colour(255, 255, 255))  # White for deselection
                self.update_selected_count()
        event.Skip()

    def update_selected_count(self):
        selected_count = len(self.selected_files)
        self.selected_count_label.SetLabel(f"Selected files: {selected_count}")
