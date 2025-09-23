# -*- coding: utf-8 -*-
# 此檔案程式碼設計部分邏輯參考自 ChatGPT 的建議（2025/06/06）
"""
SmartStudy 系統 
"""

import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
import json
import datetime
import random
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams
from PIL import Image, ImageTk, ImageDraw
import os
import calendar
import time
import requests
from io import BytesIO
import base64
import platform  

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def get_app_data_folder(subfolder):
    """跨平台獲取用户數據資料夾"""
    system = platform.system()
    if system == "Windows":
        base_dir = os.getenv('APPDATA')
    elif system == "Darwin":  # macOS
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:  # Linux and other Unix-like
        base_dir = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    
    app_dir = os.path.join(base_dir, subfolder)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def play_sound():
    """跨平台播放提示音"""
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 500)
        else:
            # Unix-like 系统的簡單響鈴
            print("\a")
            # 對於macOS/Linux的GUI通知音
            os.system('echo -e "\a"')
    except Exception as e:
        print("音效播放失敗:", e)

# 建立圖片目錄和預設圖片
def create_default_images():
    # 使用跨平台路徑
    img_dir = get_app_data_folder("SmartStudyImages")

    # 定義圖片大小和顏色 
    img_size = (300, 300)
    colors = {
        "normal": "#4a6fa5",
        "happy": "#4fc3f7",
        "sad": "#166088",
        "sleepy": "#a5d6a7"
    }
    
    # 定義圖片文件名
    image_files = {
        "normal": "cat_normal.png",
        "happy": "cat_happy.png",
        "sad": "cat_sad.png",
        "sleepy": "cat_sleepy.png"
    }
    
    
    for state, color in colors.items():
        img_path = os.path.join(img_dir, image_files[state])
        # 如果圖片已經存在，則跳過
        if os.path.exists(img_path):
            continue
            
        # 否則創建預設圖片
        img = Image.new("RGB", img_size, color)
        draw = ImageDraw.Draw(img)
        draw.ellipse((50, 50, 250, 250), fill="#FFD700")  # 貓臉
        draw.ellipse((100, 100, 130, 130), fill="black")   # 左眼
        draw.ellipse((170, 100, 200, 130), fill="black")   # 右眼
        draw.arc((100, 150, 200, 200), 0, 180, fill="black", width=5)  # 嘴巴
        
        # 保存圖片
        img.save(img_path)

# 創建預設圖片（如果不存在）
create_default_images()

class SmartStudyApp:
    def __init__(self, root):
        # 初始化各種變數
        self.course_day = None
        self.start_time = None
        self.end_time = None
        self.course_tree = None
        self.exam_tree = None
        self.calendar_frame = None  # 日曆框架
        
        # 主視窗設定
        self.root = root
        self.root.title("SmartStudy - 智慧學習助手")
        self.root.geometry("1200x800")  # 加大視窗尺寸以容納更多內容
        
        # 設定應用程式圖標 (跨平台支持)
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("smartstudy_icon.ico")
            else:
                # 對於非Windows系统使用PNG圖標
                img = Image.open("smartstudy_icon.png")
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
        except:
            pass
        
        # 設定字體
        self.title_font = font.Font(family="Microsoft YaHei", size=14, weight="bold")
        self.label_font = font.Font(family="Microsoft YaHei", size=10)
        self.button_font = font.Font(family="Microsoft YaHei", size=10, weight="bold")  # 按鈕字體加粗
        
        # 設定主題顏色
        self.primary_color = "#4a6fa5"
        self.secondary_color = "#166088"
        self.accent_color = "#4fc3f7"
        self.background_color = "#f0f4f8"
        self.text_color = "#333333"
        self.button_text_color = "#000000"  # 按鈕文字顏色設定為黑色
        
        # 初始化資料結構
        self.setup_data_structures()
        self.load_data()
        self.setup_styles()  # 確保樣式設定存在
        self.create_main_interface()
        
        # 設定視窗最小大小
        self.root.minsize(1000, 700)
        
        # 設定視窗居中
        self.center_window()
        
        # 檢查每日成就
        self.check_daily_achievements()

    def center_window(self):
        """將視窗居中顯示於螢幕中央"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_data_structures(self):
        """初始化所有資料結構"""
        self.courses = []  # 儲存課程資訊
        self.exams = []  # 儲存考試資訊
        self.study_logs = []  # 儲存每日學習總時間
        self.study_records = []  # 儲存詳細學習記錄（科目、時間）
        self.catcoins = 0  # 虛擬貨幣數量
        self.badges = []  # 獲得的徽章
        self.pet_status = {"happiness": 50, "energy": 50, "level": 1, "xp": 0}  # 寵物狀態
        self.sessions_completed = 0  # 完成的學習次數
        self.daily_goals = {}  # 每日學習目標
        self.achievements = {  # 成就系統
            "consecutive_days": 0,
            "total_study_hours": 0,
            "completed_goals": 0,
            "last_study_date": None
        }
        self.study_plan = {}  # 學習計畫
        self.pet_images = {}  # 儲存寵物圖片資源

    def create_main_interface(self):
        """創建主界面"""
        # 設定主視窗背景色
        self.root.configure(bg=self.background_color)
        
        # 創建頂部標題欄
        self.create_header()
        
        # 主界面設定
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        
        # 設定Notebook樣式
        style = ttk.Style()
        style.configure("TNotebook", background=self.background_color)
        style.configure("TNotebook.Tab", font=self.label_font, padding=[10, 5])
        
        # 創建各個功能頁面
        self.schedule_page = ttk.Frame(self.notebook)
        self.timer_page = ttk.Frame(self.notebook)
        self.progress_page = ttk.Frame(self.notebook)
        self.pet_page = ttk.Frame(self.notebook)
        self.calendar_page = ttk.Frame(self.notebook)  # 日曆頁面

        self.notebook.add(self.schedule_page, text="📅 課程排程")  
        self.notebook.add(self.timer_page, text="⏱️ 學習番茄鐘")
        self.notebook.add(self.calendar_page, text="🗓️ 學習計畫")
        self.notebook.add(self.progress_page, text="📊 學習進度")
        self.notebook.add(self.pet_page, text="🐱 虛擬寵物")

        # 初始化各個頁面
        self.setup_schedule_page()
        self.setup_timer_page()
        self.setup_progress_page()
        self.setup_pet_page()
        self.setup_calendar_page()

        # 綁定標籤切換事件以更新科目列表
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """當切換標籤頁時更新科目列表"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 1:  # 如果是計時器頁面
            self.update_timer_subjects()

    def load_data(self):
        pass
    def create_header(self):
        """創建頂部標題欄"""
        header_frame = tk.Frame(self.root, bg=self.primary_color)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        # 標題格式
        title_label = tk.Label(
            header_frame, 
            text="SmartStudy 智慧學習助手", 
            font=self.title_font,
            bg=self.primary_color,
            fg="white",
            padx=20,
            pady=10
        )
        title_label.pack(side="left")
        
        # Catcoins 顯示格式
        self.catcoins_header = tk.Label(
            header_frame,
            text=f"Catcoins: {self.catcoins}",
            font=self.button_font,
            bg=self.primary_color,
            fg="white",
            padx=10,
            pady=10
        )
        self.catcoins_header.pack(side="right")
        
        # 分隔線
        separator = ttk.Separator(self.root, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=0)

    def setup_schedule_page(self):
        """設定課程排程頁面"""
        # 設定頁面背景
        self.schedule_page.configure(style="Background.TFrame")
        
        # 主容器框架
        main_frame = ttk.Frame(self.schedule_page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左側框架 - 輸入表單
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # 右側框架 - 顯示列表
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 課程輸入表單
        course_frame = ttk.LabelFrame(
            left_frame, 
            text="新增課程", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        course_frame.pack(fill="x", pady=5)
        
        # 選擇課程在星期幾
        ttk.Label(course_frame, text="星期:").grid(row=0, column=0, sticky="w")
        self.course_day = ttk.Combobox(course_frame, values=["星期一","星期二","星期三","星期四","星期五","星期六","星期日"])
        self.course_day.grid(row=0, column=1, sticky="ew", pady=2)  
        
        # 課程名稱
        ttk.Label(course_frame, text="課程名稱:").grid(row=1, column=0, sticky="w")
        self.course_name = ttk.Entry(course_frame)
        self.course_name.grid(row=1, column=1, sticky="ew", pady=2)
        
        # 開始時間
        ttk.Label(course_frame, text="開始時間:").grid(row=2, column=0, sticky="w")
        self.start_time = ttk.Combobox(course_frame, values=[f"{h:02d}:{m:02d}" for h in range(8,22) for m in [0,30]])
        self.start_time.grid(row=2, column=1, sticky="ew", pady=2)  
        
        # 結束時間
        ttk.Label(course_frame, text="結束時間:").grid(row=3, column=0, sticky="w")  
        self.end_time = ttk.Combobox(course_frame, values=[f"{h:02d}:{m:02d}" for h in range(8,22) for m in [0,30]])
        self.end_time.grid(row=3, column=1, sticky="ew", pady=2)  
        
        # 新增/刪除按鈕
        btn_frame = ttk.Frame(course_frame)  
        btn_frame.grid(row=4, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="新增課程", command=self.add_course, style="Accent.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="刪除課程", command=self.delete_course, style="Accent.TButton").pack(side="left", padx=5)

        # 課程列表Treeview
        self.course_tree = ttk.Treeview(
            right_frame,
            columns=("day","name","time"),
            show="headings",  # 只顯示標題(不顯示圖標)
            selectmode="browse",  # 每次只能選取一列
            height=10  # 列表最多顯示10列
        )
        self.course_tree.heading("day", text="星期")  # 為每個欄位設定標題文字
        self.course_tree.heading("name", text="課程名稱") 
        self.course_tree.heading("time", text="時間")
        self.course_tree.column("day", width=80)  # 設定欄位寬度，單位為像素
        self.course_tree.column("name", width=120)
        self.course_tree.column("time", width=100)
        self.course_tree.pack(fill="both", expand=True, pady=5)  # 將表格放入 right_frame 中，允許自動伸縮，上下加入 5 像素間距
        
        # 考試資訊表單
        exam_frame = ttk.LabelFrame(
            left_frame,
            text="考試資訊",
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        exam_frame.pack(fill="x", pady=5)
        
        # 設定考試科目的輸入欄位
        ttk.Label(exam_frame, text="考試科目:").grid(row=0, column=0, sticky="w")
        self.exam_subject = ttk.Entry(exam_frame)
        self.exam_subject.grid(row=0, column=1, sticky="ew", pady=2)

        # 考試日期
        ttk.Label(exam_frame, text="考試日期 (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        self.exam_date = ttk.Entry(exam_frame)
        self.exam_date.grid(row=1, column=1, sticky="ew", pady=2)

        # 考試重要性
        ttk.Label(exam_frame, text="重要性 (1-5):").grid(row=2, column=0, sticky="w")
        self.exam_priority = ttk.Combobox(exam_frame, values=[1, 2, 3, 4, 5])
        self.exam_priority.grid(row=2, column=1, sticky="ew", pady=2)
        self.exam_priority.current(2)
        
        # 在考試表單下方新增刪除按鈕
        ttk.Button(exam_frame, text="新增考試", command=self.add_exam, style="Accent.TButton").grid(row=3, column=0, pady=5)
        ttk.Button(exam_frame, text="刪除考試", command=self.delete_exam, style="Accent.TButton").grid(row=3, column=1, pady=5)
        
        # 考試列表Treeview
        self.exam_tree = ttk.Treeview(
            right_frame,
            columns=("subject","date","priority","days_left"), 
            show="headings",  
            selectmode="browse",  
            height=10  
        )
        self.exam_tree.heading("subject", text="科目")  # 同290行課程列表的格式
        self.exam_tree.heading("date", text="考試日期") 
        self.exam_tree.heading("priority", text="重要性")
        self.exam_tree.heading("days_left", text="剩餘天數")
        self.exam_tree.column("subject", width=120)  
        self.exam_tree.column("date", width=100)
        self.exam_tree.column("priority", width=80)
        self.exam_tree.column("days_left", width=80)
        self.exam_tree.pack(fill="both", expand=True, pady=5)  
        
        # 初始化列表顯示
        self.update_course_list()
        self.update_exam_list()

        # 生成學習計畫按鈕
        ttk.Button(
            left_frame,
            text="📝 生成學習計畫",
            command=self.generate_study_plan,
            style="Primary.TButton"
        ).pack(fill="x", pady=10)

    def setup_styles(self):
        """設定自定義樣式"""
        style = ttk.Style()
        
        # 背景框架樣式
        style.configure("Background.TFrame", background=self.background_color)
        
        # 卡片樣式
        style.configure("Card.TLabelframe", 
                       background=self.background_color,
                       bordercolor="#dddddd",
                       relief="solid",
                       borderwidth=1)
        style.configure("Card.TLabelframe.Label", 
                       background=self.background_color,
                       font=self.label_font)
        style.configure("Card.TLabel", 
                       background=self.background_color,
                       font=self.label_font)
        
        # 按鈕樣式 - 按鈕文字顏色設定為黑色
        style.configure("Primary.TButton",
                       font=self.button_font,
                       background=self.primary_color,
                       foreground=self.button_text_color,  # 黑色文字
                       padding=5,
                       borderwidth=0)
        style.map("Primary.TButton",
                 background=[("active", self.secondary_color), ("pressed", self.secondary_color)],
                 foreground=[("active", "black"), ("pressed", "black")])  # 保持黑色
        
        style.configure("Accent.TButton",
                       font=self.button_font,
                       background=self.accent_color,
                       foreground=self.button_text_color,  # 黑色文字
                       padding=5,
                       borderwidth=0)
        style.map("Accent.TButton",
                 background=[("active", "#42a5f5"), ("pressed", "#42a5f5")],
                 foreground=[("active", "black"), ("pressed", "black")])  # 保持黑色

    def add_course(self):
        """新增課程到系統中"""
        day = self.course_day.get()
        name = self.course_name.get().strip()
        start = self.start_time.get()
        end = self.end_time.get()
        # 這邊是提醒訊息
        if not all([day, name, start, end]):
            messagebox.showwarning("警告", "請填寫完整的課程資訊！")
            return
            
        try:
            # 驗證時間格式
            datetime.datetime.strptime(start, "%H:%M")
            datetime.datetime.strptime(end, "%H:%M")
            if start >= end:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "時間格式不正確或開始時間晚於結束時間！")  
            return
        
        course = {
            "day": day,
            "name": name,
            "time": f"{start}-{end}",
            "start": start,
            "end": end
        }
        self.courses.append(course)
        self.update_course_list()
        self.save_data()
        self.clear_course_inputs()

    def delete_course(self):
        """從系統中刪除選中的課程"""
        selected = self.course_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請先選擇要刪除的課程！")
            return
            
        index = int(self.course_tree.index(selected[0]))  # 取得使用者在課程 Treeview 中選取的項目index
        if 0 <= index < len(self.courses):  # 檢查這個index是否在 self.courses 清單的有效範圍內
            self.courses.pop(index)
            self.update_course_list()
            self.save_data()
     
    def add_exam(self):
        """新增考試到系統中"""  # 從輸入欄位取得考試資訊，並去除多餘空白。
        subject = self.exam_subject.get().strip()
        date = self.exam_date.get().strip()
        priority = self.exam_priority.get()
        
        if not subject or not date:
            messagebox.showwarning("警告", "請填寫完整的考試資訊!")
            return
            
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning("警告", "日期格式不正確，請使用 YYYY-MM-DD 格式!")
            return
            
        exam = {
            "subject": subject,
            "date": date,
            "priority": int(priority),
            "days_left": self.calculate_days_left(date)
        }
        self.exams.append(exam)    # 把考試資料加入清單
        self.update_exam_list()    # 更新考試列表顯示
        self.exam_subject.delete(0, tk.END)  
        self.exam_date.delete(0, tk.END)    
        self.save_data()    # 儲存所有資訊

    def delete_exam(self):
        """從系統中刪除選中的考試"""
        selected = self.exam_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請先選擇要刪除的考試！")  # 提醒使用者要先選擇刪除項目
            return
            
        index = int(self.exam_tree.index(selected[0]))  # 同上面課程的做法，只是改成提取考試的index
        if 0 <= index < len(self.exams):  # 一樣檢查index是否在有效範圍內
            self.exams.pop(index)
            self.update_exam_list()
            self.save_data()

    def clear_course_inputs(self):
        """清空課程輸入欄位"""
        self.course_name.delete(0, tk.END)
        self.start_time.set('')
        self.end_time.set('')

    def update_course_list(self):
        """更新課程列表顯示"""
        self.course_tree.delete(*self.course_tree.get_children())
        for course in sorted(self.courses, key=lambda x: x["day"]):  # 將課程清單依照日期排序
            self.course_tree.insert("", "end", values=(
                course["day"],
                course["name"],
                f"{course['start']}-{course['end']}"
            ))

    def update_exam_list(self):
        """更新考試列表顯示"""
        self.exam_tree.delete(*self.exam_tree.get_children())
        for exam in sorted(self.exams, key=lambda x: x["date"]):  # 將考試清單依照考試的日期從早到晚排序
            self.exam_tree.insert("", "end", values=(
                exam["subject"],
                exam["date"],
                exam["priority"],
                exam.get("days_left", self.calculate_days_left(exam["date"]))
            ))   # 顯示距離考試還有幾天，如果 exam 資料裡已有 "days_left" 欄位就拿來用；否則就用 calculate_days_left 這個函式

    def calculate_days_left(self, exam_date):
        """計算考試剩餘天數"""
        try:
            exam_date = datetime.datetime.strptime(exam_date, "%Y-%m-%d").date()  # 將字串格式的考試日期轉換成 datetime.date 物件
            today = datetime.date.today()
            return (exam_date - today).days  # 計算考試日期和今天之間相差幾天並回傳這個天數。
        except:
            return 0
        
    def generate_study_plan(self):
        """生成學習計畫 - 改進版：根據考試日期調整計畫範圍"""
        if not self.exams:
            messagebox.showwarning("警告", "請先添加考試資訊!")
            return

        # 更新考試剩餘天數
        today = datetime.date.today()
        for exam in self.exams:
            exam_date = datetime.datetime.strptime(exam["date"], "%Y-%m-%d").date()  # 將考試日期轉換為 datetime.date 物件
            exam["days_left"] = max(0, (exam_date - today).days)
            # 計算優先級分數 (剩餘天數越少、重要性越高，分數越高)
            exam["priority_score"] = (exam["priority"] * 10) + (30 - min(exam["days_left"], 30))
        
        # 按優先級排序
        sorted_exams = sorted([e for e in self.exams if e["days_left"] > 0], 
                            key=lambda x: -x["priority_score"])

        if not sorted_exams:
            messagebox.showinfo("提示", "目前沒有即將到來的考試!")  # 如果接下來沒有考試的提示訊息
            return
    
        # 生成學習計畫
        self.study_plan = {}
        
        # 找出所有考試科目及其最後考試日期
        subject_last_exam = {}   # 用來記錄每個科目的最後考試日期
        for exam in sorted_exams:  
            exam_date = datetime.datetime.strptime(exam["date"], "%Y-%m-%d").date()  
            if exam["subject"] not in subject_last_exam or exam_date > subject_last_exam[exam["subject"]]:  
                subject_last_exam[exam["subject"]] = exam_date  # 如果有更晚的考試就更新科目的最後考試日期
        
        # 從今天開始到最後一個考試的日期
        end_date = max(subject_last_exam.values())
        current_date = datetime.date.today()
        
        # 為每一天分配學習任務
        while current_date <= end_date:
            # 跳過週末（可根據需要調整）
            if current_date.weekday() >= 5:  # 5=星期六, 6=星期日
                current_date += datetime.timedelta(days=1)
                continue
                
            # 檢查當前日期是否超過某科目的最後考試日期
            active_subjects = []
            for subject, last_exam_date in subject_last_exam.items():
                if current_date < last_exam_date:
                    active_subjects.append(subject)
            
            if not active_subjects:
                break  # 所有科目考試都已結束
                
            # 為每一天分配2-3個科目（根據考試急迫性）
            day_plan = []
            
            # 優先安排即將考試的科目
            urgent_subjects = []
            for exam in sorted_exams:
                exam_date = datetime.datetime.strptime(exam["date"], "%Y-%m-%d").date()
                days_left = (exam_date - current_date).days
                if days_left <= 3 and exam["subject"] in active_subjects and exam["subject"] not in urgent_subjects:
                    urgent_subjects.append(exam["subject"])   # 如果考試剩不到3天，則優先安排該科目
            
            # 如果沒有即將考試的科目，則選擇優先度最高的科目
            if not urgent_subjects:
                for exam in sorted_exams:
                    if exam["subject"] in active_subjects and exam["subject"] not in [task["subject"] for task in day_plan]:
                        urgent_subjects.append(exam["subject"])
                        if len(urgent_subjects) >= 2:  # 最多選擇2個科目
                            break
            
            # 分配學習時間（30-90分鐘）
            for subject in urgent_subjects[:3]:  # 最多3個科目
                # 根據考試急迫性調整學習時間
                exam_dates = [datetime.datetime.strptime(e["date"], "%Y-%m-%d").date() 
                             for e in sorted_exams if e["subject"] == subject]
                min_days_left = min((exam_date - current_date).days for exam_date in exam_dates)
                
                # 考試越近，學習時間越長
                if min_days_left <= 1:
                    study_time = random.randint(60, 90)  # 考試前1天，學習60-90分鐘
                elif min_days_left <= 3:
                    study_time = random.randint(45, 75)  # 考試前3天，學習45-75分鐘
                else:
                    study_time = random.randint(30, 60)  # 其他時間，學習30-60分鐘
                
                day_plan.append({
                    "subject": subject,
                    "time": study_time,
                    "completed": False
                })
            
            self.study_plan[current_date.strftime("%Y-%m-%d")] = day_plan
            current_date += datetime.timedelta(days=1)
        
        # 顯示成功訊息
        messagebox.showinfo("成功", "學習計畫已生成！請查看'學習計畫'頁面")
        
        # 更新日曆顯示
        self.update_calendar()
        self.notebook.select(self.calendar_page)  # 自動切換到日曆頁面
        
        # 保存數據
        self.save_data()

    def setup_timer_page(self):
        """設置番茄鐘頁面"""
        # 設置頁面背景
        self.timer_page.configure(style="Background.TFrame")
        
        # 主容器框架
        main_frame = ttk.Frame(self.timer_page, style="Background.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Pomodoro 計時器設定
        self.timer_frame = ttk.LabelFrame(
            main_frame, 
            text="🍅 學習番茄鐘", 
            padding=(20, 15),
            style="Card.TLabelframe"
        )
        self.timer_frame.pack(fill="both", expand=True)
        
        # 科目選擇框架
        subject_frame = ttk.Frame(self.timer_frame, style="Background.TFrame")
        subject_frame.pack(fill="x", pady=10)
        
        ttk.Label(subject_frame, text="選擇科目:", style="Card.TLabel").pack(side="left", padx=5)
        
        # 獲得所有科目（課程+考試+其他）
        self.subject_var = tk.StringVar()
        self.subject_combobox = ttk.Combobox(subject_frame, textvariable=self.subject_var)
        self.subject_combobox.pack(side="left", padx=5, fill="x", expand=True)
        
        # 更新科目列表
        self.update_timer_subjects()
        
        # 自訂時間框架
        time_frame = ttk.Frame(self.timer_frame, style="Background.TFrame")
        time_frame.pack(fill="x", pady=10)
        
        ttk.Label(time_frame, text="自訂時間 (分鐘):", style="Card.TLabel").pack(side="left", padx=5)
        
        self.custom_time = tk.StringVar(value="25")
        ttk.Entry(time_frame, textvariable=self.custom_time, width=5).pack(side="left", padx=5)
        
        # 番茄鐘顯示
        timer_display_frame = ttk.Frame(self.timer_frame, style="Background.TFrame")
        timer_display_frame.pack(pady=20)
        
        # 建立番茄鐘的字串變數 time_left
        self.time_left = tk.StringVar()
        self.time_left.set("25:00")  # 預設顯示25分鐘
        self.timer_label = ttk.Label(
            timer_display_frame,   # 放在 timer_display_frame 裡
            textvariable=self.time_left,   # 使用 time_left 變數來顯示時間
            font=("Helvetica", 48, "bold"),
            foreground=self.primary_color,
            style="Background.TLabel"  # 套用背景樣式（可自定義）
        )
        self.timer_label.pack()
        # 番茄鐘狀態顯示，建立番茄鐘狀態的字串變數 session_type
        self.session_type = tk.StringVar()
        self.session_type.set("準備開始")  # 預設狀態為"準備開始"
        self.session_label = ttk.Label(
            timer_display_frame, 
            textvariable=self.session_type,    # 使用 session_type 變數來顯示當前狀態
            font=self.label_font,
            style="Background.TLabel"
        )
        self.session_label.pack()
        
        # 按鈕框架
        button_frame = ttk.Frame(self.timer_frame, style="Background.TFrame")
        button_frame.pack(pady=20)  # 垂直間距 20，讓按鈕和上方區塊有空間
        
        self.start_button = ttk.Button(
            button_frame, 
            text="▶️ 開始", 
            command=self.start_timer,  # 將按鈕與開始計時的函式結合
            style="Primary.TButton",
            width=10
        )
        self.start_button.pack(side="left", padx=10)
        
        self.pause_button = ttk.Button(   # 暫停按鈕：一開始為停用狀態，開始後才啟用
            button_frame, 
            text="⏸️ 暫停", 
            command=self.pause_timer, 
            state="disabled",  # 初始設成停用狀態，避免誤按
            style="Primary.TButton",
            width=10
        )
        self.pause_button.pack(side="left", padx=10)
        
        self.reset_button = ttk.Button(
            button_frame, 
            text="🔄 重置", 
            command=self.reset_timer,
            style="Primary.TButton",
            width=10
        )
        self.reset_button.pack(side="left", padx=10)
        
        # 番茄鐘說明
        info_frame = ttk.Frame(self.timer_frame, style="Background.TFrame")
        info_frame.pack(fill="x", pady=10)
        
        info_text = """
        學習番茄鐘使用說明:
        1. 選擇要學習的科目
        2. 設定自訂學習時間（預設25分鐘）
        3. 點擊"開始"按鈕開始學習計時
        4. 學習結束後，系統會自動進入5分鐘的休息時間
        5. 完成一個學習階段後，您將獲得Catcoins獎勵
        6. 重複這個循環來提高您的學習效率!
        """
        info_label = ttk.Label(
            info_frame, 
            text=info_text, 
            font=self.label_font,
            style="Background.TLabel",
            justify="left"
        )
        info_label.pack()
        
        # 番茄鐘的初始狀態
        self.is_running = False  # 是否正在計時(False表示沒計時)
        self.is_break = False  # 是否在休息時間(False表示在讀書)
        self.seconds_left = 25 * 60  # 25分鐘學習時間
        self.timer_id = None
        self.current_subject = ""  # 當前學習科目

    def update_timer_subjects(self):
        """更新番茄鐘頁面的科目列表"""
        # 獲得所有科目（課程+考試+其他）
        subjects = [course["name"] for course in self.courses]
        subjects += [exam["subject"] for exam in self.exams]
        subjects = list(set(subjects))  # 去重
        subjects.sort()
        subjects.append("其他")  # 添加"其他"選項
        
        # 更新下拉選單
        self.subject_combobox['values'] = subjects
        if subjects:
            self.subject_combobox.current(0)
        
    def start_timer(self):
        """開始計時"""
        # 獲取自訂時間
        try:
            minutes = int(self.custom_time.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "請輸入有效的學習時間（正整數）！")
            return
            
        # 設定學習時間（分鐘轉秒）
        self.seconds_left = minutes * 60
        
        # 獲得當前學習科目
        self.current_subject = self.subject_var.get()
        if not self.current_subject:
            messagebox.showwarning("警告", "請選擇學習科目！")
            return
            
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.update_timer()

            if not self.is_break:
                self.session_type.set(f"學習中: {self.current_subject}")
                self.timer_label.configure(foreground=self.primary_color)
            else:
                self.session_type.set("休息中...")
                self.timer_label.configure(foreground="#4caf50")  # 綠色表示休息時間

    def pause_timer(self):
        """暫停計時"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            if self.timer_id:
                self.root.after_cancel(self.timer_id)

    def reset_timer(self):
        """重設計時"""
        self.pause_timer()
        self.is_break = False
        try:
            minutes = int(self.custom_time.get())  # 取得使用者輸入的自訂時間（分鐘）
            if minutes <= 0:
                minutes = 25
        except:
            minutes = 25  # 預設為計時 25 分鐘
        self.seconds_left = minutes * 60
        mins, secs = divmod(self.seconds_left, 60)
        self.time_left.set(f"{mins:02d}:{secs:02d}")
        self.session_type.set("準備開始")
        self.timer_label.configure(foreground=self.primary_color)

    def update_timer(self):
        """更新番茄鐘顯示"""
        if self.is_running and self.seconds_left > 0:
            mins, secs = divmod(self.seconds_left, 60)
            self.time_left.set(f"{mins:02d}:{secs:02d}")
            self.seconds_left -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.seconds_left == 0:
            self.timer_complete()

    def timer_complete(self):
        """計時完成時執行"""
        self.is_running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")

        if not self.is_break:
            # 學習階段完成
            self.sessions_completed += 1
            
            # 記錄學習時間
            study_minutes = int(self.custom_time.get())
            self.add_study_log(study_minutes, self.current_subject)
            
            # 獎勵Catcoins
            coins_earned = max(1, study_minutes // 5)  # 每5分鐘1個coin
            self.reward_catcoins(coins_earned)
            
            # 更新成就
            self.update_achievements(study_minutes)
            
            # 檢查徽章
            self.check_badges()
            
            # 增加寵物經驗值
            self.update_pet_xp(study_minutes // 5)  # 每5分鐘1點經驗
            
            # 設定休息時間
            self.is_break = True
            self.seconds_left = 5 * 60  # 5分鐘休息時間
            self.time_left.set("05:00")
            self.session_type.set("休息時間!")
            self.timer_label.configure(foreground="#4caf50")  # 綠色表示休息時間
        else:
            # 休息階段完成
            self.is_break = False
            try:
                minutes = int(self.custom_time.get())
                if minutes <= 0:
                    minutes = 25
            except:
                minutes = 25
            self.seconds_left = minutes * 60
            mins, secs = divmod(self.seconds_left, 60)
            self.time_left.set(f"{mins:02d}:{secs:02d}")
            self.session_type.set("準備學習")
            self.timer_label.configure(foreground=self.primary_color)

        # 播放提示音 (跨平台)
        play_sound()

    def add_study_log(self, minutes, subject):
        """添加學習記錄 - 修改版：累加相同科目在同一天的學習時間"""
        today = datetime.date.today().strftime("%Y-%m-%d")
    
        # 檢查是否已有當天該科目的記錄
        found = False
        for record in self.study_records:
            if record["date"] == today and record["subject"] == subject:
                record["minutes"] += minutes  # 累加時間
                found = True
                break
    
        # 如果沒有找到現有記錄，則新增一條
        if not found:
            self.study_records.append({
                "date": today,
                "subject": subject,
                "minutes": minutes
            })
    
        # 更新每日學習日誌（總時間）
        found = False
        for log in self.study_logs:
            if log["date"] == today:
                log["minutes"] += minutes
                found = True
                break

        if not found:
            self.study_logs.append({"date": today, "minutes": minutes})
        
        # 檢查是否完成每日學習計畫
        self.check_daily_goals(today, minutes, subject)

        self.save_data()
        self.update_progress_display()
        self.update_calendar()

    def check_daily_goals(self, date, minutes, subject):
        """檢查是否完成每日學習目標"""
        # 如果沒有學習計畫，則不檢查
        if not self.study_plan or date not in self.study_plan:
            return
            
        # 檢查該科目是否在當日計畫中
        for task in self.study_plan[date]:
            if task["subject"] == subject and not task["completed"]:
                # 標記為已完成
                task["completed"] = True
                
                # 獎勵Catcoins
                coins_earned = max(1, minutes // 10)  # 每10分鐘1個coin
                self.reward_catcoins(coins_earned)
                self.show_message(f"恭喜完成 {subject} 學習目標！獲得 {coins_earned} Catcoins")
                
                # 檢查是否完成所有當日目標
                all_completed = all(task["completed"] for task in self.study_plan[date])
                if all_completed:
                    self.reward_catcoins(10)  # 額外獎勵
                    self.show_message(f"恭喜完成所有今日學習目標！獲得額外 10 Catcoins")
                    
                # 更新日曆顯示
                self.update_calendar()
                break

    def update_achievements(self, minutes):
        """更新成就系統"""
        today = datetime.date.today()
        
        # 更新總學習時間
        self.achievements["total_study_hours"] += minutes / 60
        
        # 更新連續學習天數
        if self.achievements["last_study_date"]:
            last_date = datetime.datetime.strptime(self.achievements["last_study_date"], "%Y-%m-%d").date()
            if (today - last_date).days == 1:  # 連續學習
                self.achievements["consecutive_days"] += 1
            elif (today - last_date).days > 1:  # 中斷連續
                self.achievements["consecutive_days"] = 1
        else:  # 第一次學習
            self.achievements["consecutive_days"] = 1
            
        self.achievements["last_study_date"] = today.strftime("%Y-%m-%d")
        
        # 更新完成目標數
        self.achievements["completed_goals"] += 1
        
        # 保存數據
        self.save_data()

    def reward_catcoins(self, amount):
        """獎勵Catcoins"""
        self.catcoins += amount
        self.save_data()
        self.update_progress_display()
        self.catcoins_header.config(text=f"Catcoins: {self.catcoins}")

    def update_pet_xp(self, xp):
        """更新寵物經驗值"""
        self.pet_status["xp"] += xp
        # 每100經驗值升一級
        if self.pet_status["xp"] >= 100:
            self.pet_status["level"] += 1
            self.pet_status["xp"] = 0
            self.show_message(f"恭喜! 你的貓升到 {self.pet_status['level']} 級了!")
        self.save_data()
        self.update_pet_status()

    def setup_pet_page(self):
        """設定虛擬寵物頁面"""
        # 設定頁面背景
        self.pet_page.configure(style="Background.TFrame")
    
        # 主容器框架
        main_frame = ttk.Frame(self.pet_page, style="Background.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
        # 左側框架 - 寵物狀態和互動
        left_frame = ttk.Frame(main_frame, style="Background.TFrame")
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
    
        # 右側框架 - 寵物顯示和商店
        right_frame = ttk.Frame(main_frame, style="Background.TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
    
        # 寵物狀態顯示
        self.pet_status_frame = ttk.LabelFrame(
            left_frame, 
            text="🐾 寵物狀態", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        self.pet_status_frame.pack(fill="x", pady=5)
    
        # 愉悅值 - 使用進度條顯示
        ttk.Label(self.pet_status_frame, text="愉悅值:", style="Card.TLabel").pack(anchor="w")
        self.pet_happiness = ttk.Progressbar(
            self.pet_status_frame,
            orient="horizontal",
            length=200,
            mode="determinate"
        )
        self.pet_happiness.pack(fill="x", pady=2)
    
        # 能量 - 使用進度條顯示
        ttk.Label(self.pet_status_frame, text="能量:", style="Card.TLabel").pack(anchor="w")
        self.pet_energy = ttk.Progressbar(
            self.pet_status_frame,
            orient="horizontal",
            length=200,
            mode="determinate"
        )
        self.pet_energy.pack(fill="x", pady=2)
    
        # 等級和經驗值
        self.pet_level = ttk.Label(
            self.pet_status_frame, 
            text=f"等級: {self.pet_status['level']} (經驗: {self.pet_status['xp']}/100)",
            style="Card.TLabel"
        )
        self.pet_level.pack(pady=5)
    
        # 寵物互動按鈕
        self.pet_interaction_frame = ttk.LabelFrame(
            left_frame, 
            text="🐱 與寵物互動", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        self.pet_interaction_frame.pack(fill="x", pady=5)
    
        btn_frame = ttk.Frame(self.pet_interaction_frame, style="Background.TFrame")
        btn_frame.pack(fill="x")
    
        ttk.Button(
            btn_frame, 
            text="🍗 餵食", 
            command=lambda: self.interact_with_pet("feed"),
            style="Accent.TButton"
        ).pack(side="left", fill="x", expand=True, padx=2)
    
        ttk.Button(
            btn_frame, 
            text="🎾 玩耍", 
            command=lambda: self.interact_with_pet("play"),
            style="Accent.TButton"
        ).pack(side="left", fill="x", expand=True, padx=2)
    
        ttk.Button(
            btn_frame, 
            text="🧼 清潔", 
            command=lambda: self.interact_with_pet("clean"),
            style="Accent.TButton"
        ).pack(side="left", fill="x", expand=True, padx=2)
    
        # 寵物商店
        self.pet_shop_frame = ttk.LabelFrame(
            left_frame, 
            text="🛒 寵物商店", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )   
        self.pet_shop_frame.pack(fill="x", pady=5)
    
        self.catcoins_label = ttk.Label(
            self.pet_shop_frame, 
            text=f"💰 Catcoins: {self.catcoins}",
            style="Card.TLabel"
        )
        self.catcoins_label.pack()
    
        # 商店商品
        self.shop_items = [
            {"name": "⚽ 小球", "cost": 20, "effect": "happiness", "value": 15, "image": "ball"},
            {"name": "🧣 新項圈", "cost": 50, "effect": "happiness", "value": 25, "image": "collar"},
            {"name": "🍣 高級食物", "cost": 30, "effect": "energy", "value": 20, "image": "food"},
            {"name": "🏠 小房子", "cost": 100, "effect": "level", "value": 1, "image": "house"},
            {"name": "📚 經驗書", "cost": 40, "effect": "xp", "value": 50, "image": "book"}
        ]
    
        for item in self.shop_items:
            item_frame = ttk.Frame(self.pet_shop_frame, style="Background.TFrame")
            item_frame.pack(fill="x", pady=2)
            
            # 商品圖標（使用預設圖標）
            icon_label = ttk.Label(item_frame, text=item["image"], font=("Arial", 14))
            icon_label.pack(side="left", padx=5)
            
            # 商品資訊
            ttk.Label(
                item_frame, 
                text=f"{item['name']} - {item['cost']} Catcoins",
                style="Card.TLabel"
            ).pack(side="left", padx=5)
            
            # 購買按鈕
            ttk.Button(
                item_frame,
                text="購買",
                command=lambda i=item: self.buy_item(i),
                style="Primary.TButton",
                width=5
            ).pack(side="right", padx=5)
    
        # 寵物顯示區域
        pet_display_frame = ttk.LabelFrame(
            right_frame, 
            text="我的貓咪", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        pet_display_frame.pack(fill="both", expand=True, pady=5)
    
        # 使用Label顯示高品質貓咪圖片
        self.pet_image_label = tk.Label(
            pet_display_frame, 
            bg=self.background_color
        )
        self.pet_image_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 載入貓咪圖片
        self.load_pet_images()
        
        # 初始化寵物狀態
        self.update_pet_status()

    def load_pet_images(self):
        """載入貓咪圖片資源"""
        try:
             # 使用跨平台路徑
            img_dir = get_app_data_folder("SmartStudyImages")
    
            # 正常狀態貓咪
            normal_img = Image.open(os.path.join(img_dir, "cat_normal.png"))
            normal_img = normal_img.resize((300, 300), Image.LANCZOS)
            self.pet_images["normal"] = ImageTk.PhotoImage(normal_img)
            
            # 開心狀態貓咪
            happy_img = Image.open(os.path.join(img_dir, "cat_happy.png"))
            happy_img = happy_img.resize((300, 300), Image.LANCZOS)
            self.pet_images["happy"] = ImageTk.PhotoImage(happy_img)
            
            # 不開心狀態貓咪
            sad_img = Image.open(os.path.join(img_dir, "cat_sad.png"))
            sad_img = sad_img.resize((300, 300), Image.LANCZOS)
            self.pet_images["sad"] = ImageTk.PhotoImage(sad_img)
            
            # 睏倦狀態貓咪
            sleepy_img = Image.open(os.path.join(img_dir, "cat_sleepy.png"))
            sleepy_img = sleepy_img.resize((300, 300), Image.LANCZOS)
            self.pet_images["sleepy"] = ImageTk.PhotoImage(sleepy_img)
        except Exception as e:
            print(f"無法載入貓咪圖片: {e}")
            # 使用預設圖片
            self.pet_images = {
                "normal": None,
                "happy": None,
                "sad": None,
                "sleepy": None
            }

    def interact_with_pet(self, action):
        """與寵物互動"""  
        if action == "feed":  # 餵食貓咪提升能量(最大值 = 100)
            self.pet_status["energy"] = min(100, self.pet_status["energy"] + 20)
            self.show_message("你的貓吃了食物，能量增加了!")
        elif action == "play":  # 和貓咪玩提升愉悅值(最大值 = 100)
            self.pet_status["happiness"] = min(100, self.pet_status["happiness"] + 15)
            self.pet_status["energy"] = max(0, self.pet_status["energy"] - 10)
            self.show_message("你和貓玩耍，牠變得更開心了!")
        elif action == "clean":  # 打掃貓咪環境提升愉悅值(最大值 = 100)
            self.pet_status["happiness"] = min(100, self.pet_status["happiness"] + 10)
            self.show_message("你打掃了貓的環境，牠感覺更舒服了!")

        self.update_pet_status()
        self.save_data()

    def buy_item(self, item):
        """購買商店物品"""
        if self.catcoins >= item["cost"]:
            self.catcoins -= item["cost"]
            if item["effect"] == "happiness":
                self.pet_status["happiness"] = min(100, self.pet_status["happiness"] + item["value"])
                self.show_message(f"你購買了{item['name']}，貓的愉悅值增加了 {item['value']}!")
            elif item["effect"] == "energy":
                self.pet_status["energy"] = min(100, self.pet_status["energy"] + item["value"])
                self.show_message(f"你購買了{item['name']}，貓的能量增加了 {item['value']}!")
            elif item["effect"] == "level":
                self.pet_status["level"] += item["value"]
                self.show_message(f"你購買了{item['name']}，貓的等級提升了!")
            elif item["effect"] == "xp":
                self.pet_status["xp"] += item["value"]
                # 檢查是否升級
                if self.pet_status["xp"] >= 100:
                    self.pet_status["level"] += 1
                    self.pet_status["xp"] = 0
                    self.show_message(f"恭喜! 你的貓升到 {self.pet_status['level']} 級了!")
                self.show_message(f"你購買了{item['name']}，貓的經驗值增加了 {item['value']}!")

            self.update_pet_status()
            self.save_data()
        else:
            self.show_message(f"Catcoins不足! 需要 {item['cost']} Catcoins，但你只有 {self.catcoins}。")

    def update_pet_status(self):
        """更新寵物狀態顯示"""
        self.pet_happiness["value"] = self.pet_status["happiness"]  # 使用進度條顯示愉悅值
        self.pet_energy["value"] = self.pet_status["energy"]  # 使用進度條顯示能量
        self.pet_level.config(text=f"等級: {self.pet_status['level']} (經驗: {self.pet_status['xp']}/100)")
        self.catcoins_label.config(text=f"💰 Catcoins: {self.catcoins}")  
        self.catcoins_header.config(text=f"Catcoins: {self.catcoins}")   # 更新Catcoins的即時數量 
        
        # 根據寵物狀態選擇合適的圖片
        happiness = self.pet_status["happiness"]
        energy = self.pet_status["energy"]
        
        if happiness < 30:
            image_key = "sad"
        elif happiness > 70 and energy > 70:
            image_key = "happy"
        elif energy < 30:
            image_key = "sleepy"
        else:
            image_key = "normal"
        
        # 更新寵物圖片
        if self.pet_images.get(image_key):
            self.pet_image_label.config(image=self.pet_images[image_key])
            self.pet_image_label.image = self.pet_images[image_key]  # 保持參考

    def setup_calendar_page(self):
        """設定學習計畫日曆頁面"""
        # 設定頁面背景
        self.calendar_page.configure(style="Background.TFrame")

        # 主容器框架 - 改用 grid 布局
        main_frame = ttk.Frame(self.calendar_page, style="Background.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 分配 grid 權重 - 調整權重分配
        main_frame.grid_rowconfigure(0, weight=0)  # 控制按鈕行（固定高度）
        main_frame.grid_rowconfigure(1, weight=2)  # 日曆區域（減少權重）
        main_frame.grid_rowconfigure(2, weight=3)  # 詳情區域（調整權重比例）
        main_frame.grid_columnconfigure(0, weight=1)

        # 日曆控制框架 (移到第0行)
        control_frame = ttk.Frame(main_frame, style="Background.TFrame")
        control_frame.grid(row=0, column=0, sticky="ew", pady=5)

        # 月份導航按鈕
        ttk.Button(
            control_frame, 
            text="◀ 上個月", 
            command=self.prev_month,
            style="Accent.TButton"
        ).pack(side="left", padx=5)

        # 建立字串變數用來顯示目前的年月
        self.month_year_var = tk.StringVar()
        self.month_year_label = ttk.Label(
            control_frame, 
            textvariable=self.month_year_var,
            font=self.title_font,
            style="Background.TLabel"
        )
        self.month_year_label.pack(side="left", padx=10)

        # 切換到下個月的按鈕
        ttk.Button(
            control_frame, 
            text="下個月 ▶", 
            command=self.next_month,
            style="Accent.TButton"
        ).pack(side="left", padx=5)

        # 日曆顯示框架 - 增加 sticky="nsew" 讓它可擴展
        self.calendar_frame = ttk.Frame(main_frame, style="Background.TFrame")
        self.calendar_frame.grid(row=1, column=0, sticky="nsew", pady=5)

        # 學習計畫詳情框架 - 調整高度和 sticky 設定
        detail_frame = ttk.LabelFrame(
            main_frame, 
            text="📝 學習計畫詳情", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        detail_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))  # 調整下方間距

        # 調整 Text 組件的高度和 pack 設定
        self.plan_detail = tk.Text(
            detail_frame, 
            height=10,  # 稍微減少行數
            wrap="word",
            font=self.label_font,
            bg="white",
            relief="flat"
        )
        # 使用 fill 和 expand 確保完整顯示
        self.plan_detail.pack(fill="both", expand=True, padx=5, pady=5)
        self.plan_detail.insert("end", "選擇日期查看學習計畫詳情")
        self.plan_detail.config(state="disabled")

        # 初始化當前月份
        self.current_date = datetime.date.today()
        self.update_calendar()

    def update_calendar(self):
        """更新日曆顯示"""
        # 清除舊的日曆
        for widget in self.calendar_frame.winfo_children():
         widget.destroy()
    
        # 設置當前月份和年份
        self.month_year_var.set(f"{self.current_date.year}年{self.current_date.month}月")
    
        # 獲取當月的第一天和天數
        first_day, num_days = calendar.monthrange(self.current_date.year, self.current_date.month)
    
        # 創建星期標題
        days = ["一", "二", "三", "四", "五", "六", "日"]
        for i, day in enumerate(days):
            label = ttk.Label(
                self.calendar_frame, 
                text=day, 
                style="Card.TLabel",
                width=10,
                anchor="center"
            )
            label.grid(row=0, column=i, padx=2, pady=1)  # 減少 pady 值
    
        # 填充日曆
        row, col = 1, 0
        today = datetime.date.today()
    
        # 填充空白
        for _ in range(first_day):
            frame = ttk.Frame(self.calendar_frame, width=100, height=60, style="Background.TFrame")  # 減少高度
            frame.grid(row=row, column=col, padx=2, pady=1)  # 減少 pady 值
            col += 1
    
        # 填充日期
        for day in range(1, num_days + 1):
            date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
            date_obj = datetime.date(self.current_date.year, self.current_date.month, day)
        
            # 創建日期框架（包含按鈕和學習時間）
            date_frame = ttk.Frame(self.calendar_frame, width=100, height=60, style="Background.TFrame")  # 減少高度
            date_frame.grid(row=row, column=col, padx=2, pady=1, sticky="nsew")  # 減少 pady 值
            date_frame.grid_propagate(False)  # 防止內部組件改變框架大小
        
            # 日期按鈕
            date_btn = ttk.Button(
                date_frame, 
                text=str(day),
                command=lambda d=date_str: self.show_plan_detail(d),
                style="Primary.TButton" if date_obj == today else "Accent.TButton",
                width=3
            )
            date_btn.grid(row=0, column=0, sticky="nw", padx=2, pady=1)  # 減少 pady 值
        
            # 顯示學習時間（如果有）
            study_time = self.get_daily_study_time(date_str)
            if study_time > 0:
                time_label = ttk.Label(
                    date_frame, 
                    text=f"{study_time}分鐘",
                    font=("Arial", 8),
                    style="Card.TLabel",
                    background="#e0f7fa"
                )   
                time_label.grid(row=1, column=0, sticky="se", padx=2, pady=1)  # 減少 pady 值
        
            # 如果有學習計畫，添加標記
            if date_str in self.study_plan:
                # 檢查讀書計畫是否全部完成
                all_completed = all(task["completed"] for task in self.study_plan[date_str])
                if all_completed:
                    date_btn.config(style="Primary.TButton")
                else:
                    plan_label = ttk.Label(
                        date_frame,
                        text="📝",  # 表示還有該念的沒念
                        font=("Arial", 10),
                        style="Card.TLabel"
                    )
                    plan_label.grid(row=0, column=0, sticky="ne", padx=2, pady=1)  # 減少 pady 值
        
            # 控制排版：每排 7 個（即代表一週），超過就換行
            col += 1
            if col == 7:
                col = 0
                row += 1

    def get_daily_study_time(self, date_str):
        """獲得指定日期的學習時間"""
        total_minutes = 0
        for record in self.study_records:
            if record["date"] == date_str:
                total_minutes += record["minutes"]
        return total_minutes  # 回傳當天總共學習多久(單位:分鐘)

    def prev_month(self):
        """切換到上個月"""
        self.current_date = self.current_date.replace(day=1)   # 日期設定為當月1日(避免跨月份出錯)
        self.current_date -= datetime.timedelta(days=1)  # 退一天進入上個月
        self.current_date = self.current_date.replace(day=1)  # 再設定為上個月的1日
        self.update_calendar()

    def next_month(self):
        """切換到下個月"""
        self.current_date = self.current_date.replace(day=28) + datetime.timedelta(days=4)
        self.current_date = self.current_date.replace(day=1)
        self.update_calendar()

    def show_plan_detail(self, date_str):
        """顯示所選日期的學習計畫詳情"""
        self.plan_detail.config(state="normal")
        self.plan_detail.delete("1.0", "end")
        
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")  # 將日期字串轉換為 datetime 物件
            self.plan_detail.insert("end", f"{date_obj.year}年{date_obj.month}月{date_obj.day}日 學習計畫:\n\n")
            
            # 顯示學習計畫
            if date_str in self.study_plan:
                for i, task in enumerate(self.study_plan[date_str], 1):
                    status = "✓" if task["completed"] else "✗"
                    color = "green" if task["completed"] else "red"  # 根據完成狀態顯示 ✓ 或 ✗，同時決定顏色
                    self.plan_detail.insert("end", f"{i}. {task['subject']} - {task['time']}分鐘 ")
                    self.plan_detail.insert("end", f"{status}\n", f"status_{color}")
            else:
                self.plan_detail.insert("end", "當日沒有安排學習計畫\n")
            
            # 顯示實際學習記錄
            daily_records = [r for r in self.study_records if r["date"] == date_str]  
            if daily_records:
                self.plan_detail.insert("end", f"\n實際學習記錄:\n")
                total_minutes = 0
                for record in daily_records:
                    self.plan_detail.insert("end", f"- {record['subject']}: {record['minutes']}分鐘\n")  # 列出讀的科目與花費時間
                    total_minutes += record["minutes"]
                self.plan_detail.insert("end", f"\n總學習時間: {total_minutes}分鐘")
            else:
                self.plan_detail.insert("end", "\n當日沒有學習記錄")
        except:
            self.plan_detail.insert("end", "日期格式錯誤")
        
        self.plan_detail.config(state="disabled")  # 鎖住文字框內容，不可編輯
        
        # 添加文字標籤樣式
        self.plan_detail.tag_config("status_green", foreground="green")
        self.plan_detail.tag_config("status_red", foreground="red")

    def setup_progress_page(self):
        """設定學習進度頁面"""
        # 設定頁面背景
        self.progress_page.configure(style="Background.TFrame")
        
        # 主容器框架
        main_frame = ttk.Frame(self.progress_page, style="Background.TFrame")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左側框架 - 統計數據和徽章
        left_frame = ttk.Frame(main_frame, style="Background.TFrame")
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # 右側框架 - 圖表
        right_frame = ttk.Frame(main_frame, style="Background.TFrame")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 學習統計數據
        stats_frame = ttk.LabelFrame(
            left_frame, 
            text="📈 學習統計", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        stats_frame.pack(fill="x", pady=5)
        
        self.total_study_time = ttk.Label(
            stats_frame, 
            text="總學習時間: 0分鐘",
            style="Card.TLabel"
        )
        self.total_study_time.pack(anchor="w", pady=2)
        
        self.total_sessions = ttk.Label(
            stats_frame, 
            text="完成學習次數: 0",
            style="Card.TLabel"
        )
        self.total_sessions.pack(anchor="w", pady=2)
        
        self.catcoins_earned = ttk.Label(
            stats_frame, 
            text="獲得的Catcoins: 0",
            style="Card.TLabel"
        )
        self.catcoins_earned.pack(anchor="w", pady=2)
        
        self.consecutive_days = ttk.Label(
            stats_frame, 
            text="連續學習天數: 0",
            style="Card.TLabel"
        )
        self.consecutive_days.pack(anchor="w", pady=2)
        
        self.completed_goals = ttk.Label(
            stats_frame, 
            text="完成學習目標: 0",
            style="Card.TLabel"
        )
        self.completed_goals.pack(anchor="w", pady=2)
        
        # 徽章展示
        badges_frame = ttk.LabelFrame(
            left_frame, 
            text="🏆 獲得的徽章", 
            padding=(10, 5),
            style="Card.TLabelframe"
        )
        badges_frame.pack(fill="both", expand=True, pady=5)
        
        self.badges_display = tk.Text(
            badges_frame, 
            height=5, 
            wrap="word",
            font=self.label_font,
            bg="white",
            relief="flat"
        )
        self.badges_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.badges_display.insert("end", "尚未獲得任何徽章")
        self.badges_display.config(state="disabled")
        
        # 學習進度圖表
        chart_frame = ttk.LabelFrame(
            right_frame, 
            text="📊 學習進度圖表", 
            padding=(10, 5),
            style="Card.TLabelframe"  # 修正拼寫錯誤
        )
        chart_frame.pack(fill="both", expand=True, pady=5)
        
        # 創建圖表框架
        self.figure = plt.Figure(figsize=(8, 6), dpi=100, facecolor=self.background_color)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)  # 改良背景色
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # 更新顯示
        self.update_progress_display()

    def check_daily_achievements(self):
        """檢查每日成就"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # 檢查是否已經學習過
        has_studied = any(log["date"] == today for log in self.study_logs)
        
        if has_studied:
            # 檢查每日學習成就
            daily_minutes = next((log["minutes"] for log in self.study_logs if log["date"] == today), 0)
            
            if daily_minutes >= 60:  # 學習超過60分鐘
                if "daily_60min" not in self.badges:
                    self.badges.append("daily_60min")
                    self.reward_catcoins(15)
                    self.show_message("恭喜獲得成就: 今日學習達60分鐘! 獲得15 Catcoins")
            
            if daily_minutes >= 120:  # 學習超過120分鐘
                if "daily_120min" not in self.badges:
                    self.badges.append("daily_120min")
                    self.reward_catcoins(30)
                    self.show_message("恭喜獲得成就: 今日學習達120分鐘! 獲得30 Catcoins")
        
        # 保存數據
        self.save_data()
        self.update_progress_display()
    
    # 成就徽章系統
    def check_badges(self):
        """檢查並授予成就徽章"""
        badges = [
            {"name": "初學者", "condition": lambda: self.achievements["total_study_hours"] >= 5, "earned": False},
            {"name": "學習達人", "condition": lambda: self.achievements["total_study_hours"] >= 20, "earned": False},
            {"name": "學霸", "condition": lambda: self.achievements["total_study_hours"] >= 50, "earned": False},
            {"name": "連續學習3天", "condition": lambda: self.achievements["consecutive_days"] >= 3, "earned": False},
            {"name": "連續學習7天", "condition": lambda: self.achievements["consecutive_days"] >= 7, "earned": False},
            {"name": "連續學習30天", "condition": lambda: self.achievements["consecutive_days"] >= 30, "earned": False},
            {"name": "完成10個目標", "condition": lambda: self.achievements["completed_goals"] >= 10, "earned": False},
            {"name": "完成50個目標", "condition": lambda: self.achievements["completed_goals"] >= 50, "earned": False},
            {"name": "貓咪愛好者", "condition": lambda: self.pet_status["level"] >= 3, "earned": False},
            {"name": "貓咪大師", "condition": lambda: self.pet_status["level"] >= 5, "earned": False}
        ]

        new_badges = []

        for badge in badges:
            if badge["condition"]() and badge["name"] not in self.badges:
                self.badges.append(badge["name"])  # 將新獲得的徽章加到使用者的徽章列表
                new_badges.append(badge["name"])
                # 獎勵Catcoins
                self.reward_catcoins(20)

        if new_badges:
            self.show_message(f"恭喜獲得新徽章: {', '.join(new_badges)}! 獲得20 Catcoins")
            self.save_data()
            self.update_progress_display()

    def update_progress_display(self):
        """更新進度頁面顯示"""
        # 更新統計數據
        total_minutes = sum(log["minutes"] for log in self.study_logs)
        self.total_study_time.config(text=f"總學習時間: {total_minutes}分鐘")
        self.total_sessions.config(text=f"完成學習次數: {self.sessions_completed}")
        self.catcoins_earned.config(text=f"獲得的Catcoins: {self.catcoins}")
        self.consecutive_days.config(text=f"連續學習天數: {self.achievements['consecutive_days']}")
        self.completed_goals.config(text=f"完成學習目標: {self.achievements['completed_goals']}")
        self.catcoins_header.config(text=f"Catcoins: {self.catcoins}")

        # 更新徽章顯示
        self.badges_display.config(state="normal")
        self.badges_display.delete("1.0", "end")
        if self.badges:
            self.badges_display.insert("end", "\n".join(f"🏅 {badge}" for badge in self.badges))
        else:
            self.badges_display.insert("end", "尚未獲得任何徽章")
        self.badges_display.config(state="disabled")

        # 更新圖表
        self.update_chart()

    def update_chart(self):
        """更新學習進度圖表 - 修改版：在右上角顯示顏色圖標與科目對照"""
        self.figure.clear()

        if not self.study_records:
            ax = self.figure.add_subplot(111, facecolor=self.background_color)
            ax.text(0.5, 0.5, "尚無學習數據", ha="center", va="center", color=self.text_color)
            self.canvas.draw()
            return

        # 準備數據（最近7天）
        dates = []
        subjects_data = {}
        today = datetime.date.today()

        for i in range(6, -1, -1):
            date = today - datetime.timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            dates.append(date.strftime("%m-%d"))

            daily_records = [r for r in self.study_records if r["date"] == date_str]

            for record in daily_records:
                subject = record["subject"]
                if subject not in subjects_data:
                    subjects_data[subject] = [0] * 7
                subjects_data[subject][6-i] = record["minutes"]

        ax = self.figure.add_subplot(111, facecolor=self.background_color)

        # 設定圖表樣式
        ax.tick_params(axis='x', colors=self.text_color)
        ax.tick_params(axis='y', colors=self.text_color)
        ax.spines['bottom'].set_color(self.text_color)
        ax.spines['top'].set_color(self.text_color) 
        ax.spines['right'].set_color(self.text_color)
        ax.spines['left'].set_color(self.text_color)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        ax.title.set_color(self.text_color)

        # 繪製堆疊柱狀圖
        bottom = [0] * 7
        colors = plt.cm.tab20.colors

        # 計算總學習時間並排序科目（從大到小）
        subject_totals = {subject: sum(minutes) for subject, minutes in subjects_data.items()}
        sorted_subjects = sorted(subject_totals.items(), key=lambda x: -x[1])

        # 繪製柱狀圖並收集科目顏色對照
        color_map = {}
        patches = []  # 用於存儲圖例句柄
        for i, (subject, total) in enumerate(sorted_subjects):
            color = colors[i % len(colors)]
            color_map[subject] = color
            minutes = subjects_data[subject]
            bar = ax.bar(dates, minutes, bottom=bottom, color=color, label=subject)
            bottom = [b + m for b, m in zip(bottom, minutes)]
            patches.append(bar[0])  # 添加第一個矩形到圖例句柄

        ax.set_title("每日學習時間（按科目分類，最近7天）", color=self.text_color)
        ax.set_xlabel("日期", color=self.text_color)
        ax.set_ylabel("分鐘", color=self.text_color)
        ax.tick_params(axis='x', rotation=45, colors=self.text_color)
        ax.tick_params(axis='y', colors=self.text_color)

        ax.grid(True, linestyle='--', alpha=0.5, color=self.text_color, axis='y')

        # 創建圖例
        if patches:  # 只有當有數據時才創建圖例
            # 調整圖例位置在圖表外右側
            legend = ax.legend(
                handles=patches,
                labels=[subject for subject, _ in sorted_subjects],
                bbox_to_anchor=(1, 1),
                loc='upper left',
                borderaxespad=0.,
                frameon=False,
                handlelength=0.5,  # 調整顏色方塊長度
                handletextpad=0.5,  # 調整方塊與文字間距
                fontsize='small'    # 調整文字大小
            )

            # 設置圖例文字顏色
            for text in legend.get_texts():
                text.set_color(self.text_color)

        # 調整圖表佈局，為圖例留出空間
        plt.tight_layout(rect=[0, 0, 0.85, 1])  # 右側留出15%空間

        self.canvas.draw()

    def show_message(self, message):
        """顯示訊息對話框"""
        messagebox.showinfo("訊息", message)

    def save_data(self):
        """保存所有數據到文件"""
        # 使用跨平台路徑
        data_dir = get_app_data_folder("SmartStudyData")
        data_file = os.path.join(data_dir, "smartstudy_data.json")
        
        data = {
            "courses": self.courses,
            "exams": self.exams,
            "study_logs": self.study_logs,
            "study_records": self.study_records,
            "catcoins": self.catcoins,
            "badges": self.badges,
            "pet_status": self.pet_status,
            "sessions_completed": self.sessions_completed,
            "achievements": self.achievements,
            "study_plan": self.study_plan
        }

        try:
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存數據時出錯: {e}")

    def load_data(self):
        """從文件載入數據"""
        # 使用跨平台路徑
        data_dir = get_app_data_folder("SmartStudyData")
        data_file = os.path.join(data_dir, "smartstudy_data.json")
        
        try:
            if os.path.exists(data_file):
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    self.courses = data.get("courses", [])
                    self.exams = data.get("exams", [])
                    self.study_logs = data.get("study_logs", [])
                    self.study_records = data.get("study_records", [])
                    self.catcoins = data.get("catcoins", 0)
                    self.badges = data.get("badges", [])
                    self.pet_status = data.get("pet_status", {"happiness": 50, "energy": 50, "level": 1, "xp": 0})
                    self.sessions_completed = data.get("sessions_completed", 0)
                    self.achievements = data.get("achievements", {
                        "consecutive_days": 0,
                        "total_study_hours": 0,
                        "completed_goals": 0,
                        "last_study_date": None
                    })
                    self.study_plan = data.get("study_plan", {})
        except Exception as e:
            print(f"載入數據時出錯: {e}")
        finally:
            # 確保所有必要的字段都存在
            if "xp" not in self.pet_status:
                self.pet_status["xp"] = 0

if __name__ == "__main__":
    try:
        from ttkthemes import ThemedTk
        root = ThemedTk(theme="arc")
        root.set_theme_advanced("arc", brightness=1.0, saturation=0.5, preserve_transparency=True)
    except:
        root = tk.Tk()
    
    root.title("SmartStudy - 智慧學習助手")
    app = SmartStudyApp(root)
    root.mainloop()