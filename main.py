import wx
from gui import DuplicateFinderFrame

def main():
    app = wx.App(False)
    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
        dialog.Destroy()
        if folder_selected:
            frame = DuplicateFinderFrame(None, "Duplicate Files", folder_selected)
            frame.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, frame.on_double_click)
            app.MainLoop()
    else:
        dialog.Destroy()
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    main()