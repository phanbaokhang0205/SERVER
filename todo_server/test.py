import requests
from tkinter import Tk, Text, Button, END

def fetch_logs():
    try:
        # Gửi request GET đến Flask server
        response = requests.get("http://172.16.0.15:5001/api/logs")
        response.raise_for_status()  # Kiểm tra nếu lỗi xảy ra
        
        logs = response.json()  # Parse dữ liệu từ Flask
        
        # Hiển thị logs trong tkinter
        text_area.delete(1.0, END)  # Xóa nội dung cũ
        for log in logs:
            text_area.insert(END, log + '\n')  # Thêm từng dòng log
    except requests.RequestException as e:
        text_area.insert(END, f"Error fetching logs: {e}\n")

# Tạo GUI tkinter
root = Tk()
root.title("Server Logs Viewer")

text_area = Text(root, width=100, height=30)
text_area.pack()

refresh_button = Button(root, text="Refresh Logs", command=fetch_logs)
refresh_button.pack()

root.mainloop()
