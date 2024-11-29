from tkinter import  messagebox, ttk
import customtkinter as ctk
from PIL import Image
from call_api import *
import time, threading, requests, psutil, socket

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

log_list = []
# base_url = 'http://172.16.0.15:5001'
base_url = 'https://flask-webserver-e07c23893a36.herokuapp.com'


def confirm_exit(app):
    response = messagebox.askyesno(
        "Tắt server", "Bạn có chắc chắn muốn tắt server?")
    if response:
        app.quit()


class App(ctk.CTk):
    def __init__(self, log_list):
        super().__init__()
        self.WIDTH = self.winfo_screenwidth()
        self.HEIGHT = self.winfo_screenheight()
        self.geometry(f'{self.WIDTH}x{self.HEIGHT}+0+0')

        # header
        self.header = HeaderFrame(master=self)

        # sider
        self.sider = SiderFrame(
            master=self, navigate_callback=self.navigate_to_frame)

        # body
        self.body = BodyFrame(master=self, log_list=log_list)

        # Placing widgets
        self.header.place(relx=0.01, rely=0.02, relwidth=0.98, relheight=0.13)
        self.sider.place(relx=0.01, rely=0.17, relwidth=0.2, relheight=0.82)
        self.body.place(relx=0.22, rely=0.17, relwidth=0.77, relheight=0.82)

        # Default view
        self.navigate_to_frame("dashboard")

    def navigate_to_frame(self, frame_name):
        # Hide all frames
        for frame in self.body.frames.values():
            frame.pack_forget()

        # Show the selected frame
        selected_frame = self.body.frames.get(frame_name)
        if selected_frame:
            selected_frame.pack(fill="both", expand=True)


class HeaderFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color='#768FCF')
        # Server Logo
        self.server_logo = self.logo_title()
        self.server_logo.pack(side=ctk.LEFT)
        # Shut down Button
        self.shutdown = self.shut_btn(master)
        self.shutdown.pack(side=ctk.RIGHT)

        # refresh button
        # self.refresh = self.refresh_btn()
        # self.refresh.pack(side=ctk.RIGHT)

    def logo_title(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        image = ctk.CTkImage(Image.open(
            "server/icons/server.png"), size=(70, 70))
        label = ctk.CTkLabel(frame, image=image, text="")
        label.pack(side=ctk.LEFT, padx=5)
        title = ctk.CTkLabel(frame, text="Todo Server",
                             font=("Arial", 20), text_color='black')
        title.pack(side=ctk.LEFT, padx=5)
        return frame


    def shut_btn(self, app):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        image = ctk.CTkImage(Image.open(
            "server/icons/restart.png"), size=(50, 50))
        button = ctk.CTkButton(frame, image=image, text="",
                               fg_color="transparent", command=lambda: confirm_exit(app))
        label = ctk.CTkLabel(frame, text="Shut down",
                             font=("Arial", 18), text_color='black')
        button.pack(padx=0, pady=0)
        label.pack(padx=0, pady=0)
        return frame


class SiderFrame(ctk.CTkFrame):
    def __init__(self, master, navigate_callback):
        super().__init__(master, corner_radius=10, fg_color='#768FCF')
        self.navigate_callback = navigate_callback

        # Dashboard
        self.dashboard = self.create_button(
            "Dashboard", "server/icons/dashboard.png", "dashboard")
        self.dashboard.pack(fill="x", anchor=ctk.W, padx=10)
        # Requests
        self.requests = self.create_button(
            "Requests", "server/icons/terminal.png", "requests")
        self.requests.pack(fill="x", anchor=ctk.W, padx=10)
        # Users
        self.users = self.create_button(
            "Users", "server/icons/group.png", "users")
        self.users.pack(fill="x", anchor=ctk.W, padx=10)

    def create_button(self, text, icon_path, frame_name):
        frame = ctk.CTkFrame(self, fg_color='transparent', corner_radius=10)
        image = ctk.CTkImage(Image.open(icon_path), size=(45, 45))
        button = ctk.CTkButton(
            frame, image=image, text="", width=45, height=45, fg_color='transparent',
            command=lambda: self.navigate_callback(frame_name)
        )
        label = ctk.CTkLabel(frame, text=text, font=(
            "Aria", 18), text_color='black')
        button.pack(fill="x", side=ctk.LEFT, padx=10, pady=10)
        label.pack(fill="x", side=ctk.LEFT)
        return frame


class BodyFrame(ctk.CTkFrame):
    def __init__(self, master, log_list):
        super().__init__(master, corner_radius=10, fg_color='transparent')
        # Create frame instances and store them in a dictionary for easy access
        self.frames = {
            "requests": Requests_Frame(self, log_list),
            "users": Users_Frame(self),
            "dashboard": Dashboard_Frame(self),
        }


class Dashboard_Frame(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color='#cfe1b9')

        self.frame = self.dashFrame(self)
        self.frame.pack(fill='both')
        # Tạo và bắt đầu luồng cập nhật request rate mỗi giây
        self.threads = []
        self.threads.append(threading.Thread(target=self.update_request_rate, daemon=True))
        self.threads.append(threading.Thread(target=update_system_info, args=(self,), daemon=True))
        # self.threads.append(threading.Thread(target=self.update_data, daemon=True))
        for thread in self.threads:
            thread.start()

    def update_request_rate(self):
        """Cập nhật tỷ lệ request mỗi giây"""
        while True:
            time.sleep(1)  # Chờ 1 giây

            try:
                # Lấy dữ liệu mới từ API hoặc nguồn dữ liệu
                hosts = get_all_host()  # Hàm này giả định trả về danh sách hosts

                # Tính toán tỷ lệ mới
                success_rate, fail_rate = self.calculate_overall_success_rate(
                    hosts)

                # Cập nhật giao diện Success Request
                self.success_rate.winfo_children()[0].configure(
                    text=f"Success Request: {round(success_rate, 2)}%"
                )

                # Cập nhật giao diện Fail Request
                self.fail_rate.winfo_children()[0].configure(
                    text=f"Fail Request: {round(fail_rate, 2)}%"
                )
                print("Dashboard updated!")

            except Exception as e:
                print(f"Error during refresh: {e}")


    def dashFrame(self, master):
        frame = ctk.CTkFrame(master, fg_color='transparent')
        # System information
        sys_info_title = self.titleLabel(frame, "System Information")
        sys_info_title.pack(fill='both', padx=20, pady=10)

        system_info = get_system_info()  # API call hoặc hàm hệ thống
        user_quantity = getUsers()
        task_quantity = getTasks()

        task_quantity_list = task_quantity.get("Tasks list", [])  # Sử dụng key phù hợp
        # task_quantity_list = task_quantity  # Sử dụng key phù hợp

        done_tasks = [task for task in task_quantity_list if task["status"] == "COMPLETED"]
        doing_tasks = [task for task in task_quantity_list if task["status"] == "IN_PROGRESS"]
        todo_tasks = [task for task in task_quantity_list if task["status"] == "TODO"]

        # Lấy số lg ng dùng on, off
        online_users = sum(1 for user in user_quantity if user.get("isOnline"))
        offline_users = len(user_quantity) - online_users


        if system_info:

            # Frame chứa CPU và RAM
            sys_info_row1 = ctk.CTkFrame(frame, fg_color='transparent')
            sys_info_row1.pack(fill='x', padx=100, pady=10)

            # CPU

            self.cpu_card = self.sys_card(sys_info_row1, "#76CF8C", "server/icons/CPU.png",
                                          "CPU", usage=system_info["cpu_usage"], used=None, total=None)
            self.cpu_card.pack(fill='x', expand=False, side=ctk.LEFT)

            # RAM
            self.ram_card = self.sys_card(sys_info_row1, "#CFCC76", "server/icons/RAM.png", "RAM",
                                          usage=system_info["memory_usage_percent"], used=system_info["used_memory"],
                                          total=system_info["total_memory"])
            self.ram_card.pack(expand=True, anchor=ctk.E)

            # Frame chứa DISK và STATUS
            sys_info_row2 = ctk.CTkFrame(frame, fg_color='transparent')
            sys_info_row2.pack(fill='x', padx=100, pady=10)
            # DISK
            self.disk_card = self.sys_card(
                sys_info_row2, "#CF7676", "server/icons/DISK.png",
                "DISK", usage=system_info["disk_usage_percent"],
                used=system_info["used_disk"],
                total=system_info["total_disk"]
            )
            self.disk_card.pack(fill='x', expand=False, side=ctk.LEFT)

            # STATUS
            self.status_card = self.sys_card(
                sys_info_row2, "#A776CF", "server/icons/STATUS.png",
                "STATUS", usage=None, used=None, total=None)
            self.status_card.pack(expand=True, anchor=ctk.E)

            # Tạo một Frame trống để cách top
            spacer = ctk.CTkFrame(frame, fg_color="transparent", height=50)
            spacer.pack(fill='x')

        if user_quantity:
            total_users = len(user_quantity)
            total_tasks = len(task_quantity_list)
            _done = len(done_tasks)
            _doing = len(doing_tasks)
            _todo = len(todo_tasks)

            # Statistical Information
            statis_info_title = self.titleLabel(
                frame, "Statistical Information")
            statis_info_title.pack(fill='both', padx=20, pady=10)

            # Statis frame
            statis_frame = ctk.CTkFrame(frame, fg_color='transparent')
            statis_frame.pack(fill='x')

            # users_statisCard
            self.users_statisCard = self.users_card(
                statis_frame, total_users, online_users, offline_users)
            self.users_statisCard.pack(fill='x', padx=(
                100, 50), pady=10, side=ctk.LEFT, expand=True, anchor=ctk.N)

            # tasks_statisCard
            self.task_statisCard = self.tasks_card(
                statis_frame, total_tasks, _done, _doing, _todo)
            self.task_statisCard.pack(fill='x', padx=(
                50, 100), pady=10, side=ctk.RIGHT, expand=True, anchor=ctk.N)

        # Lấy tất cả client_ip
        hosts = get_all_host()
        if not hosts:
            print("Không có dữ liệu để hiển thị.")
            # Hiển thị thông báo lỗi lên frame để không bị trả về None
            error_label = ctk.CTkLabel(
                frame, text="Không có dữ liệu để hiển thị.", text_color="red", font=("Arial", 18))
            error_label.pack(pady=20)
            return frame  # Trả về frame rỗng để tránh lỗi

        # Tính toán tỷ lệ tổng thể
        success_rate, fail_rate = self.calculate_overall_success_rate(hosts)

        # request rate
        request_frame = ctk.CTkFrame(frame, fg_color='transparent')
        request_frame.pack(fill='x', padx=150)
        self.success_rate = self.request_rate(
            request_frame, "#6DFF9B", "Success Request", "server/icons/success.png", round(success_rate, 2))
        self.success_rate.pack(side=ctk.LEFT,  expand=False)

        self.fail_rate = self.request_rate(
            request_frame, "#FF6D6D", "Fail Request", "server/icons/fail.png", round(fail_rate, 2))
        self.fail_rate.pack(anchor=ctk.E)

        # Bảng dữ liệu clients
        table_client_frame = self.create_client_table(frame)
        table_client_frame.pack(fill="both", expand=True, pady=20)

        return frame


# ============= system infomation =========================
    def update_dashboard(self, system_info, user_quantity, task_quantity):
        # Cập nhật các giá trị CPU, RAM, DISK
        global cpu_card, ram_card, disk_card, users_statisCard, task_statisCard

        # Cập nhật CPU
        self.cpu_card.usage_label.configure(
            text=f"{system_info['cpu_usage']} %")
        self.cpu_card.monitor["progress_var"].set(
            system_info["cpu_usage"] / 100)

        # Cập nhật RAM
        self.ram_card.usage_label.configure(
            text=f"{system_info['memory_usage_percent']} %")
        if self.ram_card.used_label:
            self.ram_card.used_label.configure(
                text=f"{system_info['used_memory']} GB / {system_info['total_memory']} GB"
            )
        self.ram_card.monitor["progress_var"].set(
            system_info["memory_usage_percent"] / 100)

        # Cập nhật DISK
        self.disk_card.usage_label.configure(
            text=f"{system_info['disk_usage_percent']} %")
        if self.disk_card.used_label:
            self.disk_card.used_label.configure(
                text=f"{system_info['used_disk']} GB / {system_info['total_disk']} GB"
            )
        self.disk_card.monitor["progress_var"].set(
            system_info["disk_usage_percent"] / 100)
        
        # Cập nhật user quantity
        online_users = sum(1 for user in user_quantity if user.get("isOnline"))
        offline_users = len(user_quantity) - online_users
        self.users_statisCard.total_users.configure(
            text=f"Online: {online_users}, Offline: {offline_users}"
        )

        # Cập nhật task quantity
        task_quantity_list = task_quantity.get("Tasks list", [])  # Sử dụng key phù hợp

        done_tasks = [task for task in task_quantity_list if task["status"] == "COMPLETED"]
        doing_tasks = [task for task in task_quantity_list if task["status"] == "IN_PROGRESS"]
        todo_tasks = [task for task in task_quantity_list if task["status"] == "TODO"]
        self.task_statisCard.total_tasks.configure(
            text=f"Done: {len(done_tasks)} - Doing: {len(doing_tasks)} - Todo: {len(todo_tasks)}"
        )
        self.task_statisCard.header.title_label.configure(
            text=f"Total Tasks: {len(task_quantity_list)}"
        )

        

    def create_monitor_frame(self, master, color, var):
        frame = ctk.CTkFrame(master, fg_color="transparent")

        min_value = 0.0
        max_value = 100.0
        normalized_var = (var - min_value) / (max_value - min_value)
        # Thanh trạng thái
        progress_var = ctk.DoubleVar()
        progress_bar = ctk.CTkProgressBar(
            frame, variable=progress_var, fg_color="#DDDDDD", progress_color=color, height=20, width=250, corner_radius=0, border_width=2)
        progress_bar.set(normalized_var)  # Giá trị mặc định là 0
        progress_bar.pack(side="left", fill="x", expand=True, padx=10)

        return {
            "frame": frame,
            "progress_var": progress_var,
            "progress_bar": progress_bar
        }

    def titleLabel(self, master, content):
        frame = ctk.CTkFrame(master, fg_color="#6D96FF",
                             border_width=2, border_color='black', corner_radius=20)
        label = ctk.CTkLabel(frame, text=content, font=(
            'Arial', 32, 'bold'), text_color='black', anchor='center')
        label.pack(fill='x', padx=20, pady=10)
        return frame

    def sys_card(self, master, color, img_src, title, usage, used, total):
        card = ctk.CTkFrame(master, fg_color=color, corner_radius=10)

        # Left: Ảnh và tiêu đề
        left = ctk.CTkFrame(card, fg_color='transparent')
        left.pack(side=ctk.LEFT, padx=(30, 15), pady=10)
        image_src = ctk.CTkImage(Image.open(img_src), size=(100, 100))
        image = ctk.CTkLabel(left, text='', image=image_src)
        image.pack(pady=10)
        title_label = ctk.CTkLabel(left, text=title, font=(
            "Arial", 22, "bold"), text_color='white')
        title_label.pack()

        # Right: Usage và thanh tiến trình
        right = ctk.CTkFrame(card, fg_color='transparent')
        right.pack(side=ctk.RIGHT, padx=(15, 30), pady=5)

        if (title != "STATUS"):
            if used is not None and total is not None:
                used_label = ctk.CTkLabel(
                    right, text=f"{used} GB / {total} GB", font=("Arial", 22, 'bold'), text_color='white')
                used_label.pack(pady=10)

            usage_label = ctk.CTkLabel(right, text=f"{usage} %", font=(
                "Arial", 52, 'bold'), text_color='white')
            usage_label.pack(pady=5)
            self.monitor = self.create_monitor_frame(right, color, usage)
            self.monitor["frame"].pack(pady=10)
            card.monitor = self.monitor  # Lưu monitor để sử dụng sau

            # Lưu tham chiếu
            card.usage_label = usage_label
            card.used_label = used_label if used is not None else None
        else:
            label = ctk.CTkLabel(right, text="ON", font=(
                "Arial", 52, 'bold'), text_color='white', width=270)
            label.pack(pady=5)
        return card

# ============= Statistical Information =========================
    def statisCard(self, master, title):
        card = ctk.CTkFrame(master, fg_color="transparent")
        # Header
        title_label = ctk.CTkLabel(
            card, text=title, font=("Aria", 25), text_color='black')
        title_label.pack(fill='x')
        
        # lưu tham chiếu
        card.title_label = title_label

        return card

    def users_card(self, master, quantity, online, offline):
        frame = ctk.CTkFrame(master, fg_color='#C3C7F4',
                             corner_radius=10, width=170, height=100)
        # Ngăn frame tự động điều chỉnh kích thước theo nội dung
        frame.pack_propagate(False)

        # Header
        header = self.statisCard(frame, f"Total Users: {quantity}")
        header.pack(fill='x', pady=10)
        # Quantity
        # self.user_quantity = ctk.CTkLabel(frame, text=f"Quantity: {quantity}", font=("Aria", 22, 'bold'), text_color='black')
        # self.user_quantity.pack(fill='x', pady=10, padx=20)

        # Online frame
        total_users_frame = ctk.CTkFrame(frame, fg_color='transparent')
        total_users_frame.pack(fill='x', pady=5)
        # online quantity
        total_users = ctk.CTkLabel(total_users_frame, text=f"Online: {online}, Offline: {offline}", font=(
            "Aria", 20), text_color='black', justify='center', anchor='center')
        total_users.pack(side=ctk.TOP, expand=True)
        # lưu tham chiếu
        frame.total_users = total_users

        return frame

    def tasks_card(self, master, quantity, done, doing, todo):
        frame = ctk.CTkFrame(master, fg_color='#C3C7F4',
                             corner_radius=10, width=170, height=100)
        # Ngăn frame tự động điều chỉnh kích thước theo nội dung
        frame.pack_propagate(False)
        # Header
        header = self.statisCard(frame, f"Total Tasks: {quantity}")
        header.pack(fill='x', pady=10)
        # # Quantity
        # self.tasks_quantity = ctk.CTkLabel(frame, text=f"Quantity: {quantity}", font=("Aria", 22, 'bold'), text_color='black')
        # self.tasks_quantity.pack(fill='x', pady=10, padx=20)

        # done frame
        total_tasks_frame = ctk.CTkFrame(frame, fg_color='transparent')
        total_tasks_frame.pack(fill='x', pady=5)
        # done quantity
        total_tasks = ctk.CTkLabel(total_tasks_frame, text=f"Done: {done} - Doing: {doing} - Todo: {todo}", font=(
            "Aria", 20), text_color='black', justify='center', anchor='center')
        total_tasks.pack(side=ctk.TOP, expand=True)

        # lưu tham chiếu
        frame.total_tasks = total_tasks
        frame.header = header
        return frame

    def create_client_table(self, master):
        # Khung chứa bảng
        frame = ctk.CTkFrame(master, fg_color="white", corner_radius=10)

        # Tạo kiểu tùy chỉnh cho Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#FFFFFF",
                        foreground="black",
                        rowheight=30,
                        fieldbackground="#FFFFFF",
                        font=("Arial", 16))
        style.configure("Treeview.Heading",
                        font=("Arial", 18, "bold"),
                        background="#BDD1C5",
                        foreground="black")
        style.map("Treeview", background=[("selected", "#768FCF")])

        # Cột của bảng
        columns = ("ID", "Host", "Number of Requests", "Date")
        self.tree = ttk.Treeview(
            frame, columns=columns, show="headings", style="Treeview")

        # Định nghĩa tiêu đề và kích thước cột
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        # Thêm dữ liệu mẫu
        sample_data = get_all_host()

        for data in sample_data:
            self.tree.insert("", "end", values=(
                data['id'], data['client_ip'], data['success'] + data['fail'],
                data['created_at']
            ))

        # Tính toán số lượng dòng data
        rows = len(data)
        self.tree.config(height=min(rows, 10))  # Chỉ hiển thị tối đa 10 dòng

        # Thanh cuộn dọc
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        # Đặt bảng và thanh cuộn
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Thêm khoảng cách khi đặt frame
        frame.pack(fill="both", expand=True, pady=10, padx=10)

        return frame

# ============= request rate =========================
    def calculate_overall_success_rate(self, hosts):
        total_success = sum(host['success'] for host in hosts)
        total_fail = sum(host['fail'] for host in hosts)
        total_requests = total_success + total_fail

        if total_requests == 0:
            return 0, 0

        success_rate = (total_success / total_requests) * 100
        fail_rate = (total_fail / total_requests) * 100
        return success_rate, fail_rate

    def request_rate(self, master, color, title, img, rate):
        frame = ctk.CTkFrame(master, fg_color=color,
                             corner_radius=10, width=320, height=160)
        # Ngăn frame tự điều chỉnh kích thước theo nội dung
        frame.pack_propagate(False)

        # title
        title_label = ctk.CTkLabel(
            frame, text=f"{title}: {rate}%", text_color='black', font=("Aria", 25))
        title_label.pack(fill='x', padx=5, pady=10)

        # image
        rate_src = ctk.CTkImage(Image.open(img), size=(85, 85))
        self.rate_img = ctk.CTkLabel(frame, text='', image=rate_src)
        self.rate_img.pack(padx=5)

        return frame


# ============= system info =========================
# Hàm lấy thông tin hệ thống
def get_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    total_memory = round(memory_info.total / (1024 ** 3), 2)  # GB
    used_memory = round(memory_info.used / (1024 ** 3), 2)    # GB
    memory_usage_percent = memory_info.percent

    disk_info = psutil.disk_usage('/')
    total_disk = round(disk_info.total / (1024 ** 3), 2)      # GB
    used_disk = round(disk_info.used / (1024 ** 3), 2)        # GB
    disk_usage_percent = disk_info.percent

    return {
        "cpu_usage": cpu_usage,
        "total_memory": total_memory,
        "used_memory": used_memory,
        "memory_usage_percent": memory_usage_percent,
        "total_disk": total_disk,
        "used_disk": used_disk,
        "disk_usage_percent": disk_usage_percent
    }


def update_system_info(dashboard_frame):
    while True:
        info = get_system_info()
        users = getUsers()
        tasks = getTasks()
        if info and users and tasks:
            dashboard_frame.update_dashboard(info, users, tasks)  # Cập nhật giao diện
            time.sleep(0.1)  # Dừng 0.1 giây trước khi cập nhật tiếp


class Requests_Frame(ctk.CTkFrame):
    def __init__(self, master, log_list):
        super().__init__(master, corner_radius=10, fg_color='#768FCF')

        # # search_frame
        self.search = self.search_frame(self, log_list)
        self.search.pack(fill='x', expand=False, padx=10, pady=10)

        # ScrolledText để hiển thị log
        self.log_display = self.log_frame(self)
        self.log_display.pack(fill='both', expand=True, pady=(0, 10), padx=10)

    def search_frame(self, master, log_list):
        frame = ctk.CTkFrame(master, fg_color='transparent')

        global search_img
        search_img = ctk.CTkImage(Image.open(
            'server/icons/search.png'), size=(20, 20))
        refresh_img = ctk.CTkImage(Image.open(
            'server/icons/refresh.png'), size=(20, 20))
        self.title = ctk.CTkLabel(frame, text="Requests List", font=(
            "Aria", 34, "bold"), text_color='black')
        self.title.pack(side=ctk.LEFT, expand=True,
                        anchor=ctk.W, padx=(5, 10), pady=5)

        # Trường nhập liệu tìm kiếm
        self.search_entry = ctk.CTkEntry(frame, height=35, placeholder_text="Searching...",
                                         placeholder_text_color="gray", fg_color='black', corner_radius=20, border_width=0)
        self.search_entry.pack(side=ctk.LEFT, padx=(
            5, 15), fill='x', expand=True)

        # Nút Refresh để cập nhật log
        refresh_button = ctk.CTkButton(frame, fg_color="#79FDA5", text="Refresh", width=100, text_color='black',
                                       image=refresh_img, compound=ctk.LEFT, height=35, command=lambda: self.update_logs(api_url=f"{base_url}/api/logs"))
        refresh_button.pack(padx=5, side=ctk.LEFT, expand=False)

        # Nút tìm kiếm
        search_button = ctk.CTkButton(frame, width=100, text_color='black', fg_color='#79E2FD', text="Search",
                                      height=35, image=search_img, compound=ctk.LEFT, command=lambda: self.search_logs(log_list))
        search_button.pack(padx=5, side=ctk.LEFT, expand=False)
        return frame

    def log_frame(self, master):
        frame = ctk.CTkScrollableFrame(
            master, fg_color='black', corner_radius=10)
        return frame

    # Request item
    def request_item(self, master, method, content, color):
        frame = ctk.CTkFrame(master, fg_color='transparent', corner_radius=20)

        # request method
        self.method = self.method_item(frame, color, method)
        self.method.pack(expand=False, side=ctk.LEFT, anchor=ctk.N)

        # request content
        self.content = self.request_content(frame, color, content)
        self.content.pack(expand=True, side=ctk.LEFT, ipadx=10,
                          ipady=15, anchor=ctk.W, padx=(20, 0))

        return frame

    # request method item
    def method_item(self, master, fg_color, method):
        self.label = ctk.CTkLabel(
            master=master, text=method, text_color='black',
            font=('Aria', 16, 'bold'), corner_radius=20, fg_color=fg_color,
            width=120, height=50
        )
        return self.label

    # request content
    def request_content(self, master, fg_color, content):
        self.label = ctk.CTkLabel(
            master, text=content,
            font=('Aria', 16), text_color='black',
            fg_color=fg_color, corner_radius=20, anchor=ctk.W, justify=ctk.LEFT
        )
        return self.label
    
    def get_server_ip(self):
        hostname = socket.gethostname() 
        server_ip = socket.gethostbyname(hostname)
        return server_ip


    # Hàm cập nhật log
    def update_logs(self, filtered_logs=None, log_list=None, api_url=None):
        # Xóa nội dung cũ
        for widget in self.log_display.winfo_children():
            widget.destroy()

         # Nếu API URL được cung cấp, gọi API để lấy log
        if api_url:
            log_list = self.fetch_logs_from_api(api_url)

        # Lấy danh sách log cần hiển thị
        logs_to_display = filtered_logs if filtered_logs else log_list
        server_ip = self.get_server_ip()

        # Duyệt qua từng log và tạo request item cho mỗi log
        for log in logs_to_display:
            parts = log.split("@")

            if len(parts) >= 6:
                times = parts[0]
                method = parts[1]
                path = parts[2]
                status = parts[3]
                host = parts[4]
                client_ip = parts[5]
                content = f"[{times}]\n\nMethod: {method}\nHost: {host}\nPath: {path}\nServer IP: {server_ip}\nClient IP: {client_ip}\nStatus: {status}"
                color = "#79FDA5" if method == "GET" else "#79E2FD" if method == "POST" else "#FD797B" if method == "DELETE" else "#FDEF79"
                request_item = self.request_item(
                    master=self.log_display,
                    method=method,
                    content=content,
                    color=color
                )
                if self.filterRequest(path):
                    request_item.pack(fill='x', padx=10, pady=10)

        # Tự động cuộn xuống cuối
        self.log_display.update_idletasks()
        self.log_display._parent_canvas.yview_moveto(1.0)

    def filterRequest(self, content):
        if ("/static/assets" in content):
            return False
        else:
            return True

    def search_logs(self, log_list):
        # Lấy từ khóa từ ô tìm kiếm
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Input Error", "Please enter a keyword!")
            return

        try:
            # Tạo URL tìm kiếm với từ khóa
            search_url = f"{base_url}/api/logs/search"
            params = {"kw": keyword}

            # Gửi yêu cầu GET đến API
            response = requests.get(search_url, params=params)

            # Kiểm tra phản hồi từ API
            if response.status_code == 200:
                # Lấy danh sách logs trả về từ API
                logs = response.json().get("logs", [])

                if logs:
                    # Cập nhật logs trên giao diện
                    self.update_logs(filtered_logs=logs)
                else:
                    messagebox.showinfo(
                        "No Results", "No logs found for the given keyword.")
            elif response.status_code == 404:
                messagebox.showinfo(
                    "No Results", "No logs found for the given keyword.")
            else:
                messagebox.showerror(
                    "Error", f"Error {response.status_code}: {response.json().get('message', 'Unknown error')}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def fetch_logs_from_api(self, api_url):
        """Gọi API để lấy danh sách log từ server"""
        try:
            response = requests.get(api_url)
            response.raise_for_status()  # Kiểm tra lỗi HTTP
            logs = response.json()  # API trả về danh sách log dạng JSON
            return logs
        except requests.exceptions.RequestException as e:
            print(f"Error fetching logs: {e}")
            return []


class Users_Frame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color='#E7F5DC')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)
        self.data_label = None  # Định nghĩa biến data_label
        self.selected_id = None  # Lưu ID người dùng được chọn

        self.content = self.user_table(self)
        self.search = self.search_user(self)
        self.search.grid(row=0, column=0, sticky=ctk.NSEW, padx=10)
        self.content.grid(row=1, column=0, sticky=ctk.NSEW, padx=10, pady=10)

    def search_user(self, master):
        frame = ctk.CTkFrame(master, fg_color='transparent')

        self.title = ctk.CTkLabel(frame, text="Users List", font=(
            "Aria", 34, "bold"), text_color='black')
        self.title.pack(side=ctk.LEFT, expand=True, anchor=ctk.W, padx=(5, 10))
        # Trường nhập liệu tìm kiếm
        self.search_entry = ctk.CTkEntry(frame, height=35, placeholder_text="Searching...",
                                         placeholder_text_color="gray", fg_color='black', corner_radius=20, border_width=0)
        self.search_entry.pack(side=ctk.LEFT, padx=(
            5, 15), fill='x', expand=True)

        # Nút tìm kiếm
        search_button = ctk.CTkButton(frame, text="Search", width=100, text_color='black',
                                      fg_color='#79E2FD', height=35, image=search_img, compound=ctk.LEFT)
        search_button.pack(padx=5, side=ctk.LEFT, expand=False)
        
        # Nút active
        active_img = ctk.CTkImage(Image.open(
            'server/icons/active.png'), size=(20, 20))
        active_button = ctk.CTkButton(frame, text="Active", width=100, text_color='black',
                                      fg_color='#FD797B', height=35, image=active_img, compound=ctk.LEFT, command=self.confirm_active_action)
        active_button.pack(padx=5, side=ctk.LEFT, expand=False)

        self.data_label = ctk.CTkLabel(frame, text="Selected ID: ", text_color="black", font=("Arial", 14))
        self.data_label.pack(pady=10)
        return frame

    def user_table(self, master):
        frame = ctk.CTkFrame(master, fg_color="transparent")

        # Thiết lập kiểu tùy chỉnh cho Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#D9D9D9",   # màu nền cho các hàng
                        foreground="black",     # màu chữ
                        rowheight=30,           # tăng chiều cao dòng
                        borderwidth=0,
                        # tăng kích thước font chữ nội dung
                        font=("Arial", 12),
                        fieldbackground="#768FCF")  # màu nền cho các trường trống
        style.configure("Treeview.Heading",
                        # tăng kích thước và đậm cho tiêu đề
                        font=("Arial", 14, "bold"),
                        background="#CFDDFF",  # màu nền cho tiêu đề
                        rowheight=30,
                        foreground="black")    # màu chữ cho tiêu đề
        # màu dòng được chọn
        style.map("Treeview", background=[("selected", "#768FCF")])

        # Tạo Treeview
        columns = ("ID", "Fullname", "Age", "Gender", "Phone",
                   "Address", "Email", "Username", "isActive")
        self.tree = ttk.Treeview(frame, columns=columns,
                                 show="headings", style="Treeview")

        # Định nghĩa tiêu đề các cột và thiết lập kích thước cột
        for col in columns:
            self.tree.heading(col, text=col)
            # tăng kích thước mỗi cột
            self.tree.column(col, width=150, anchor=ctk.CENTER)

        # Thêm dữ liệu mẫu vào Treeview
        sample_data = getUsers()
        for data in sample_data:
            self.tree.insert("", "end",
                             values=(data['id'], data['fullname'], data['age'],
                                     data['gender'], data['phone'], data['address'], data['email'],
                                     data['username'], data['isActive']))

        # Tạo thanh cuộn dọc (không tạo thanh cuộn ngang)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)

        # Thêm sự kiện khi chọn hàng
        self.tree.bind("<ButtonRelease-1>", self.on_row_select)

        # Đặt Treeview và thanh cuộn dọc vào frame
        self.tree.grid(row=0, column=0, sticky="nsew")
        # vsb.grid(row=0, column=1, sticky="ns")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        return frame  # Trả về frame để tránh lỗi AttributeError

    # Hàm xử lý sự kiện khi chọn một hàng
    def on_row_select(self, event):
        """Lấy ID của hàng được chọn."""
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, "values")
            if values:
                self.selected_id = values[0]  # Lưu ID được chọn
                self.data_label.configure(text=f"Selected ID: {self.selected_id}")

    def confirm_active_action(self):
        """Hiển thị hộp thoại xác nhận và thực hiện hành động Active."""
        if self.selected_id is None:
            messagebox.showerror("No Selection", "Please select a user first!")
            return

        answer = messagebox.askyesno(
            title="Confirm Action",
            message=f"Are you sure you want to change the active status for user ID {self.selected_id}?"
        )

        if answer:
            is_successful = update_user_active(self.selected_id, is_active=True)  # Ví dụ: Cập nhật thành True
            if is_successful:
                messagebox.showinfo("Success", "User active status updated!")
                self.refresh_treeview()  # Cập nhật lại TreeView
            else:
                messagebox.showerror("Error", "Failed to update user status!")

    def refresh_treeview(self):
        """Cập nhật lại dữ liệu trong TreeView."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        sample_data = getUsers()
        for data in sample_data:
            self.tree.insert("", "end", values=(data['id'], data['fullname'], data['age'],
                                                data['gender'], data['phone'], data['address'], data['email'],
                                                data['username'], data['isActive']))
        

server_ui = App(log_list=log_list)
# Truy cập Dashboard_Frame từ App
dashboard_frame = server_ui.body.frames["dashboard"]
# update_thread = threading.Thread(
#     target=update_system_info, args=(dashboard_frame,))
# update_thread.daemon = True  # Đảm bảo thread dừng khi ứng dụng tắt
# update_thread.start()
server_ui.mainloop()
