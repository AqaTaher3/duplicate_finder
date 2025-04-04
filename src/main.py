import wx
from gui import FileFinderFrame
from logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
from src2.corrupted_files import move_corrupted_files
from src2.create_other_folders import making_folders

FFMPEG_PATH = r"D:\000_projects\librareis\ffmpeg\bin\ffmpeg.exe"

# finding_corrupted_files_from_000_PriorityFolder
finding_corrupted_files = False


def main():
    app = wx.App(False)

    dialog = wx.DirDialog(None, "Select a Folder")
    if dialog.ShowModal() == wx.ID_OK:
        folder_selected = dialog.GetPath()
    else:
        folder_selected = None

    dialog.Destroy()

    if folder_selected:
        [priority_folder, corrupted_folder] = making_folders()
        if finding_corrupted_files:
            move_corrupted_files(priority_folder, FFMPEG_PATH, corrupted_folder)
        handler = FileHandler(folder_selected, priority_folder_name="000_PriorityFolder")
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()
        app.MainLoop()

        # حذف فولدر های خالی
        delete_empty_folders(folder_selected)

    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)


if __name__ == "__main__":
    main()