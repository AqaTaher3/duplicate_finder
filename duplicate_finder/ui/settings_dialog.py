from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, ttk
from duplicate_finder.services import AppConfig

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, config: AppConfig):
        super().__init__(parent)
        self.config_obj = config
        self.title("تنظیمات")
        self.geometry("560x430")
        self.transient(parent); self.grab_set(); self.resizable(False, False)
        frame = ttk.Frame(self, padding=18); frame.pack(fill="both", expand=True)
        self.workers = tk.IntVar(value=config.workers)
        self.minimum = tk.DoubleVar(value=config.min_size_bytes / 1024 / 1024)
        self.algorithm = tk.StringVar(value=config.hash_algorithm)
        self.hidden = tk.BooleanVar(value=config.include_hidden)
        self.extensions = tk.StringVar(value=", ".join(config.excluded_extensions))
        self.threshold = tk.DoubleVar(value=config.similar_name_threshold)
        controls = [
            ("تعداد پردازش هم‌زمان", ttk.Spinbox(frame, from_=1, to=64, textvariable=self.workers)),
            ("حداقل حجم فایل (MB)", ttk.Entry(frame, textvariable=self.minimum)),
            ("الگوریتم هش", ttk.Combobox(frame, textvariable=self.algorithm, values=("sha256", "blake2b", "md5"), state="readonly")),
            ("پسوندهای مستثنا", ttk.Entry(frame, textvariable=self.extensions)),
            ("آستانه شباهت نام", ttk.Entry(frame, textvariable=self.threshold)),
        ]
        for row, (label, widget) in enumerate(controls):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=9)
            widget.grid(row=row, column=1, sticky="ew", pady=9)
        ttk.Checkbutton(frame, text="شامل فایل‌های مخفی", variable=self.hidden).grid(row=6, column=0, columnspan=2, sticky="w")
        frame.columnconfigure(1, weight=1)
        buttons = ttk.Frame(frame); buttons.grid(row=9, column=0, columnspan=2, sticky="e", pady=24)
        ttk.Button(buttons, text="انصراف", command=self.destroy).pack(side="left")
        ttk.Button(buttons, text="ذخیره", command=self.save).pack(side="left", padx=8)

    def save(self):
        try:
            self.config_obj.workers = max(1, int(self.workers.get()))
            self.config_obj.min_size_bytes = max(0, int(float(self.minimum.get()) * 1024 * 1024))
            self.config_obj.hash_algorithm = self.algorithm.get()
            self.config_obj.include_hidden = self.hidden.get()
            self.config_obj.excluded_extensions = [x.strip() for x in self.extensions.get().split(",") if x.strip()]
            self.config_obj.similar_name_threshold = min(1.0, max(0.0, float(self.threshold.get())))
            self.config_obj.save(); self.destroy()
        except Exception as exc:
            messagebox.showerror("تنظیمات", str(exc), parent=self)
