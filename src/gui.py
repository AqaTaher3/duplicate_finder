import wx
from finder import DuplicateFinder
import os

class DuplicateFinderLogic:
    def __init__(self, folder_selected):
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []  # Store selected files
        self.duplicate_list = []  # List of duplicates
        self.load_duplicates()

    def load_duplicates(self):
        # Pass None for progress_bar and progress_label
        finder = DuplicateFinder(self.folder_selected, None, None)
        self.duplicate_list = list(finder.find_duplicates().values())

    def delete_selected_files(self):
        for file in self.selected_files:
            try:
                os.remove(file)
                print(f"File ---------->  {file}  -----------> Deleted")
            except Exception as e:
                print(f"Error Deleting File: {file}\n{str(e)}")
        self.selected_files.clear()

    def get_current_set_files(self):
        return self.duplicate_list[self.current_set] if self.duplicate_list else []

    def next_set(self):
        if self.current_set < len(self.duplicate_list) - 1:
            self.current_set += 1

    def back_to_previous_set(self):
        if self.current_set > 0:
            self.current_set -= 1

    def update_selected_count(self):
        return len(self.selected_files)

class DuplicateFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_selected, logic):
        super().__init__(parent, title=title, size=(800, 600))
        self.folder_selected = folder_selected
        self.logic = logic  # Store logic instance
        self.font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(45, 45, 48))  # Dark background

        vbox = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(panel, label="Duplicate sets remaining: ")
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

        self.back_button = wx.Button(button_panel, label="بازگشت")
        self.back_button.SetFont(self.font)
        self.back_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.back_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.back_button.Bind(wx.EVT_BUTTON, self.back_to_previous_set)
        button_sizer.Add(self.back_button, flag=wx.RIGHT, border=10)

        self.delete_button = wx.Button(button_panel, label="حذف موارد انتخاب‌شده تا الآن")
        self.delete_button.SetFont(self.font)
        self.delete_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.delete_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected_files)
        button_sizer.Add(self.delete_button, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        self.next_button = wx.Button(button_panel, label="بعدی")
        self.next_button.SetFont(self.font)
        self.next_button.SetBackgroundColour(wx.Colour(60, 60, 63))
        self.next_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.next_button.Bind(wx.EVT_BUTTON, self.next_set)
        button_sizer.Add(self.next_button, flag=wx.LEFT, border=10)

        button_panel.SetSizer(button_sizer)
        vbox.Add(button_panel, flag=wx.ALL | wx.EXPAND, border=10)

        panel.SetSizer(vbox)
        self.Show()
        self.run_find_duplicates()

    def run_find_duplicates(self):
        self.logic.load_duplicates()  # Ensure duplicates are loaded
        self.show_current_set()

    def show_current_set(self):
        self.tree.DeleteAllItems()
        root = self.tree.AddRoot("Duplicate Files")

        if self.logic.current_set < len(self.logic.duplicate_list):
            for file in self.logic.get_current_set_files():
                item = self.tree.AppendItem(root, file)
                self.tree.SetItemData(item, file)
            self.tree.Expand(root)
            self.status_label.SetLabel(f"Duplicate sets remaining: {len(self.logic.duplicate_list) - self.logic.current_set}")
        else:
            self.status_label.SetLabel("No more duplicates. Review completed.")

    def next_set(self, event):
        self.logic.next_set()
        self.show_current_set()

    def back_to_previous_set(self, event):
        self.logic.back_to_previous_set()
        self.show_current_set()

    def delete_selected_files(self, event):
        self.logic.delete_selected_files()
        self.update_selected_count()

    def on_item_activated(self, event):
        item = self.tree.GetSelection()
        if item.IsOk():
            file_path = self.tree.GetItemText(item)
            if file_path not in self.logic.selected_files:
                self.logic.selected_files.append(file_path)
                self.tree.SetItemTextColour(item, wx.Colour(0, 0, 255))  # Blue for selection
            else:
                self.logic.selected_files.remove(file_path)
                self.tree.SetItemTextColour(item, wx.Colour(255, 255, 255))  # White for deselection
            self.update_selected_count()

    def on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_SPACE:
            item = self.tree.GetSelection()
            if item.IsOk():
                file_path = self.tree.GetItemText(item)
                if file_path not in self.logic.selected_files:
                    self.logic.selected_files.append(file_path)
                    self.tree.SetItemTextColour(item, wx.Colour(0, 0, 255))  # Blue for selection
                else:
                    self.logic.selected_files.remove(file_path)
                    self.tree.SetItemTextColour(item, wx.Colour(255, 255, 255))  # White for deselection
                self.update_selected_count()
        event.Skip()

    def update_selected_count(self):
        selected_count = len(self.logic.selected_files)
        self.selected_count_label.SetLabel(f"Selected files: {selected_count}")

def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
        dialog.Destroy()

        if folder_selected:
            # Create logic instance to handle the duplicate file logic
            logic = DuplicateFinderLogic(folder_selected)

            # Create the GUI frame and pass the logic instance along with folder
            frame = DuplicateFinderFrame(None, "Duplicate Files", folder_selected, logic)

            # Start the GUI event loop
            app.MainLoop()

        else:
            wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)
    else:
        dialog.Destroy()

if __name__ == "__main__":
    main()
