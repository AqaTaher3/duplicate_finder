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


def show_method_selection_dialog(parent, folder_path):
    """نمایش دیالوگ انتخاب روش بررسی فایل‌های تکراری"""
    dlg = wx.Dialog(parent, title="انتخاب روش بررسی", size=(500, 350))
    dlg.SetBackgroundColour(wx.Colour(43, 58, 68))

    panel = wx.Panel(dlg)
    panel.SetBackgroundColour(wx.Colour(43, 69, 60))

    vbox = wx.BoxSizer(wx.VERTICAL)

    # عنوان
    title = wx.StaticText(panel, label="روش بررسی فایل‌های تکراری را انتخاب کنید")
    title.SetForegroundColour(wx.Colour(230, 210, 181))
    title_font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    title.SetFont(title_font)
    vbox.Add(title, 0, wx.ALL | wx.CENTER, 20)

    # گزینه ۱: هش کردن (دقیق)
    btn_hash = wx.Button(panel, label="🔍 روش دقیق (هش کردن)", size=(400, 60))
    btn_hash.SetBackgroundColour(wx.Colour(60, 179, 113))
    btn_hash.SetForegroundColour(wx.WHITE)
    btn_hash.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    vbox.Add(btn_hash, 0, wx.ALL | wx.CENTER, 10)

    # توضیح گزینه ۱
    desc1 = wx.StaticText(panel,
                          label="• بررسی ۱۰۰٪ دقیق بر اساس محتوای فایل\n• کندتر اما کاملاً مطمئن\n• مناسب فایل‌های حیاتی")
    desc1.SetForegroundColour(wx.Colour(200, 200, 200))
    vbox.Add(desc1, 0, wx.ALL | wx.LEFT, 30)

    # گزینه ۲: نام مشابه (سریع)
    btn_name = wx.Button(panel, label="⚡ روش سریع (نام مشابه)", size=(400, 60))
    btn_name.SetBackgroundColour(wx.Colour(70, 130, 180))
    btn_name.SetForegroundColour(wx.WHITE)
    btn_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    vbox.Add(btn_name, 0, wx.ALL | wx.CENTER, 10)

    # توضیح گزینه ۲
    desc2 = wx.StaticText(panel,
                          label="• بررسی بر اساس شباهت نام فایل‌ها\n• بسیار سریع\n• مناسب فایل‌های رسانه و مستندات")
    desc2.SetForegroundColour(wx.Colour(200, 200, 200))
    vbox.Add(desc2, 0, wx.ALL | wx.LEFT, 30)

    # دکمه انصراف
    btn_cancel = wx.Button(panel, label="انصراف", size=(200, 40))
    vbox.Add(btn_cancel, 0, wx.ALL | wx.CENTER, 10)

    panel.SetSizer(vbox)

    # تنظیم نتیجه
    result = {"method": None}

    def on_hash_method(event):
        result["method"] = "hash"
        dlg.EndModal(wx.ID_OK)

    def on_name_method(event):
        result["method"] = "name"
        dlg.EndModal(wx.ID_OK)

    def on_cancel(event):
        result["method"] = None
        dlg.EndModal(wx.ID_CANCEL)

    btn_hash.Bind(wx.EVT_BUTTON, on_hash_method)
    btn_name.Bind(wx.EVT_BUTTON, on_name_method)
    btn_cancel.Bind(wx.EVT_BUTTON, on_cancel)

    if dlg.ShowModal() == wx.ID_OK:
        return result["method"]
    return None


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
            # نمایش منوی انتخاب روش
            method = show_method_selection_dialog(None, folder_selected)
            if method is None:
                print("عملیات توسط کاربر لغو شد.")
                return

            change_folder_permissions(folder_selected)
            [keep_folder, priority_folder, corrupted_folder] = making_folders(folder_selected)

            if finding_corrupted_files:
                move_corrupted_files(folder_selected, FFMPEG_PATH, corrupted_folder)

            remove_duplicates_from_corrupted_folder_and_otherwhere(folder_selected)

            if method == "hash":
                # روش هش کردن
                handler = FileHandler(folder_selected, priority_folder, keep_folder)
                frame = FileFinderFrame(None, "File Finder", folder_selected, handler)
                frame.Show()
                app.MainLoop()

                # بعد از بسته شدن، پیشنهاد روش نام مشابه
                dlg = wx.MessageDialog(None,
                                       "آیا می‌خواهید فایل‌های با نام‌های مشابه را نیز بررسی کنید؟",
                                       "بررسی اضافی",
                                       wx.YES_NO | wx.ICON_QUESTION)

                if dlg.ShowModal() == wx.ID_YES:
                    dlg.Destroy()

                    # تنظیمات برای نام مشابه
                    settings_dlg = SimilarFilesSettingsDialog(None)
                    if settings_dlg.ShowModal() == wx.ID_OK:
                        settings = settings_dlg.get_settings()
                        similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                        similar_frame.Show()

                        # اجرای برنامه جدید
                        app2 = wx.App(False)
                        app2.MainLoop()
                else:
                    dlg.Destroy()

            elif method == "name":
                # روش نام مشابه (مستقیم)
                settings_dlg = SimilarFilesSettingsDialog(None)
                if settings_dlg.ShowModal() == wx.ID_OK:
                    settings = settings_dlg.get_settings()
                    similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                    similar_frame.Show()
                    app.MainLoop()

            # حذف فولدر های خالی
            delete_empty_folders(folder_selected)

        else:
            wx.MessageBox("No folder selected, exiting application.", "Error", wx.OK | wx.ICON_ERROR)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()