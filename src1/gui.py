import wx
from src1.logic import FileHandler
import os



class FileFinderFrame(wx.Frame):
    def __init__(self, parent, title, folder_path, file_handler):
        super().__init__(parent, title=title, size=(800, 600))  # اندازه پنجره کوچکتر شده
        self.folder_path = folder_path
        self.file_handler = file_handler
        self.files_list = []
        self.selected_files = []

        self.init_ui()
        self.load_files()

    def init_ui(self):
        self.SetBackgroundColour(wx.Colour(43, 58, 68))
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(43, 69, 60))

        # Main sizer
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        # اضافه کردن المان‌های جدید برای نمایش اطلاعات اسکن
        self.scan_info_panel = wx.Panel(self.panel)
        self.scan_info_panel.SetBackgroundColour(wx.Colour(60, 60, 60))

        self.scan_info_sizer = wx.BoxSizer(wx.VERTICAL)

        self.total_files_label = wx.StaticText(self.scan_info_panel, label="Total files to scan: 0")
        self.files_scanned_label = wx.StaticText(self.scan_info_panel, label="Files scanned: 0")
        self.scan_speed_label = wx.StaticText(self.scan_info_panel, label="Scan speed: 0 file/s")

        for label in [self.total_files_label, self.files_scanned_label, self.scan_speed_label]:
            label.SetForegroundColour(wx.Colour(230, 210, 181))
            self.scan_info_sizer.Add(label, 0, wx.ALL, 5)

        self.scan_info_panel.SetSizer(self.scan_info_sizer)
        self.main_sizer.Add(self.scan_info_panel, 0, wx.EXPAND | wx.ALL, 10)

        # Progress section
        self.progress_bar = wx.Gauge(self.panel, range=100, size=(-1, 20))
        self.progress_label = wx.StaticText(self.panel, label="Progress: 0%")
        self.progress_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.main_sizer.Add(self.progress_label, 0, wx.ALL | wx.CENTER, 5)
        self.main_sizer.Add(self.progress_bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Single console for both logs and file display
        self.console = wx.TextCtrl(self.panel,
                                   style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                                   size=(-1, 400))
        self.console.SetBackgroundColour(wx.Colour(60, 60, 60))  # رنگ طوسی تیره
        self.console.SetForegroundColour(wx.Colour(230, 210, 181))
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.console.SetFont(font)
        self.main_sizer.Add(self.console, 1, wx.EXPAND | wx.ALL, 10)

        # Delete button
        self.btn_delete = wx.Button(self.panel, label="Delete Selected")
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete_selected)
        self.main_sizer.Add(self.btn_delete, 0, wx.ALL | wx.CENTER, 10)

        # Status label
        self.status_label = wx.StaticText(self.panel, label="Status: Ready")
        self.status_label.SetForegroundColour(wx.Colour(230, 210, 181))
        self.main_sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        self.panel.SetSizer(self.main_sizer)

    def load_files(self):
        """Load files and update display"""
        self.log("Loading files...")
        self.log(f"Scanning folder: {self.folder_path}")
        self.files_list = self.file_handler.load_files() or []

        if not self.files_list:
            self.log("\nNo duplicate files found.")
            self.status_label.SetLabel("Status: No duplicates found")
        else:
            self.show_files()
            self.status_label.SetLabel(f"Status: Found {len(self.files_list)} duplicates")

    def show_files(self):
        """Display files in the console"""
        self.console.AppendText("\n\nDuplicate files:\n")
        self.console.AppendText("-" * 50 + "\n")

        for i, file_group in enumerate(self.files_list, 1):
            self.console.AppendText(f"Group {i}:\n")
            for file in file_group:
                self.console.AppendText(f"• {os.path.basename(file)}\n")
            self.console.AppendText("\n")

    def log(self, message):
        """Add message to console"""
        self.console.AppendText(f"{message}\n")

    def on_delete_selected(self, event):
        """Handle file deletion"""
        self.log("\nDeletion not implemented yet")

    def update_scan_info(self, data):
        """تابع به‌روزرسانی رابط کاربری با فرمت صحیح"""
        # تنظیم فونت فارسی
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL, False, 'B Nazanin')

        # به‌روزرسانی برچسب‌ها با ترتیب صحیح
        self.total_files_label.SetLabel(f"تعداد کل فایل‌ها: {data['total_files']}")
        self.scanned_files_label.SetLabel(f"فایل‌های اسکن شده: {data['scanned_files']}")
        self.speed_label.SetLabel(f"سرعت اسکن: {data['speed']:.1f} فایل/ثانیه")

        # تنظیم پیشرفت
        progress_value = int(data['percentage'])
        self.progress_bar.SetValue(progress_value)
        self.progress_label.SetLabel(f"{progress_value}%")

        # اعمال فونت به همه برچسب‌ها
        for label in [self.total_files_label, self.scanned_files_label,
                      self.speed_label, self.progress_label]:
            label.SetFont(font)
            label.SetForegroundColour(wx.Colour(230, 210, 181))