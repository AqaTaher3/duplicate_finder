# config_dialog.py
import wx
from config import config


class ConfigDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="تنظیمات برنامه", size=(600, 500))

        self.config = config
        self.SetBackgroundColour(wx.Colour(43, 58, 68))

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        vbox = wx.BoxSizer(wx.VERTICAL)

        # تب‌ها
        notebook = wx.Notebook(panel)

        # تب عمومی
        general_panel = wx.Panel(notebook)
        self.setup_general_tab(general_panel)
        notebook.AddPage(general_panel, "عمومی")

        # تب عملکرد
        performance_panel = wx.Panel(notebook)
        self.setup_performance_tab(performance_panel)
        notebook.AddPage(performance_panel, "عملکرد")

        # تب فیلترها
        filter_panel = wx.Panel(notebook)
        self.setup_filter_tab(filter_panel)
        notebook.AddPage(filter_panel, "فیلترها")

        vbox.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)

        # دکمه‌ها
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        btn_save = wx.Button(panel, label="ذخیره")
        btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.Add(btn_save, 0, wx.ALL, 5)

        btn_cancel = wx.Button(panel, label="انصراف")
        btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        button_sizer.Add(btn_cancel, 0, wx.ALL, 5)

        btn_defaults = wx.Button(panel, label="پیش‌فرض")
        btn_defaults.Bind(wx.EVT_BUTTON, self.on_defaults)
        button_sizer.Add(btn_defaults, 0, wx.ALL, 5)

        vbox.Add(button_sizer, 0, wx.CENTER | wx.BOTTOM, 10)

        panel.SetSizer(vbox)

    def setup_general_tab(self, panel):
        # ویجت‌های تنظیمات عمومی
        pass

    def setup_performance_tab(self, panel):
        # ویجت‌های تنظیمات عملکرد
        pass

    def setup_filter_tab(self, panel):
        # ویجت‌های تنظیمات فیلتر
        pass

    def on_save(self, event):
        # ذخیره تنظیمات
        self.config.save()
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_defaults(self, event):
        # بازنشانی به پیش‌فرض
        dlg = wx.MessageDialog(self,
                               "آیا می‌خواهید تنظیمات به حالت پیش‌فرض بازنشانی شود؟",
                               "تأیید",
                               wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            self.config.reset_to_defaults()
        dlg.Destroy()