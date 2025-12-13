# file: launcher.py (اختیاری)
import wx
import os
import subprocess
import sys


def launch_with_method(method="hash"):
    """اجرای برنامه با روش مشخص"""
    if method == "hash":
        # اجرای main.py (روش هش)
        subprocess.run([sys.executable, "main.py"])
    elif method == "name":
        # اجرای مستقیماً روش نام مشابه
        subprocess.run([sys.executable, "quick_mode.py"])


class MethodSelector(wx.Frame):
    def __init__(self):
        super().__init__(None, title="انتخاب روش بررسی", size=(400, 300))

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Duplicates Cleaner")
        title.SetForegroundColour(wx.Colour(230, 210, 181))
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        vbox.Add(title, 0, wx.ALL | wx.CENTER, 20)

        subtitle = wx.StaticText(panel, label="روش بررسی فایل‌های تکراری")
        subtitle.SetForegroundColour(wx.Colour(200, 200, 200))
        vbox.Add(subtitle, 0, wx.ALL | wx.CENTER, 10)

        # دکمه روش هش
        btn_hash = wx.Button(panel, label="🔍 روش دقیق (هش)")
        btn_hash.SetBackgroundColour(wx.Colour(60, 179, 113))
        btn_hash.SetForegroundColour(wx.WHITE)
        btn_hash.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        vbox.Add(btn_hash, 0, wx.ALL | wx.EXPAND, 10)

        # دکمه روش نام مشابه
        btn_name = wx.Button(panel, label="⚡ روش سریع (نام مشابه)")
        btn_name.SetBackgroundColour(wx.Colour(70, 130, 180))
        btn_name.SetForegroundColour(wx.WHITE)
        btn_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        vbox.Add(btn_name, 0, wx.ALL | wx.EXPAND, 10)

        # دکمه خروج
        btn_exit = wx.Button(panel, label="خروج")
        vbox.Add(btn_exit, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(vbox)

        # رویدادها
        btn_hash.Bind(wx.EVT_BUTTON, lambda e: self.on_method_selected("hash"))
        btn_name.Bind(wx.EVT_BUTTON, lambda e: self.on_method_selected("name"))
        btn_exit.Bind(wx.EVT_BUTTON, lambda e: self.Close())

        self.Show()

    def on_method_selected(self, method):
        """وقتی روشی انتخاب شد"""
        self.Close()
        launch_with_method(method)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MethodSelector()
    app.MainLoop()