import wx, os
from src1.gui import FileFinderFrame
from src1.logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
from src2.corrupted_files import move_corrupted_files, remove_duplicates_from_corrupted_folder_and_otherwhere
from src2.create_other_folders import making_folders
import sys
import ctypes
import platform

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
            move_corrupted_files(folder_selected, FFMPEG_PATH, corrupted_folder)
        remove_duplicates_from_corrupted_folder_and_otherwhere(folder_selected)
        handler = FileHandler(folder_selected, priority_folder, keep_folder)
        frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
        frame.Show()
        app.MainLoop()

        # حذف فولدر های خالی
        delete_empty_folders(folder_selected)
        # making_folders(folder_selected)

    else:
        wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

    # delete duplicate corrupted file in corrupted and other where





def is_admin():
    """بررسی آیا اسکریپت با دسترسی Administrator اجرا شده است"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def run_as_admin():
    """اجرای مجدد اسکریپت با دسترسی Administrator"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


if __name__ == "__main__":
    if platform.system() == "Windows":
        if not is_admin():
            print("درخواست دسترسی Administrator...")
            run_as_admin()
        else:
            print("دسترسی Administrator تایید شد")
            main()
    else:
        print("این اسکریپت فقط در ویندوز قابل اجراست")
        main()  # یا sys.exit(1) اگر فقط برای ویندوز طراحی شده
