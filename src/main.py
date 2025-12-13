import wx, os, stat
from src1.gui import FileFinderFrame
from src1.logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
from src2.corrupted_files import move_corrupted_files, remove_duplicates_from_corrupted_folder_and_otherwhere
from src2.create_other_folders import making_folders
from src3.similar_files_frame import SimilarFilesFrame
from src3.settings_dialog import SimilarFilesSettingsDialog

FFMPEG_PATH = r"D:\000_projects\librareis\ffmpeg\bin\ffmpeg.exe"
finding_corrupted_files = False


def change_folder_permissions(folder_path):
    """تغییر دسترسی پوشه"""
    for root, dirs, files in os.walk(folder_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                os.chmod(dir_path, stat.S_IWRITE)
            except:
                pass
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                os.chmod(file_path, stat.S_IWRITE)
            except:
                pass


def ask_for_similar_files_search(parent, folder_path):
    """سؤال از کاربر برای جستجوی فایل‌های مشابه"""
    dlg = wx.MessageDialog(parent,
                           "آیا می‌خواهید فایل‌های با نام‌های مشابه را نیز بررسی کنید؟\n\n"
                           "این ویژگی فایل‌هایی که نام‌های شبیه به هم دارند را پیدا می‌کند.\n"
                           "مثال: 'document_final.pdf' و 'document_final_v2.pdf'",
                           "جستجوی فایل‌های مشابه",
                           wx.YES_NO | wx.ICON_QUESTION | wx.YES_DEFAULT)

    result = dlg.ShowModal()
    dlg.Destroy()

    return result == wx.ID_YES


def main():
    try:
        app = wx.App(False)

        dialog = wx.DirDialog(None, "Select a Folder")
        if dialog.ShowModal() == wx.ID_OK:
            folder_selected = dialog.GetPath()
        else:
            folder_selected = None

        dialog.Destroy()

        if folder_selected:
            change_folder_permissions(folder_selected)
            [keep_folder, priority_folder, corrupted_folder] = making_folders(folder_selected)

            if finding_corrupted_files:
                move_corrupted_files(folder_selected, FFMPEG_PATH, corrupted_folder)

            remove_duplicates_from_corrupted_folder_and_otherwhere(folder_selected)
            handler = FileHandler(folder_selected, priority_folder, keep_folder)

            # اجرای پنجره اصلی
            frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
            frame.Show()
            app.MainLoop()

            # بعد از بسته شدن پنجره اصلی، بررسی فایل‌های مشابه
            if ask_for_similar_files_search(None, folder_selected):
                # نمایش دیالوگ تنظیمات
                settings_dlg = SimilarFilesSettingsDialog(None)
                if settings_dlg.ShowModal() == wx.ID_OK:
                    settings = settings_dlg.get_settings()

                    # اجرای پنجره جستجوی فایل‌های مشابه
                    similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                    similar_frame.Show()

                    # اجرای loop جدید
                    app2 = wx.App(False)
                    app2.MainLoop()

            # حذف فولدر های خالی
            delete_empty_folders(folder_selected)

        else:
            wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()