import wx, os, stat
import traceback
from src1.gui import FileFinderFrame
from src1.logic import FileHandler
from src2.delete_empty_folders import delete_empty_folders
from src2.corrupted_files import move_corrupted_files, remove_duplicates_from_corrupted_folder_and_otherwhere
from src2.create_other_folders import making_folders
from src3.similar_files_frame import SimilarFilesFrame
from src3.settings_dialog import SimilarFilesSettingsDialog
from log_manager import log_manager
from config import config  # ✅ اضافه کردن import


logger = log_manager.get_logger("main")
log_manager.log_startup()

FFMPEG_PATH = config.get("ffmpeg_path")  # ✅
finding_corrupted_files = config.get("finding_corrupted_files")  # ✅


def change_folder_permissions(folder_path):
    """تغییر دسترسی پوشه - بهینه‌سازی شده"""
    try:
        for root, dirs, files in os.walk(folder_path):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.chmod(dir_path, stat.S_IWUSR | stat.S_IRUSR)
                except:
                    continue

            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    os.chmod(file_path, stat.S_IWUSR | stat.S_IRUSR)
                except:
                    continue
    except Exception as e:
        logger.error(f"خطا در تغییر دسترسی پوشه: {e}")


def show_method_selection_dialog(parent, folder_path):
    """نمایش دیالوگ انتخاب روش - بهینه‌سازی شده"""
    dlg = wx.Dialog(parent, title="انتخاب روش بررسی", size=(500, 380))
    dlg.SetBackgroundColour(wx.Colour(43, 58, 68))

    panel = wx.Panel(dlg)
    panel.SetBackgroundColour(wx.Colour(43, 69, 60))

    vbox = wx.BoxSizer(wx.VERTICAL)

    # عنوان
    title = wx.StaticText(panel, label="روش بررسی فایل‌های تکراری")
    title.SetForegroundColour(wx.Colour(230, 210, 181))
    title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    title.SetFont(title_font)
    vbox.Add(title, 0, wx.ALL | wx.CENTER, 20)

    # گزینه ۱: هش کردن
    btn_hash = wx.Button(panel, label="🔍 روش دقیق (هش کردن)")
    btn_hash.SetBackgroundColour(wx.Colour(60, 179, 113))
    btn_hash.SetForegroundColour(wx.WHITE)
    btn_hash.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    btn_hash.SetToolTip("بررسی ۱۰۰٪ دقیق بر اساس محتوای فایل")
    vbox.Add(btn_hash, 0, wx.ALL | wx.EXPAND, 10)

    # گزینه ۲: نام مشابه
    btn_name = wx.Button(panel, label="⚡ روش سریع (نام مشابه)")
    btn_name.SetBackgroundColour(wx.Colour(70, 130, 180))
    btn_name.SetForegroundColour(wx.WHITE)
    btn_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    btn_name.SetToolTip("بررسی بر اساس شباهت نام فایل‌ها")
    vbox.Add(btn_name, 0, wx.ALL | wx.EXPAND, 10)

    # گزینه ۳: ترکیبی
    btn_hybrid = wx.Button(panel, label="🔗 روش ترکیبی")
    btn_hybrid.SetBackgroundColour(wx.Colour(153, 50, 204))
    btn_hybrid.SetForegroundColour(wx.WHITE)
    btn_hybrid.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
    btn_hybrid.SetToolTip("ابتدا نام مشابه، سپس بررسی هش")
    vbox.Add(btn_hybrid, 0, wx.ALL | wx.EXPAND, 10)

    vbox.AddSpacer(20)

    # دکمه انصراف
    btn_cancel = wx.Button(panel, label="انصراف")
    vbox.Add(btn_cancel, 0, wx.ALL | wx.CENTER, 10)

    panel.SetSizer(vbox)
    dlg.Center()

    # تنظیم نتیجه
    result = {"method": None}

    def on_hash_method(event):
        result["method"] = "hash"
        dlg.EndModal(wx.ID_OK)

    def on_name_method(event):
        result["method"] = "name"
        dlg.EndModal(wx.ID_OK)

    def on_hybrid_method(event):
        result["method"] = "hybrid"
        dlg.EndModal(wx.ID_OK)

    def on_cancel(event):
        dlg.EndModal(wx.ID_CANCEL)

    btn_hash.Bind(wx.EVT_BUTTON, on_hash_method)
    btn_name.Bind(wx.EVT_BUTTON, on_name_method)
    btn_hybrid.Bind(wx.EVT_BUTTON, on_hybrid_method)
    btn_cancel.Bind(wx.EVT_BUTTON, on_cancel)

    return result["method"] if dlg.ShowModal() == wx.ID_OK else None


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """مدیریت خطاهای unhandled"""

    logger = log_manager.get_logger("unhandled")

    logger.critical("خطای unhandled",
                    exc_info=(exc_type, exc_value, exc_traceback))

def main():

    try:
        logger.info("برنامه در حال راه‌اندازی...")
        app = wx.App(False)


        # نمایش دیالوگ انتخاب پوشه
        dialog = wx.DirDialog(None, "لطفاً یک پوشه را انتخاب کنید",
                              style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dialog.ShowModal() != wx.ID_OK:
            logger.warning("هیچ پوشه‌ای انتخاب نشد")
            wx.MessageBox("هیچ پوشه‌ای انتخاب نشد. برنامه بسته می‌شود.",
                          "توجه", wx.OK | wx.ICON_INFORMATION)
            dialog.Destroy()
            return

        folder_selected = dialog.GetPath()
        dialog.Destroy()
        logger.info(f"پوشه انتخاب شد: {folder_selected}")

        if not os.path.exists(folder_selected):
            wx.MessageBox(f"پوشه انتخاب شده وجود ندارد:\n{folder_selected}",
                          "خطا", wx.OK | wx.ICON_ERROR)
            return

        # نمایش منوی انتخاب روش
        method = show_method_selection_dialog(None, folder_selected)
        if method is None:
            logger.info("عملیات توسط کاربر لغو شد.")
            return

        logger.info(f"روش انتخاب شده: {method}")

        # تغییر دسترسی‌ها
        change_folder_permissions(folder_selected)

        # ایجاد پوشه‌های لازم
        [keep_folder, priority_folder, corrupted_folder] = making_folders(folder_selected)

        # بررسی فایل‌های خراب (در صورت فعال بودن)
        if finding_corrupted_files and os.path.exists(FFMPEG_PATH):
            move_corrupted_files(folder_selected, FFMPEG_PATH, corrupted_folder)
            remove_duplicates_from_corrupted_folder_and_otherwhere(folder_selected)

        if method == "hash":
            # روش هش کردن
            handler = FileHandler(folder_selected, priority_folder, keep_folder)
            frame = FileFinderFrame(None, "Duplicates Cleaner - روش دقیق", folder_selected, handler)
            frame.Show()
            app.MainLoop()

            # پیشنهاد روش بعدی
            dlg = wx.MessageDialog(None,
                                   "آیا می‌خواهید فایل‌های با نام‌های مشابه را نیز بررسی کنید؟",
                                   "بررسی اضافی",
                                   wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT)

            if dlg.ShowModal() == wx.ID_YES:
                settings_dlg = SimilarFilesSettingsDialog(None)
                if settings_dlg.ShowModal() == wx.ID_OK:
                    settings = settings_dlg.get_settings()
                    similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                    similar_frame.Show()
                    wx.Yield()  # آپدیت UI

            dlg.Destroy()

        elif method == "name":
            # روش نام مشابه
            settings_dlg = SimilarFilesSettingsDialog(None)
            if settings_dlg.ShowModal() == wx.ID_OK:
                settings = settings_dlg.get_settings()
                similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                similar_frame.Show()
                app.MainLoop()

        elif method == "hybrid":
            # روش ترکیبی - ابتدا نام مشابه، سپس هش
            settings_dlg = SimilarFilesSettingsDialog(None)
            if settings_dlg.ShowModal() == wx.ID_OK:
                settings = settings_dlg.get_settings()

                # مرحله اول: نام مشابه
                similar_frame = SimilarFilesFrame(None, folder_selected, settings)
                similar_frame.Show()

                # صبر تا بسته شدن پنجره
                while similar_frame.IsShown():
                    wx.Yield()
                    wx.MilliSleep(100)

                # مرحله دوم: هش کردن
                reply = wx.MessageBox("آیا می‌خواهید بررسی دقیق (هش) را نیز انجام دهید؟",
                                      "مرحله بعدی",
                                      wx.YES_NO | wx.ICON_QUESTION)

                if reply == wx.YES:
                    handler = FileHandler(folder_selected, priority_folder, keep_folder)
                    frame = FileFinderFrame(None, "Duplicates Cleaner - روش دقیق",
                                            folder_selected, handler)
                    frame.Show()
                    app.MainLoop()

        # حذف پوشه‌های خالی
        try:
            delete_empty_folders(folder_selected)
        except Exception as e:
            logger.error(f"خطا در حذف پوشه‌های خالی: {e}")

        logger.info("برنامه با موفقیت به پایان رسید")

    except Exception as e:
        logger.exception(f"خطای غیرمنتظره در main: {str(e)}")
        wx.MessageBox(f"خطای شدید در اجرای برنامه:\n{str(e)}",
                      "خطا", wx.OK | wx.ICON_ERROR)
        traceback.print_exc()
    finally:
        log_manager.log_shutdown()



if __name__ == "__main__":
    main()