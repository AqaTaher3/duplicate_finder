import wx
from duplicate_finder import DuplicateFinder
import os


class DuplicateFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_selected):
        super().__init__(parent, title=title, size=(800, 600))
        self.folder_selected = folder_selected
        self.current_set = 0
        self.click_count = {}

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(panel, label="Duplicate sets remaining: ")
        vbox.Add(self.status_label, flag=wx.ALL | wx.EXPAND, border=10)

        self.tree = wx.TreeCtrl(panel)
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click)
        vbox.Add(self.tree, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        button_panel = wx.Panel(panel)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.skip_button = wx.Button(button_panel, label="Skip")
        self.skip_button.Bind(wx.EVT_BUTTON, self.skip_current_set)
        button_sizer.Add(self.skip_button, flag=wx.RIGHT, border=10)

        self.exit_button = wx.Button(button_panel, label="Exit")
        self.exit_button.Bind(wx.EVT_BUTTON, self.exit_program)
        button_sizer.Add(self.exit_button, flag=wx.RIGHT, border=10)
        button_panel.SetSizer(button_sizer)

        vbox.Add(button_panel, flag=wx.ALL | wx.EXPAND, border=10)
        panel.SetSizer(vbox)
        self.Show()
        self.run_find_duplicates()

    def run_find_duplicates(self):
        finder = DuplicateFinder(self.folder_selected, None, None)
        self.duplicate_list = list(finder.find_duplicates().values())
        self.show_next_set()

    def show_next_set(self):
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("Duplicate Files")

        if self.current_set < len(self.duplicate_list):
            for file in self.duplicate_list[self.current_set]:
                self.tree.AppendItem(root, file)
            self.tree.Expand(root)  # This line ensures the items are expanded
            self.current_set += 1
            self.status_label.SetLabel(f"Duplicate sets remaining: {len(self.duplicate_list) - self.current_set}")
        else:
            self.status_label.SetLabel("No more duplicates. Review completed.")

    def skip_current_set(self, event):
        self.show_next_set()

    def exit_program(self, event):
        self.Close()

    def on_double_click(self, event):
        item = self.tree.GetSelection()
        file_path = self.tree.GetItemText(item)

        if file_path not in self.click_count:
            self.click_count[file_path] = 1
        else:
            self.click_count[file_path] += 1

        if self.click_count[file_path] == 2:
            self.delete_file(file_path)

    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            wx.MessageBox(f"File Deleted: {file_path}", "Info", wx.OK | wx.ICON_INFORMATION)
            self.show_next_set()  # Move to the next set after deletion
        except Exception as e:
            wx.MessageBox(f"Error Deleting File: {file_path}\n{str(e)}", "Error", wx.OK | wx.ICON_ERROR)
