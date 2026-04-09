"""
gui_app.py - AntiGravity CV Macro GUI
=====================================
Tkinter 윈도우 앱. run.bat에서 이 파일을 직접 실행합니다.
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import sys
import os
import io
import traceback
import webbrowser
import ctypes

# ── stdout/stderr가 None인 환경(pythonw 등) 대비 ──
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# ── cv_macro 임포트 (에러 시 GUI로 표시) ──
try:
    import cv_macro
except Exception as e:
    _import_error = str(e) + "\n" + traceback.format_exc()
    cv_macro = None
else:
    _import_error = None


class ThreadSafeStream:
    """백그라운드 쓰레드 → GUI 메인루프로 안전하게 텍스트를 전달하는 큐 기반 스트림"""
    def __init__(self, log_queue):
        self._queue = log_queue

    def write(self, text):
        if text:
            self._queue.put(text)

    def flush(self):
        pass

# ── GUI 로드 시 CMD(콘솔) 창 숨기기 ──
if sys.platform == 'win32':
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE

class MacroApp:
    POLL_INTERVAL = 100  # ms 단위로 큐를 확인

    def __init__(self, root):
        self.root = root
        self.root.title("Wrist Protector")
        self.root.geometry("620x450")
        self.root.minsize(400, 300)
        self.root.configure(bg="#2b2b2b")
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── 로그 큐 (쓰레드 → GUI) ──
        self.log_queue = queue.Queue()

        # ── Title ──
        title = tk.Label(
            root, text="🛡️ 전북 연수원 손목 지킴이 (월급루팡 모드)",
            bg="#2b2b2b", fg="#ffffff",
            font=("Malgun Gothic", 14, "bold"),
        )
        title.pack(side="top", pady=(10, 5))

        # ── 포털 접속 버튼 ──
        portal_btn = tk.Button(
            root, text="🌐 교육연수포털 접속하기",
            font=("Malgun Gothic", 9, "underline"),
            bg="#2b2b2b", fg="#4da6ff",
            relief="flat", cursor="hand2", activebackground="#2b2b2b", activeforeground="#99ccff",
            command=lambda: webbrowser.open("https://www.jbstudy.kr/")
        )
        portal_btn.pack(side="top", pady=(0, 5))

        # ── 상태 표시 ──
        self.status_var = tk.StringVar(value="⏸  대기 중")
        status_bar = tk.Label(
            root, textvariable=self.status_var,
            bg="#2b2b2b", fg="#aaaaaa",
            font=("Malgun Gothic", 10),
        )
        status_bar.pack(side="top")

        # ── 버튼 (아래 고정) ──
        btn_frame = tk.Frame(root, bg="#2b2b2b")
        btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        self.btn_start = tk.Button(
            btn_frame, text="▶  매크로 시작",
            font=("Malgun Gothic", 12, "bold"),
            bg="#4CAF50", fg="white", width=15,
            relief="flat", cursor="hand2",
            command=self.start_macro,
        )
        self.btn_start.pack(side="left", padx=10, expand=True)

        self.btn_stop = tk.Button(
            btn_frame, text="■  매크로 정지",
            font=("Malgun Gothic", 12, "bold"),
            bg="#f44336", fg="white", width=15,
            relief="flat", cursor="hand2",
            state="disabled",
            command=self.stop_macro,
        )
        self.btn_stop.pack(side="right", padx=10, expand=True)

        # ── 로그 콘솔 (가운데, 나머지 공간 차지) ──
        self.console = scrolledtext.ScrolledText(
            root, bg="#1e1e1e", fg="#00ff00",
            font=("Consolas", 10),
            state="normal", wrap="word",
            insertbackground="#00ff00",
        )
        self.console.pack(side="top", expand=True, fill="both", padx=10, pady=5)

        # ── stdout을 큐 기반 스트림으로 교체 ──
        sys.stdout = ThreadSafeStream(self.log_queue)
        sys.stderr = ThreadSafeStream(self.log_queue)

        # ── 큐 폴링 시작 ──
        self._poll_queue()

        # ── 초기 메시지 ──
        if _import_error:
            print(f"[오류] cv_macro 모듈 로드 실패:\n{_import_error}")
            self.btn_start.config(state="disabled")
        else:
            print("[시스템] 매크로 준비 완료. '매크로 시작' 버튼을 누르세요.")
            print("[주의] 브라우저 창을 최소화(-) 하지 마시고, 다른 창으로 가려주세요!")

    # ──────────────── 큐 → GUI 텍스트 위젯 ────────────────
    def _poll_queue(self):
        """메인 쓰레드에서 큐를 주기적으로 비워서 콘솔에 출력"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.console.insert(tk.END, msg)
                self.console.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(self.POLL_INTERVAL, self._poll_queue)

    # ──────────────── 매크로 제어 ────────────────
    def start_macro(self):
        if cv_macro is None:
            return
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.status_var.set("▶  매크로 실행 중...")
        print("\n[시스템] 매크로 쓰레드를 시작합니다...")

        cv_macro.RUNNING = True
        self.thread = threading.Thread(target=self._run_macro, daemon=True)
        self.thread.start()

    def _run_macro(self):
        """매크로를 실행하고, 예외 발생 시 로그에 출력"""
        try:
            cv_macro.run()
        except Exception as e:
            print(f"\n[오류] 매크로 실행 중 예외 발생:\n{traceback.format_exc()}")
        finally:
            # 쓰레드 종료 후 UI 복원 (메인 쓰레드에서 실행)
            self.root.after(0, self._on_macro_stopped)

    def stop_macro(self):
        self.btn_stop.config(state="disabled")
        self.status_var.set("⏳  정지하는 중...")
        print("\n[시스템] 매크로를 정지하는 중...")
        if cv_macro:
            cv_macro.RUNNING = False

    def _on_macro_stopped(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.status_var.set("⏸  대기 중")
        print("[시스템] 매크로가 정지되었습니다.")

    def _on_close(self):
        if cv_macro:
            cv_macro.RUNNING = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MacroApp(root)
    root.mainloop()
