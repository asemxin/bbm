"""
排班甘特图可视化
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, time
from models import AppointmentStatus, generate_time_slots, DURATION_OPTIONS


# 配色方案 - 10个技师的颜色
TECH_COLORS = [
    "#4FC3F7",  # 浅蓝
    "#81C784",  # 浅绿
    "#FFB74D",  # 橙色
    "#E57373",  # 浅红
    "#BA68C8",  # 紫色
    "#4DD0E1",  # 青色
    "#FFD54F",  # 黄色
    "#A1887F",  # 棕色
    "#90A4AE",  # 灰蓝
    "#F06292",  # 粉色
]

TECH_COLORS_LIGHT = [
    "#B3E5FC",
    "#C8E6C9",
    "#FFE0B2",
    "#FFCDD2",
    "#E1BEE7",
    "#B2EBF2",
    "#FFF9C4",
    "#D7CCC8",
    "#CFD8DC",
    "#F8BBD0",
]


class ScheduleView(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="📅 实时排班表", padding=5)
        self.app = app
        self.cell_width = 50    # 每30分钟格子宽度
        self.row_height = 40    # 每行高度
        self.header_height = 30 # 表头高度
        self.label_width = 80   # 左侧标签宽度
        self._build_ui()

    def _build_ui(self):
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(toolbar, text="🔄 刷新", command=self._refresh, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 预约列表", command=self._show_appointment_list, width=10).pack(side=tk.LEFT, padx=2)

        # Canvas + 滚动条
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#1E1E2E",
            highlightthickness=0,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )

        self.h_scroll.configure(command=self.canvas.xview)
        self.v_scroll.configure(command=self.canvas.yview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 右键菜单
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.context_menu.add_command(label="取消预约", command=self._cancel_selected)
        self.context_menu.add_command(label="调整时间", command=self._adjust_selected)

        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<Button-1>", self._on_click)

        self._selected_appt_id = None

    def _refresh(self):
        self.app.refresh_all()

    def render(self):
        """重新绘制排班表"""
        self.canvas.delete("all")
        work_date = self.app.tech_panel.get_work_date()
        techs = self.app.db.get_technicians(work_date)

        if not techs:
            self.canvas.create_text(
                300, 100, text="暂无技师上班，请先设置技师",
                fill="#888", font=("Microsoft YaHei", 14)
            )
            return

        # 计算时间范围
        min_hour = min(t.start_time.hour for t in techs)
        max_hour = max(t.end_time.hour for t in techs)
        total_slots = (max_hour - min_hour) * 2  # 每小时2个slot

        canvas_width = self.label_width + total_slots * self.cell_width + 20
        canvas_height = self.header_height + len(techs) * self.row_height + 20
        self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

        # 画时间表头
        for i in range(total_slots + 1):
            x = self.label_width + i * self.cell_width
            hour = min_hour + i // 2
            minute = (i % 2) * 30

            # 竖线
            self.canvas.create_line(
                x, self.header_height, x, canvas_height,
                fill="#333346", width=1
            )

            # 时间标签（只显示整点和半点）
            if i < total_slots:
                time_str = f"{hour:02d}:{minute:02d}"
                self.canvas.create_text(
                    x + self.cell_width // 2, self.header_height // 2,
                    text=time_str, fill="#AAA", font=("Consolas", 8)
                )

        # 画技师行
        for row_idx, tech in enumerate(techs):
            y = self.header_height + row_idx * self.row_height

            # 横线
            self.canvas.create_line(
                0, y, canvas_width, y, fill="#333346", width=1
            )

            # 技师标签
            color = TECH_COLORS[(tech.tech_id - 1) % len(TECH_COLORS)]
            self.canvas.create_rectangle(
                2, y + 2, self.label_width - 2, y + self.row_height - 2,
                fill=color, outline="", stipple=""
            )
            self.canvas.create_text(
                self.label_width // 2, y + self.row_height // 2,
                text=tech.name, fill="#1E1E2E",
                font=("Microsoft YaHei", 10, "bold")
            )

            # 画工作时间范围背景
            tech_start_slot = (tech.start_time.hour - min_hour) * 2 + tech.start_time.minute // 30
            tech_end_slot = (tech.end_time.hour - min_hour) * 2 + tech.end_time.minute // 30
            x1 = self.label_width + tech_start_slot * self.cell_width
            x2 = self.label_width + tech_end_slot * self.cell_width
            self.canvas.create_rectangle(
                x1, y + 2, x2, y + self.row_height - 2,
                fill="#2A2A3E", outline=""
            )

            # 画预约色块
            appointments = self.app.db.get_appointments_for_tech(tech.tech_id, work_date)
            for appt in appointments:
                if appt.status == AppointmentStatus.CANCELLED:
                    continue
                self._draw_appointment_block(appt, tech, min_hour, y)

        # 最后一条横线
        y_bottom = self.header_height + len(techs) * self.row_height
        self.canvas.create_line(0, y_bottom, canvas_width, y_bottom, fill="#333346")

        # 画当前时间线
        now = datetime.now()
        if work_date == date.today() and min_hour <= now.hour < max_hour:
            now_slot = (now.hour - min_hour) * 2 + now.minute / 30
            now_x = self.label_width + now_slot * self.cell_width
            self.canvas.create_line(
                now_x, 0, now_x, canvas_height,
                fill="#FF5555", width=2, dash=(4, 2)
            )
            self.canvas.create_text(
                now_x, 8, text="▼ 现在", fill="#FF5555",
                font=("Microsoft YaHei", 8)
            )

    def _draw_appointment_block(self, appt, tech, min_hour, y):
        """画单个预约色块"""
        appt_start = appt.start_time.hour * 60 + appt.start_time.minute
        appt_end = appt.end_time.hour * 60 + appt.end_time.minute
        min_minutes = min_hour * 60

        x1 = self.label_width + (appt_start - min_minutes) / 30 * self.cell_width
        x2 = self.label_width + (appt_end - min_minutes) / 30 * self.cell_width

        color = TECH_COLORS[(tech.tech_id - 1) % len(TECH_COLORS)]
        light_color = TECH_COLORS_LIGHT[(tech.tech_id - 1) % len(TECH_COLORS_LIGHT)]

        # 判断状态决定样式
        now = datetime.now()
        now_min = now.hour * 60 + now.minute
        if appt.work_date == date.today() and appt_end <= now_min:
            # 已完成 - 半透明
            fill_color = light_color
            text_color = "#666"
        else:
            fill_color = color
            text_color = "#1E1E2E"

        # 带圆角的矩形（用多边形模拟）
        padding = 3
        tag = f"appt_{appt.appointment_id}"
        self.canvas.create_rectangle(
            x1 + 1, y + padding, x2 - 1, y + self.row_height - padding,
            fill=fill_color, outline="#FFF", width=1, tags=tag
        )

        # 文字：客户名 + 点钟标记
        label = appt.customer_name or "客户"
        if appt.is_named:
            label = f"⭐{label}"
        # 只有宽度足够才显示文字
        if x2 - x1 > 40:
            self.canvas.create_text(
                (x1 + x2) / 2, y + self.row_height // 2,
                text=label, fill=text_color,
                font=("Microsoft YaHei", 8, "bold"),
                tags=tag
            )

    def _on_click(self, event):
        """点击选择预约"""
        item = self.canvas.find_closest(event.x, event.y)
        if item:
            tags = self.canvas.gettags(item[0])
            for tag in tags:
                if tag.startswith("appt_"):
                    self._selected_appt_id = int(tag.split("_")[1])
                    return
        self._selected_appt_id = None

    def _on_right_click(self, event):
        """右键菜单"""
        self._on_click(event)
        if self._selected_appt_id:
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _cancel_selected(self):
        """取消选中的预约"""
        if self._selected_appt_id:
            if messagebox.askyesno("确认", "确定要取消这个预约吗？"):
                self.app.scheduler.cancel_appointment(self._selected_appt_id)
                self.app.refresh_all()

    def _adjust_selected(self):
        """调整选中的预约"""
        if not self._selected_appt_id:
            return

        work_date = self.app.tech_panel.get_work_date()
        appointments = self.app.db.get_appointments(work_date)
        target = None
        for a in appointments:
            if a.appointment_id == self._selected_appt_id:
                target = a
                break
        if not target:
            return

        # 弹窗
        dialog = tk.Toplevel(self)
        dialog.title("调整排班")
        dialog.geometry("300x250")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=f"客户：{target.customer_name}").pack(pady=5)

        # 新时间
        time_frame = ttk.Frame(dialog)
        time_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(time_frame, text="新时间：").pack(side=tk.LEFT)
        time_slots = generate_time_slots()
        current_time = target.start_time.strftime("%H:%M") if target.start_time else time_slots[0]
        time_var = tk.StringVar(value=current_time)
        ttk.Combobox(time_frame, textvariable=time_var, values=time_slots,
                     state="readonly", width=8).pack(side=tk.LEFT, padx=5)

        # 新时长
        dur_frame = ttk.Frame(dialog)
        dur_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dur_frame, text="时长：").pack(side=tk.LEFT)
        dur_var = tk.StringVar(value=str(target.duration))
        ttk.Combobox(dur_frame, textvariable=dur_var,
                     values=[str(d) for d in DURATION_OPTIONS],
                     state="readonly", width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(dur_frame, text="分钟").pack(side=tk.LEFT)

        # 新技师
        tech_frame = ttk.Frame(dialog)
        tech_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(tech_frame, text="技师：").pack(side=tk.LEFT)
        techs = self.app.db.get_technicians(work_date)
        tech_options = [f"{t.tech_id}号" for t in techs]
        tech_var = tk.StringVar(value=f"{target.tech_id}号")
        ttk.Combobox(tech_frame, textvariable=tech_var, values=tech_options,
                     state="readonly", width=8).pack(side=tk.LEFT, padx=5)

        def confirm():
            new_tech_id = int(tech_var.get().replace("号", ""))
            result = self.app.scheduler.adjust_appointment(
                self._selected_appt_id,
                time_var.get(),
                int(dur_var.get()),
                new_tech_id,
                work_date
            )
            if result.success:
                messagebox.showinfo("成功", result.message)
                dialog.destroy()
                self.app.refresh_all()
            else:
                messagebox.showerror("失败", result.message)

        ttk.Button(dialog, text="确认调整", command=confirm,
                   style="Accent.TButton").pack(pady=15)

    def _show_appointment_list(self):
        """显示预约列表"""
        work_date = self.app.tech_panel.get_work_date()
        appointments = self.app.db.get_appointments(work_date)

        dialog = tk.Toplevel(self)
        dialog.title(f"{work_date} 预约列表")
        dialog.geometry("650x400")
        dialog.transient(self)

        # Treeview
        columns = ("id", "客户", "电话", "技师", "时间", "时长", "点钟", "类型", "状态")
        tree = ttk.Treeview(dialog, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=70)
        tree.column("id", width=40)
        tree.column("客户", width=80)
        tree.column("电话", width=100)

        for appt in appointments:
            start = appt.start_time.strftime("%H:%M") if appt.start_time else ""
            end = appt.end_time.strftime("%H:%M") if appt.end_time else ""
            tree.insert("", tk.END, values=(
                appt.appointment_id,
                appt.customer_name,
                appt.customer_phone,
                f"{appt.tech_id}号" if appt.tech_id else "",
                f"{start}-{end}",
                f"{appt.duration}分钟",
                "是" if appt.is_named else "否",
                appt.booking_type.value,
                appt.status.value
            ))

        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
