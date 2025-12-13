import wx


class SimilarFilesSettingsDialog(wx.Dialog):
    def __init__(self, parent, title="تنظیمات جستجوی فایل‌های مشابه"):
        super().__init__(parent, title=title, size=(500, 300))

        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        vbox = wx.BoxSizer(wx.VERTICAL)

        # عنوان
        title_label = wx.StaticText(panel, label="جستجوی فایل‌های با نام‌های مشابه")
        title_label.SetForegroundColour(wx.Colour(230, 210, 181))
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title_label.SetFont(title_font)
        vbox.Add(title_label, 0, wx.ALL | wx.CENTER, 10)

        # توضیح
        desc_label = wx.StaticText(panel, label="فایل‌هایی که نام‌های شبیه به هم دارند را پیدا می‌کند")
        desc_label.SetForegroundColour(wx.Colour(200, 200, 200))
        vbox.Add(desc_label, 0, wx.ALL | wx.CENTER, 5)

        # تنظیم حداقل شباهت
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        similarity_label = wx.StaticText(panel, label="حداقل شباهت نام (%):")
        similarity_label.SetForegroundColour(wx.Colour(230, 210, 181))
        hbox1.Add(similarity_label, 0, wx.ALL | wx.CENTER, 10)

        self.similarity_slider = wx.Slider(panel, value=70, minValue=30, maxValue=95,
                                           style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        hbox1.Add(self.similarity_slider, 1, wx.ALL | wx.EXPAND, 10)
        vbox.Add(hbox1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # تنظیم حداقل طول نام
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        length_label = wx.StaticText(panel, label="حداقل طول نام برای بررسی:")
        length_label.SetForegroundColour(wx.Colour(230, 210, 181))
        hbox2.Add(length_label, 0, wx.ALL | wx.CENTER, 10)

        self.length_spin = wx.SpinCtrl(panel, value='10', min=3, max=50)
        hbox2.Add(self.length_spin, 0, wx.ALL | wx.CENTER, 10)
        vbox.Add(hbox2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # تنظیم پسوند
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        ext_label = wx.StaticText(panel, label="فقط فایل‌های با پسوند مشابه:")
        ext_label.SetForegroundColour(wx.Colour(230, 210, 181))
        hbox3.Add(ext_label, 0, wx.ALL | wx.CENTER, 10)

        self.ext_checkbox = wx.CheckBox(panel)
        self.ext_checkbox.SetValue(True)
        hbox3.Add(self.ext_checkbox, 0, wx.ALL | wx.CENTER, 10)
        vbox.Add(hbox3, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # دکمه‌ها
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_ok = wx.Button(panel, label="شروع جستجو", size=(120, 40))
        self.btn_ok.SetBackgroundColour(wx.Colour(60, 179, 113))
        self.btn_ok.SetForegroundColour(wx.WHITE)
        button_sizer.Add(self.btn_ok, 0, wx.ALL | wx.CENTER, 10)

        self.btn_cancel = wx.Button(panel, label="انصراف", size=(100, 40))
        button_sizer.Add(self.btn_cancel, 0, wx.ALL | wx.CENTER, 10)

        vbox.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(vbox)

        # رویدادها
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)

    def get_settings(self):
        """دریافت تنظیمات انتخابی"""
        return {
            'min_similarity': self.similarity_slider.GetValue() / 100.0,
            'min_length': self.length_spin.GetValue(),
            'same_extension_only': self.ext_checkbox.GetValue()
        }