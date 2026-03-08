"""
技师管理面板
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, time, datetime
from models import Technician, DEFAULT_START_TIME, DEFAULT_END_TIME, generate_time_slots, MAX_TECHNICIANS


class TechnicianPanel(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="📋 技师管理", padding=10)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 日期选择
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(date_frame, text="日期：").pack(side=tk.LEFT)

        today = date.today()
        dates = []
        for i in range(7):
            d = today + __import__('datetime').timedelta(days=i)
            dates.append(d.strftime("%Y-%m-%d"))

        self.date_var = tk.StringVar(value=dates[0])
        date_combo = ttk.Combobox(date_frame, textvariable=self.date_var,
                                   values=dates, state="readonly", width=14)
        date_combo.pack(side=tk.LEFT, padx=5)
        date_combo.bind("<<ComboboxSelected>>", self._on_date_change)

        # 快捷操作按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(btn_frame, text="全选", command=self._select_all, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全不选", command=self._deselect_all, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="保存设置", command=self._save_settings,
                   style="Accent.TButton", width=8).pack(side=tk.RIGHT, padx=2)

        # 技师列表 - 滚动区域
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0, height=280)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.tech_inner = ttk.Frame(canvas)

        self.tech_inner.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.tech_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 时间选项
        time_slots = generate_time_slots()

        self.tech_vars = []  # [(checkbox_var, start_var, end_var), ...]
        for i in range(1, MAX_TECHNICIANS + 1):
            row = ttk.Frame(self.tech_inner)
            row.pack(fill=tk.X, pady=2)

            cb_var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(row, text=f"{i}号", variable=cb_var, width=5)
            cb.pack(side=tk.LEFT)

            start_var = tk.StringVar(value="10:00")
            ttk.Combobox(row, textvariable=start_var, values=time_slots,
                         state="readonly", width=6).pack(side=tk.LEFT, padx=2)

            ttk.Label(row, text="-").pack(side=tk.LEFT)

            end_var = tk.StringVar(value="22:00")
            ttk.Combobox(row, textvariable=end_var, values=time_slots,
                         state="readonly", width=6).pack(side=tk.LEFT, padx=2)

            self.tech_vars.append((cb_var, start_var, end_var))

    def _on_date_change(self, event=None):
        """日期改变时加载已有设置"""
        self._load_settings()
        self.app.refresh_all()

    def _select_all(self):
        for cb_var, _, _ in self.tech_vars:
            cb_var.set(True)

    def _deselect_all(self):
        for cb_var, _, _ in self.tech_vars:
            cb_var.set(False)

    def get_work_date(self) -> date:
        return date.fromisoformat(self.date_var.get())

    def _save_settings(self):
        """保存技师设置到数据库"""
        work_date = self.get_work_date()

        for i, (cb_var, start_var, end_var) in enumerate(self.tech_vars):
            tech_id = i + 1
            if cb_var.get():
                start_parts = start_var.get().split(":")
                end_parts = end_var.get().split(":")
                tech = Technician(
                    tech_id=tech_id,
                    start_time=time(int(start_parts[0]), int(start_parts[1])),
                    end_time=time(int(end_parts[0]), int(end_parts[1])),
                    is_available=True,
                    work_date=work_date
                )
                self.app.db.set_technician(tech)
            else:
                self.app.db.remove_technician(tech_id, work_date)

        messagebox.showinfo("成功", f"已保存 {work_date} 的技师设置")
        self.app.refresh_all()

    def _load_settings(self):
        """从数据库加载设置"""
        work_date = self.get_work_date()
        techs = self.app.db.get_technicians(work_date)
        tech_dict = {t.tech_id: t for t in techs}

        for i, (cb_var, start_var, end_var) in enumerate(self.tech_vars):
            tech_id = i + 1
            if tech_id in tech_dict:
                t = tech_dict[tech_id]
                cb_var.set(True)
                start_var.set(t.start_time.strftime("%H:%M"))
                end_var.set(t.end_time.strftime("%H:%M"))
            else:
                cb_var.set(False)
                start_var.set("10:00")
                end_var.set("22:00")

    def load_initial(self):
        """初始加载"""
        self._load_settings()
