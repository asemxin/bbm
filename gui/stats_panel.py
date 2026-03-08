"""
技师统计面板
"""
import tkinter as tk
from tkinter import ttk
from datetime import date


class StatsPanel(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="📊 技师工作统计", padding=5)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Treeview
        columns = ("编号", "姓名", "上班时间", "已完成", "待完成", "总计")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=6)

        self.tree.heading("编号", text="编号")
        self.tree.heading("姓名", text="姓名")
        self.tree.heading("上班时间", text="上班时间")
        self.tree.heading("已完成", text="已完成")
        self.tree.heading("待完成", text="待完成")
        self.tree.heading("总计", text="总计")

        self.tree.column("编号", width=45, anchor="center")
        self.tree.column("姓名", width=75, anchor="center")
        self.tree.column("上班时间", width=95, anchor="center")
        self.tree.column("已完成", width=90, anchor="center")
        self.tree.column("待完成", width=90, anchor="center")
        self.tree.column("总计", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh(self):
        """刷新统计数据"""
        # 清空
        for item in self.tree.get_children():
            self.tree.delete(item)

        work_date = self.app.tech_panel.get_work_date()
        stats = self.app.scheduler.get_technician_stats(work_date)

        for s in stats:
            completed = f"{s['completed_count']}单/{s['completed_minutes']}分钟"
            scheduled = f"{s['scheduled_count']}单/{s['scheduled_minutes']}分钟"
            total = f"{s['total_count']}单/{s['total_minutes']}分钟"

            self.tree.insert("", tk.END, values=(
                f"{s['tech_id']}号",
                s['name'],
                f"{s['start_time']}-{s['end_time']}",
                completed,
                scheduled,
                total
            ))
