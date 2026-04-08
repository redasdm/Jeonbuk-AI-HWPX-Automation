import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
import cv_macro

class GUIStream:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.insert(tk.END, text)
        self.text_widget.see(tk.END)

    def flush(self):
        pass

class MacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AntiGravity CV Macro")
        self.root.geometry("600x400")
        self.root.configure(bg="#2b2b2b")
        self.root.attributes("-topmost", True)

        # Title Label
        title = tk.Label(root, text="JBStudy CV Macro v2.0", bg="#2b2b2b", fg="#ffffff", font=("Malgun Gothic", 14, "bold"))
        title.pack(side="top", pady=10)

        # Button Frame (Bottom)
        btn_frame = tk.Frame(root, bg="#2b2b2b")
        btn_frame.pack(side="bottom", fill="x", pady=10)

        # Log Console (Middle, fills remaining space)
        self.console = scrolledtext.ScrolledText(root, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10), state="normal")
        self.console.pack(side="top", expand=True, fill="both", padx=10, pady=5)
        
        # Redirect stdout
        sys.stdout = GUIStream(self.console)

        # Control Buttons
        self.btn_start = tk.Button(btn_frame, text="▶ 매크로 시작", font=("Malgun Gothic", 12, "bold"), bg="#4CAF50", fg="white", width=15, command=self.start_macro)
        self.btn_start.pack(side="left", padx=20, expand=True)

        self.btn_stop = tk.Button(btn_frame, text="■ 매크로 정지", font=("Malgun Gothic", 12, "bold"), bg="#f44336", fg="white", width=15, state="disabled", command=self.stop_macro)
        self.btn_stop.pack(side="right", padx=20, expand=True)

        print("[시스템] 매크로 준비 완료. 시작 버튼을 누르세요.")
        print("[주의] 창을 최소화(-) 하지 마시고, 엑셀 등 다른 창으로 가려주세요!")

    def start_macro(self):
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        print("\n[시스템] 매크로 쓰레드를 시작합니다...")
        
        cv_macro.RUNNING = True
        self.thread = threading.Thread(target=cv_macro.run, daemon=True)
        self.thread.start()

    def stop_macro(self):
        self.btn_stop.config(state="disabled")
        print("\n[시스템] 매크로를 정지하는 중...")
        cv_macro.RUNNING = False
        
        # UI 복원은 쓰레드가 완전히 죽은 뒤에 하거나 바로 해도 됨
        self.root.after(1000, self._enable_start)

    def _enable_start(self):
        self.btn_start.config(state="normal")
        print("[시스템] 매크로가 완전히 정지되었습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()
