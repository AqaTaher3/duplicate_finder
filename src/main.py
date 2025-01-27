import wx
from finder import DuplicateFinder  # Instead of DuplicateFinderLogic
from gui import *
from logic import *
from finder import *


def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
        dialog.Destroy()

        if folder_selected:
            # Create logic instance to handle the duplicate file logic
            logic = DuplicateFinderLogic(folder_selected)

            # Pass None for progress_bar and progress_label
            finder = DuplicateFinder(folder_selected, None, None)
            logic = DuplicateFinderLogic(folder_selected)  # Ensure this is set up properly
            frame = DuplicateFinderFrame(None, "Duplicate Files", folder_selected, logic)

            # Start the GUI event loop
            app.MainLoop()

        else:
            print("No folder selected, exiting application.", "Error")
    else:
        dialog.Destroy()


if __name__ == "__main__":
    main()