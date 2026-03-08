"""
预约面板
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
from models import (
    BookingType, DURATION_OPTIONS, generate_time_slots, MAX_TECHNICIANS
)


class BookingPanel(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="📞 客户预约", padding=10)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 预约类型
        row0 = ttk.Frame(self)
        row0.pack(fill=tk.X, pady=3)
        ttk.Label(row0, text="类型：").pack(side=tk.LEFT)
        self.type_var = tk.StringVar(value=BookingType.WALK_IN.value)
        ttk.Combobox(row0, textvariable=self.type_var,
                     values=[bt.value for bt in BookingType],
                     state="readonly", width=12).pack(side=tk.LEFT, padx=5)

        # 客户姓名
        row1 = ttk.Frame(self)
        row1.pack(fill=tk.X, pady=3)
        ttk.Label(row1, text="姓名：").pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.name_var, width=16).pack(side=tk.LEFT, padx=5)

        # 联系方式
        row2 = ttk.Frame(self)
        row2.pack(fill=tk.X, pady=3)
        ttk.Label(row2, text="电话：").pack(side=tk.LEFT)
        self.phone_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.phone_var, width=16).pack(side=tk.LEFT, padx=5)

        # 期望时间
        row3 = ttk.Frame(self)
        row3.pack(fill=tk.X, pady=3)
        ttk.Label(row3, text="时间：").pack(side=tk.LEFT)
        time_slots = generate_time_slots()
        # 默认当前时间最近的时间段
        now = datetime.now()
        now_str = f"{now.hour:02d}:{(now.minute // 30) * 30:02d}"
        default_time = now_str if now_str in time_slots else time_slots[0]
        self.time_var = tk.StringVar(value=default_time)
        ttk.Combobox(row3, textvariable=self.time_var, values=time_slots,
                     state="readonly", width=8).pack(side=tk.LEFT, padx=5)

        # 时长
        row4 = ttk.Frame(self)
        row4.pack(fill=tk.X, pady=3)
        ttk.Label(row4, text="时长：").pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="60")
        dur_combo = ttk.Combobox(row4, textvariable=self.duration_var,
                                  values=[str(d) for d in DURATION_OPTIONS],
                                  state="readonly", width=6)
        dur_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(row4, text="分钟").pack(side=tk.LEFT)

        # 点技师
        row5 = ttk.Frame(self)
        row5.pack(fill=tk.X, pady=3)
        ttk.Label(row5, text="点钟：").pack(side=tk.LEFT)
        tech_options = ["不指定"] + [f"{i}号" for i in range(1, MAX_TECHNICIANS + 1)]
        self.tech_var = tk.StringVar(value="不指定")
        ttk.Combobox(row5, textvariable=self.tech_var, values=tech_options,
                     state="readonly", width=8).pack(side=tk.LEFT, padx=5)

        # 备注
        row6 = ttk.Frame(self)
        row6.pack(fill=tk.X, pady=3)
        ttk.Label(row6, text="备注：").pack(side=tk.LEFT)
        self.notes_var = tk.StringVar()
        ttk.Entry(row6, textvariable=self.notes_var, width=16).pack(side=tk.LEFT, padx=5)

        # 提交按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="🔔 立即排班", command=self._submit,
                   style="Accent.TButton").pack(fill=tk.X)

    def _submit(self):
        """提交预约"""
        customer_name = self.name_var.get().strip()
        if not customer_name:
            messagebox.showwarning("提示", "请输入客户姓名")
            return

        work_date = self.app.tech_panel.get_work_date()
        start_time = self.time_var.get()
        duration = int(self.duration_var.get())

        # 解析点钟
        tech_str = self.tech_var.get()
        preferred_tech_id = None
        if tech_str != "不指定":
            preferred_tech_id = int(tech_str.replace("号", ""))

        # 解析预约类型
        booking_type = BookingType.WALK_IN
        for bt in BookingType:
            if bt.value == self.type_var.get():
                booking_type = bt
                break

        # 调用排班引擎
        result = self.app.scheduler.schedule_appointment(
            customer_name=customer_name,
            customer_phone=self.phone_var.get().strip(),
            work_date=work_date,
            start_time_str=start_time,
            duration=duration,
            preferred_tech_id=preferred_tech_id,
            booking_type=booking_type
        )

        if result.success:
            messagebox.showinfo("排班成功", result.message)
            self._clear_form()
            self.app.refresh_all()
        else:
            # 显示建议时段
            self._show_suggestions(result, customer_name, work_date, duration,
                                    preferred_tech_id, booking_type)

    def _show_suggestions(self, result, customer_name, work_date, duration,
                          preferred_tech_id, booking_type):
        """显示建议时段弹窗"""
        if not result.suggestions:
            messagebox.showinfo("无法排班", result.message)
            return

        dialog = tk.Toplevel(self)
        dialog.title("选择可用时段")
        dialog.geometry("380x400")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text=result.message, wraplength=350).pack(pady=10)

        # 建议列表
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self._selected_suggestion = None

        for i, sug in enumerate(result.suggestions):
            text = f"{sug['tech_name']}  {sug['start']}-{sug['end']}"
            btn = ttk.Button(list_frame, text=text,
                             command=lambda s=sug: self._accept_suggestion(
                                 dialog, s, customer_name, work_date, duration,
                                 preferred_tech_id, booking_type))
            btn.pack(fill=tk.X, pady=2)

        # 拒绝按钮
        ttk.Button(dialog, text="放弃预约", command=dialog.destroy).pack(pady=10)

    def _accept_suggestion(self, dialog, suggestion, customer_name, work_date,
                           duration, preferred_tech_id, booking_type):
        """接受建议时段"""
        result = self.app.scheduler.schedule_appointment(
            customer_name=customer_name,
            customer_phone=self.phone_var.get().strip(),
            work_date=work_date,
            start_time_str=suggestion['start'],
            duration=duration,
            preferred_tech_id=suggestion['tech_id'],
            booking_type=booking_type
        )

        if result.success:
            messagebox.showinfo("排班成功", result.message)
            self._clear_form()
            dialog.destroy()
            self.app.refresh_all()
        else:
            messagebox.showerror("错误", "排班失败，请重试")

    def _clear_form(self):
        """清空表单"""
        self.name_var.set("")
        self.phone_var.set("")
        self.tech_var.set("不指定")
        self.notes_var.set("")
