"""
主窗口 - 盲人按摩店排班系统
"""
import tkinter as tk
from tkinter import ttk
from database import Database
from scheduler import Scheduler
from gui.technician_panel import TechnicianPanel
from gui.booking_panel import BookingPanel
from gui.schedule_view import ScheduleView
from gui.stats_panel import StatsPanel


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💆 盲人按摩店排班系统 v1.0")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 600)

        # 初始化后端
        self.db = Database()
        self.scheduler = Scheduler(self.db)

        # 样式
        self._setup_styles()

        # 构建UI
        self._build_ui()

        # 加载初始数据
        self.tech_panel.load_initial()
        self.refresh_all()

        # 定时刷新（每60秒）
        self._auto_refresh()

    def _setup_styles(self):
        """设置主题样式"""
        style = ttk.Style()

        # 尝试用 clam 主题
        available = style.theme_names()
        if "clam" in available:
            style.theme_use("clam")

        # 自定义 Accent 按钮样式
        style.configure("Accent.TButton",
                         background="#4FC3F7",
                         foreground="#1E1E2E",
                         font=("Microsoft YaHei", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", "#29B6F6")])

        # 标签框标题
        style.configure("TLabelframe.Label",
                         font=("Microsoft YaHei", 11, "bold"))

        # Treeview 样式
        style.configure("Treeview",
                         font=("Microsoft YaHei", 9),
                         rowheight=28)
        style.configure("Treeview.Heading",
                         font=("Microsoft YaHei", 9, "bold"))

    def _build_ui(self):
        """构建主界面布局"""
        # 标题栏
        title_bar = ttk.Frame(self.root)
        title_bar.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(title_bar, text="💆 盲人按摩店智能排班系统 (由ma店长的老公开发)",
                 font=("Microsoft YaHei", 16, "bold"),
                 fg="#4FC3F7").pack(side=tk.LEFT)
                 
        # 增加帮助按钮
        help_btn = ttk.Button(title_bar, text="❓ 使用说明与关于", style="Accent.TButton", command=self._show_help)
        help_btn.pack(side=tk.RIGHT, padx=5, pady=5)
                 
        tk.Label(title_bar, text="同时支持通过 GitHub 生成能在苹果和安卓手机运行的 App",
                 font=("Microsoft YaHei", 10),
                 fg="#888888").pack(side=tk.RIGHT, pady=5)

        # 主体区域：左右分栏
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _show_help(self):
        import tkinter.messagebox as messagebox
        help_text = (
            "💆 盲人按摩店智能排班系统 v1.0\n\n"
            "👨‍💻 开发者：本软件由 ma 店长的老公倾情开发！\n"
            "🌐 全平台支持：同时提供通过 GitHub 自动生成的苹果免签版 (PWA) 和安卓真包 (.apk)。\n\n"
            "【功能说明】\n"
            "1. 员工设置：每天营业前，左侧选定上班日期，勾选今天出勤的技师并设置时间。\n"
            "2. 客人录单：前台接到预约或到店客人，在左下方录入客人名字及期望时长（可点钟）。\n"
            "3. 智能排班：点钟如有冲突，系统会推荐相近空档；不点钟则系统自动分配到最闲的技师处排钟。\n"
            "4. 错单调整：在右侧彩色排班表上，对着想要修改的记录“点击鼠标右键”，即可取消该排班。\n\n"
            "【本地数据安全】\n"
            "本系统为无网也可操作的离线单机版，数据会自动安全保存在同目录下的 massage.db 数据库中。"
        )
        messagebox.showinfo("软件说明与帮助", help_text)

        # === 左侧面板 ===
        left_frame = ttk.Frame(main_paned, width=320)

        # 技师管理
        self.tech_panel = TechnicianPanel(left_frame, self)
        self.tech_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 预约面板
        self.booking_panel = BookingPanel(left_frame, self)
        self.booking_panel.pack(fill=tk.X, pady=(0, 5))

        main_paned.add(left_frame, weight=0)

        # === 右侧面板 ===
        right_frame = ttk.Frame(main_paned)

        # 排班甘特图
        self.schedule_view = ScheduleView(right_frame, self)
        self.schedule_view.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # 统计面板
        self.stats_panel = StatsPanel(right_frame, self)
        self.stats_panel.pack(fill=tk.X)

        main_paned.add(right_frame, weight=1)

    def refresh_all(self):
        """刷新所有视图"""
        self.schedule_view.render()
        self.stats_panel.refresh()

    def _auto_refresh(self):
        """定时刷新"""
        self.refresh_all()
        self.root.after(60000, self._auto_refresh)  # 60秒刷新一次

    def run(self):
        """运行主循环"""
        self.root.mainloop()
        self.db.close()
