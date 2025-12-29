# اصلاحات:
# 1. اضافه کردن import sys
# 2. تصحیح مسیر فایل‌ها
# 3. مدیریت بهتر exceptionها

import wx
import os
import subprocess
import sys
import traceback


def launch_with_method(method="hash"):
    """اجرای برنامه با روش مشخص"""
    try:
        if method == "hash":
            subprocess.run([sys.executable, "main.py"], check=True)
        elif method == "name":
            subprocess.run([sys.executable, "quick_mode.py"], check=True)
    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"خطا در اجرای برنامه: {str(e)}", "خطا", wx.OK | wx.ICON_ERROR)
    except FileNotFoundError:
        wx.MessageBox("فایل اصلی برنامه یافت نشد!", "خطا", wx.OK | wx.ICON_ERROR)
    except Exception as e:
        wx.MessageBox(f"خطای غیرمنتظره: {str(e)}", "خطا", wx.OK | wx.ICON_ERROR)


class MethodSelector(wx.Frame):
    def __init__(self):
        super().__init__(None, title="انتخاب روش بررسی", size=(450, 350))

        # اضافه کردن icon
        try:
            if os.path.exists("icon.ico"):
                self.SetIcon(wx.Icon("icon.ico", wx.BITMAP_TYPE_ICO))
        except:
            pass

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        vbox = wx.BoxSizer(wx.VERTICAL)

        # عنوان با فونت بهتر
        title = wx.StaticText(panel, label="Duplicates Cleaner")
        title.SetForegroundColour(wx.Colour(230, 210, 181))
        title_font = wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, 0, wx.ALL | wx.CENTER, 20)

        # اضافه کردن توضیح
        explanation = wx.StaticText(panel,
                                    label="برنامه برای یافتن و حذف فایل‌های تکراری\nاز روش‌های مختلف استفاده می‌کند")
        explanation.SetForegroundColour(wx.Colour(200, 200, 200))
        explanation.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        vbox.Add(explanation, 0, wx.ALL | wx.CENTER, 10)

        subtitle = wx.StaticText(panel, label="روش بررسی فایل‌های تکراری")
        subtitle.SetForegroundColour(wx.Colour(200, 200, 200))
        subtitle.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(subtitle, 0, wx.ALL | wx.CENTER, 10)

        # دکمه روش هش با tooltip
        btn_hash = wx.Button(panel, label="🔍 روش دقیق (هش)")
        btn_hash.SetBackgroundColour(wx.Colour(60, 179, 113))
        btn_hash.SetForegroundColour(wx.WHITE)
        btn_hash.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        btn_hash.SetToolTip("بررسی 100% دقیق بر اساس محتوای فایل\nمناسب برای فایل‌های مهم و حیاتی")
        vbox.Add(btn_hash, 0, wx.ALL | wx.EXPAND, 10)

        # دکمه روش نام مشابه
        btn_name = wx.Button(panel, label="⚡ روش سریع (نام مشابه)")
        btn_name.SetBackgroundColour(wx.Colour(70, 130, 180))
        btn_name.SetForegroundColour(wx.WHITE)
        btn_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        btn_name.SetToolTip("بررسی بر اساس شباهت نام فایل‌ها\nسریع و مناسب برای فایل‌های رسانه")
        vbox.Add(btn_name, 0, wx.ALL | wx.EXPAND, 10)

        # اضافه کردن فاصله
        vbox.AddSpacer(20)

        # دکمه خروج
        btn_exit = wx.Button(panel, label="خروج", size=(100, 35))
        btn_exit.SetBackgroundColour(wx.Colour(220, 53, 69))
        btn_exit.SetForegroundColour(wx.WHITE)
        vbox.Add(btn_exit, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(vbox)

        # رویدادها
        btn_hash.Bind(wx.EVT_BUTTON, lambda e: self.on_method_selected("hash"))
        btn_name.Bind(wx.EVT_BUTTON, lambda e: self.on_method_selected("name"))
        btn_exit.Bind(wx.EVT_BUTTON, lambda e: self.Close())

        # رویداد بستن پنجره
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Center()
        self.Show()

    def on_method_selected(self, method):
        """وقتی روشی انتخاب شد"""
        self.Close()
        launch_with_method(method)

    def on_close(self, event):
        """مدیریت بستن پنجره"""
        event.Skip()


if __name__ == "__main__":
    try:
        app = wx.App(False)
        frame = MethodSelector()
        app.MainLoop()
    except Exception as e:
        print(f"خطای شدید در اجرای برنامه: {str(e)}")
        traceback.print_exc()
        input("برای خروج Enter بزنید...")