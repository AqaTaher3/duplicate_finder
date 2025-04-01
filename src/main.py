import wx
from gui import FileFinderFrame
from logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
import os


def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
    else:
        folder_selected = None

    dialog.Destroy()

    if folder_selected:
        handler = FileHandler(folder_selected, priority_folder_name="000_PriorityFolder")
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()
        app.MainLoop()

        # حذف فولدرهای خالی
        priority_folder = os.path.join(folder_selected, '000_PriorityFolder')
        if os.path.exists(priority_folder):
            delete_empty_folders(priority_folder)
        else:
            print(f"Priority folder not found: {priority_folder}")
    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    main()