import wx
from gui import FileFinderFrame
from logic import FileHandler


def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
    else:
        folder_selected = None

    dialog.Destroy()  # Ensure the dialog is always destroyed

    if folder_selected:
        # Create handler instance to handle the file logic
        handler = FileHandler(folder_selected)

        # Create the GUI frame and pass the handler instance along with folder
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()

        # Start the GUI event loop
        app.MainLoop()
    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)


if __name__ == "__main__":
    main()
