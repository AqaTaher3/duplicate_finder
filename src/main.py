import wx
from src1.gui import FileFinderFrame
from src1.logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
from src2.corrupted_files import move_corrupted_files
from src2.create_other_folders import making_folders

FFMPEG_PATH = r"D:\000_projects\librareis\ffmpeg\bin\ffmpeg.exe"

# finding_corrupted_files_from_000_PriorityFolder  !!!! acting just for songs
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
        [keep_folder, priority_folder, corrupted_folder] = making_folders(folder_selected)
        if finding_corrupted_files:
            move_corrupted_files(priority_folder, FFMPEG_PATH, corrupted_folder)
        handler = FileHandler(folder_selected, priority_folder, keep_folder)
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()
        app.MainLoop()

        # حذف فولدر های خالی
        delete_empty_folders(folder_selected)
        making_folders(folder_selected)

    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)


if __name__ == "__main__":
    main()

    # Return only groups with duplicates
    # return [group for group in file_hashes.values() if len(group) > 1]
    # if len(file_hashes.values()) > 1:
    #     return file_hashes.values()
    # else:
    #     return None