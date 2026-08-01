from __future__ import annotations
import os, queue, subprocess, sys, threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from duplicate_finder.core import (Cancelled, DuplicateScanner, PriorityResolver,
                                   delete_empty_folders, move_to_backup, restore_moves)
from duplicate_finder.models import DuplicateGroup, ScanResult
from duplicate_finder.services import AppConfig
from .settings_dialog import SettingsDialog

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = AppConfig.load()
        self.title("Duplicate Finder — Modular")
        self.geometry(self.cfg.window_geometry)
        self.minsize(900, 600)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.events: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.row_paths: dict[str, str] = {}
        self.last_moves: list[tuple[str, str]] = []
        self.result: ScanResult | None = None
        self.last_scan_roots: list[str] = []
        self._build(); self.after(100, self._poll)

    def _build(self):
        outer = ttk.Frame(self, padding=10); outer.pack(fill="both", expand=True)
        top = ttk.LabelFrame(outer, text="پوشه‌های اسکن", padding=8); top.pack(fill="x")
        self.folder_list = tk.Listbox(top, height=4, selectmode="extended")
        self.folder_list.pack(side="left", fill="x", expand=True)
        for p in self.cfg.scan_folders: self.folder_list.insert("end", p)
        buttons = ttk.Frame(top); buttons.pack(side="left", padx=8)
        ttk.Button(buttons, text="افزودن", command=self.add_folder).pack(fill="x", pady=2)
        ttk.Button(buttons, text="حذف", command=self.remove_folder).pack(fill="x", pady=2)
        ttk.Button(buttons, text="پاک‌کردن", command=lambda: self.folder_list.delete(0, "end")).pack(fill="x", pady=2)

        special = ttk.LabelFrame(outer, text="پوشه‌های ویژه", padding=8); special.pack(fill="x", pady=8)
        self.keep_var = tk.StringVar(value=self.cfg.keep_folder)
        priority_value = (
            self.cfg.priority_folders[0]
            if self.cfg.priority_folders
            else ""
        )
        self.priority_var = tk.StringVar(value=priority_value)

        self._folder_row(special, 0, "Keep (محافظت مطلق)", self.keep_var)
        self._folder_row(special, 1, "PriorityFolder", self.priority_var)

        commands = ttk.Frame(outer); commands.pack(fill="x", pady=(0, 8))
        self.scan_btn = ttk.Button(commands, text="شروع اسکن", command=self.start_scan); self.scan_btn.pack(side="left")
        self.cancel_btn = ttk.Button(commands, text="توقف", state="disabled", command=self.cancel_scan); self.cancel_btn.pack(side="left", padx=5)
        ttk.Button(commands, text="انتخاب پیشنهادی", command=self.select_suggested).pack(side="left", padx=5)
        ttk.Button(commands, text="انتقال به پشتیبان", command=self.remove_selected).pack(side="left", padx=5)
        self.undo_btn = ttk.Button(commands, text="بازگردانی آخرین عملیات", command=self.undo, state="disabled"); self.undo_btn.pack(side="left", padx=5)
        ttk.Button(commands, text="تنظیمات", command=lambda: SettingsDialog(self, self.cfg)).pack(side="right")
        self.similar_var = tk.BooleanVar(value=self.cfg.detect_similar_names)
        ttk.Checkbutton(commands, text="نام‌های مشابه", variable=self.similar_var).pack(side="right", padx=8)

        self.progress = ttk.Progressbar(outer, maximum=100); self.progress.pack(fill="x")
        self.status = tk.StringVar(value="آماده")
        ttk.Label(outer, textvariable=self.status).pack(anchor="w", pady=4)
        notebook = ttk.Notebook(outer); notebook.pack(fill="both", expand=True)
        exact_tab = ttk.Frame(notebook); similar_tab = ttk.Frame(notebook); log_tab = ttk.Frame(notebook)
        notebook.add(exact_tab, text="تکراری دقیق"); notebook.add(similar_tab, text="نام مشابه"); notebook.add(log_tab, text="گزارش")
        self.exact_tree = self._tree(exact_tab); self.similar_tree = self._tree(similar_tab)
        self.log = tk.Text(log_tab, wrap="word", state="disabled"); self.log.pack(fill="both", expand=True)
        bottom = ttk.Frame(outer); bottom.pack(fill="x", pady=(8, 0))
        ttk.Button(bottom, text="بازکردن فایل", command=self.open_selected).pack(side="left")
        ttk.Button(bottom, text="بازکردن پوشه", command=self.open_parent).pack(side="left", padx=5)
        ttk.Button(bottom, text="حذف پوشه‌های خالی", command=self.remove_empty).pack(side="right")

    def _folder_row(self, parent, row, label, variable):
        ttk.Label(parent, text=label, width=22).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(parent, text="انتخاب", command=lambda v=variable: self.pick_special(v)).grid(row=row, column=2, padx=4)
        ttk.Button(parent, text="×", width=3, command=lambda v=variable: v.set("")).grid(row=row, column=3)
        parent.columnconfigure(1, weight=1)

    def _tree(self, parent):
        cols = ("status", "name", "size", "priority", "path")
        tree = ttk.Treeview(parent, columns=cols, show="tree headings", selectmode="extended")
        tree.heading("#0", text="گروه"); widths = (145, 220, 100, 80, 600)
        labels = ("وضعیت", "نام", "حجم", "اولویت", "مسیر")
        for col, label, width in zip(cols, labels, widths): tree.heading(col, text=label); tree.column(col, width=width, anchor="w")
        tree.column("#0", width=70); tree.pack(fill="both", expand=True)
        tree.bind("<Double-1>", lambda _e: self.open_selected())
        return tree

    def add_folder(self):
        p = filedialog.askdirectory(parent=self)
        if p and p not in self.folder_list.get(0, "end"): self.folder_list.insert("end", p)
    def remove_folder(self):
        for i in reversed(self.folder_list.curselection()): self.folder_list.delete(i)
    def pick_special(self, variable):
        p = filedialog.askdirectory(parent=self)
        if p: variable.set(p)

    def start_scan(self):
        roots = list(self.folder_list.get(0, "end"))
        if not roots:
            return messagebox.showwarning(
                "پوشه",
                "حداقل یک پوشه برای اسکن انتخاب کن.",
            )

        self.last_scan_roots = roots.copy()
        self.cancel_event.clear()
        self.scan_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress["value"] = 0; self._clear(); self.status.set("شروع اسکن...")
        threading.Thread(target=self._scan_worker, args=(roots,), daemon=True).start()

    def _scan_worker(self, roots):
        try:
            scanner = DuplicateScanner(roots, keep_folder=self.keep_var.get(), priority_folders=[self.priority_var.get()],
                excluded_folders=self.cfg.excluded_folders, excluded_extensions=self.cfg.excluded_extensions,
                min_size=self.cfg.min_size_bytes, workers=self.cfg.workers, algorithm=self.cfg.hash_algorithm,
                include_hidden=self.cfg.include_hidden, progress=lambda p,m: self.events.put(("progress",p,m)), cancel_event=self.cancel_event)
            result = scanner.scan(self.similar_var.get(), self.cfg.similar_name_threshold)
            self.events.put(("done", result))
        except Cancelled: self.events.put(("cancelled",))
        except Exception as exc: self.events.put(("error", str(exc)))

    def cancel_scan(self): self.cancel_event.set(); self.status.set("در حال توقف امن...")
    def _poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress": self.progress["value"] = event[1]; self.status.set(event[2])
                elif event[0] == "done": self._show(event[1]); self._idle()
                elif event[0] == "cancelled": self.status.set("اسکن متوقف شد"); self._idle()
                elif event[0] == "error": messagebox.showerror("خطا", event[1]); self._idle()
        except queue.Empty: pass
        self.after(100, self._poll)
    def _idle(self): self.scan_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
    def _clear(self):
        self.row_paths.clear()
        for tree in (self.exact_tree, self.similar_tree):
            for item in tree.get_children(): tree.delete(item)
        self.log.config(state="normal"); self.log.delete("1.0", "end"); self.log.config(state="disabled")

    def _show(self, result: ScanResult):
        self.result = result; self._fill(self.exact_tree, result.duplicate_groups); self._fill(self.similar_tree, result.similar_groups)
        reclaim = sum(sum(x.size for x in g.suggested_removals) for g in result.duplicate_groups)
        self.status.set(f"{len(result.duplicate_groups):,} گروه دقیق | {len(result.similar_groups):,} مشابه | قابل آزادسازی: {self.fmt_size(reclaim)}")
        self._log(f"فایل‌ها: {result.scanned_files:,}\nکاندیدها: {result.candidate_files:,}\nکش: {result.cache_hits:,}\nزمان: {result.elapsed_seconds:.2f} ثانیه\nخطاها: {len(result.errors):,}")
        if result.errors: self._log("\n".join(result.errors[:500]))

    def _fill(self, tree, groups: list[DuplicateGroup]):
        for index, group in enumerate(groups, 1):
            parent = tree.insert("", "end", text=f"#{index}", values=("", f"{len(group.files)} فایل", self.fmt_size(group.files[0].size), "", ""))
            keeper = group.keeper.path
            protected_paths = {f.path for f in group.files if f.protected}
            for info in group.files:
                if info.protected: status, tag, pr = "Keep — محافظت‌شده", "keep", "Keep"
                elif protected_paths: status, tag, pr = "تکراری", "duplicate", info.priority + 1 if info.priority < 999 else "-"
                elif info.path == keeper: status, tag, pr = "نگه‌دار", "keep", info.priority + 1 if info.priority < 999 else "-"
                else: status, tag, pr = ("تکراری" if group.exact else "بررسی"), "duplicate", info.priority + 1 if info.priority < 999 else "-"
                iid = tree.insert(parent, "end", values=(status, Path(info.path).name, self.fmt_size(info.size), pr, info.path), tags=(tag,))
                self.row_paths[iid] = info.path
            tree.item(parent, open=True)
        tree.tag_configure("keep", background="#e9f7ec"); tree.tag_configure("duplicate", background="#fff0f0")

    def _active_tree(self):
        return self.similar_tree if self.focus_get() is self.similar_tree else self.exact_tree
    def selected_paths(self):
        tree = self._active_tree(); return [self.row_paths[i] for i in tree.selection() if i in self.row_paths]
    def select_suggested(self):
        if not self.result: return
        paths = {f.path for group in self.result.duplicate_groups for f in group.suggested_removals}
        ids = [iid for iid, p in self.row_paths.items() if p in paths and self.exact_tree.exists(iid)]
        self.exact_tree.selection_set(ids)
        if ids: self.exact_tree.focus(ids[0]); self.exact_tree.see(ids[0])

    def remove_selected(self):
        paths = self.selected_paths()
        if not paths:
            return messagebox.showinfo(
                "انتخاب",
                "فایلی انتخاب نشده است.",
            )

        resolver = PriorityResolver(
            self.keep_var.get(),
            [self.priority_var.get()],
        )

        protected = [path for path in paths if resolver.is_protected(path)]
        if protected:
            return messagebox.showwarning(
                "Keep",
                "فایل‌های داخل Keep محافظت شده‌اند و منتقل نمی‌شوند.",
            )

        # ابتدا از پوشه‌های فعلی UI استفاده می‌کنیم. اگر کاربر بعد از اسکن
        # لیست را پاک کرده باشد، مسیرهای آخرین اسکن استفاده می‌شوند.
        roots = list(self.folder_list.get(0, "end")) or self.last_scan_roots

        if not roots:
            return messagebox.showwarning(
                "پوشه مقصد",
                "هیچ پوشه اصلی برای ساخت backup_deleted مشخص نیست.\n"
                "ابتدا حداقل یک پوشه اسکن اضافه کن و دوباره اسکن را اجرا کن.",
            )

        backup_root = roots[0]
        if not Path(backup_root).is_dir():
            return messagebox.showerror(
                "پوشه نامعتبر",
                f"پوشه اصلی وجود ندارد یا قابل دسترسی نیست:\n{backup_root}",
            )

        if not messagebox.askyesno(
            "تأیید",
            f"{len(paths)} فایل به پوشه پشتیبان منتقل شود؟\n\n"
            f"پوشه پشتیبان داخل این مسیر ساخته می‌شود:\n{backup_root}",
        ):
            return

        moved, errors = move_to_backup(
            paths,
            backup_root,
            self.cfg.backup_folder_name,
            resolver,
        )
        self.last_moves = moved; self.undo_btn.config(state="normal" if moved else "disabled")
        messagebox.showinfo("نتیجه", f"{len(moved)} فایل منتقل شد.\nخطا: {len(errors)}")
        if errors: self._log("\n".join(errors))
        for iid, path in list(self.row_paths.items()):
            if any(path == original for original, _ in moved):
                for tree in (self.exact_tree, self.similar_tree):
                    if tree.exists(iid): tree.delete(iid)
                self.row_paths.pop(iid, None)

    def undo(self):
        if not self.last_moves: return
        restored, errors = restore_moves(self.last_moves)
        self.last_moves = []; self.undo_btn.config(state="disabled")
        messagebox.showinfo("بازگردانی", f"{restored} فایل بازگردانده شد.\nخطا: {len(errors)}")
    def remove_empty(self):
        roots = list(self.folder_list.get(0, "end")) or self.last_scan_roots
        if not roots:
            return messagebox.showwarning(
                "پوشه",
                "هیچ پوشه‌ای برای بررسی انتخاب نشده است.",
            )

        n = delete_empty_folders(
            roots,
            self.cfg.backup_folder_name,
        )
        messagebox.showinfo(
            "پوشه‌های خالی",
            f"{n} پوشه خالی حذف شد.",
        )

    def open_selected(self):
        paths = self.selected_paths()
        if paths: self._open(paths[0])
    def open_parent(self):
        paths = self.selected_paths()
        if paths: self._open(str(Path(paths[0]).parent))
    @staticmethod
    def _open(path):
        try:
            if os.name == "nt": os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as exc: messagebox.showerror("بازکردن", str(exc))

    def _log(self, text):
        self.log.config(state="normal"); self.log.insert("end", text + "\n"); self.log.config(state="disabled")
    @staticmethod
    def fmt_size(value):
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024: return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"
    def close(self):
        self.cancel_event.set(); self.cfg.scan_folders = list(self.folder_list.get(0, "end")); self.cfg.keep_folder = self.keep_var.get()
        self.cfg.priority_folders = [self.priority_var.get()]; self.cfg.detect_similar_names = self.similar_var.get(); self.cfg.window_geometry = self.geometry(); self.cfg.save(); self.destroy()
