import wx
from gui import FileFinderFrame
from logic import FileHandler
from finder import FileFinder

def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
    else:
        folder_selected = None

    dialog.Destroy()

    if folder_selected:
        handler = FileHandler(folder_selected, priority_folder_name="000_PriorityFolder")  # تغییر اسم فولدر
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()
        app.MainLoop()
    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    main()