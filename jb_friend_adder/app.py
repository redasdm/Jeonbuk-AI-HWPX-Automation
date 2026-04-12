"""
JB메신저 친구 자동추가 매크로 - GUI 앱
실행: python app.py
"""
import os
import sys
import time
import threading
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pynput import mouse as pynput_mouse

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

sys.path.insert(0, BASE_DIR)
from config_manager import ConfigManager
from excel_reader import ExcelReader
from searcher import Searcher
from result_matcher import ResultMatcher

# ─────────────────────────────────────────────────────────────────────────────
# 캘리브레이션 항목 정의 (절대 좌표로 저장)
# ─────────────────────────────────────────────────────────────────────────────
CALIB_STEPS = [
    ("search_box",  "① 검색 입력창",      "이름 검색어를 입력하는 텍스트 필드"),
    ("search_btn",  "② 검색 버튼",        "돋보기(검색) 버튼"),
    ("results_tl",  "③ 결과 영역 좌상단", "검색 결과 목록의 맨 위-왼쪽 모서리"),
    ("results_br",  "④ 결과 영역 우하단", "검색 결과 목록의 맨 아래-오른쪽 모서리"),
]


class ClickCapturer:
    """창을 숨기고 다음 마우스 클릭 좌표를 캡처한다."""

    def __init__(self, on_click_cb):
        self._cb = on_click_cb
        self._listener = None

    def start(self):
        def _on_click(x, y, button, pressed):
            if pressed and button == pynput_mouse.Button.left:
                self._listener.stop()
                self._cb(int(x), int(y))
        self._listener = pynput_mouse.Listener(on_click=_on_click)
        self._listener.start()


# ─────────────────────────────────────────────────────────────────────────────
# 메인 GUI 앱
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JB메신저 친구 자동추가 매크로")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.config_mgr = ConfigManager()
        self._macro_thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

        self._setup_logger()
        self._build_ui()
        self._refresh_calib_status()

    # ── 로거 ─────────────────────────────────────────────────────────────────
    def _setup_logger(self):
        self.logger = logging.getLogger("macro")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(
                os.path.join(LOG_DIR, "macro.log"), encoding="utf-8", mode="a"
            )
            fh.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
            )
            self.logger.addHandler(fh)

    # ── UI 구성 ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        PAD = {"padx": 12, "pady": 6}

        # ── 캘리브레이션 프레임 ─────────────────────────────────────────────
        calib_frame = ttk.LabelFrame(self, text=" UI 위치 설정 (최초 1회) ", padding=8)
        calib_frame.grid(row=0, column=0, sticky="ew", **PAD)

        self._calib_rows: list[dict] = []
        for i, (key, label, hint) in enumerate(CALIB_STEPS):
            ttk.Label(calib_frame, text=label, width=18, anchor="w").grid(
                row=i, column=0, sticky="w", pady=3
            )
            coord_var = tk.StringVar(value="미설정")
            ttk.Label(calib_frame, textvariable=coord_var, width=18,
                      foreground="#888").grid(row=i, column=1, padx=8)
            btn = ttk.Button(
                calib_frame, text="위치 등록",
                command=lambda k=key: self._start_capture(k)
            )
            btn.grid(row=i, column=2)
            ttk.Label(calib_frame, text=hint, foreground="#666",
                      font=("", 8)).grid(row=i, column=3, padx=10, sticky="w")
            self._calib_rows.append({"key": key, "coord_var": coord_var, "btn": btn})

        ttk.Button(calib_frame, text="캘리브레이션 초기화",
                   command=self._reset_calib).grid(
            row=len(CALIB_STEPS), column=0, columnspan=4, pady=(8, 0), sticky="e"
        )

        # ── 엑셀 파일 프레임 ────────────────────────────────────────────────
        excel_frame = ttk.LabelFrame(self, text=" 엑셀 파일 (A열: 소속 / B열: 이름) ", padding=8)
        excel_frame.grid(row=1, column=0, sticky="ew", **PAD)

        self._excel_path = tk.StringVar()
        ttk.Entry(excel_frame, textvariable=self._excel_path, width=48).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(excel_frame, text="찾아보기",
                   command=self._browse_excel).grid(row=0, column=1)

        # ── 딜레이 설정 ─────────────────────────────────────────────────────
        delay_frame = ttk.LabelFrame(self, text=" 속도 설정 ", padding=8)
        delay_frame.grid(row=2, column=0, sticky="ew", **PAD)

        ttk.Label(delay_frame, text="검색 후 대기(초):").grid(row=0, column=0, sticky="w")
        self._delay_search = tk.DoubleVar(
            value=self.config_mgr.get("delay_after_search", 1.5)
        )
        ttk.Spinbox(delay_frame, from_=0.5, to=5.0, increment=0.5,
                    textvariable=self._delay_search, width=6).grid(
            row=0, column=1, padx=8
        )

        ttk.Label(delay_frame, text="  행 간 대기(초):").grid(row=0, column=2, sticky="w")
        self._delay_row = tk.DoubleVar(
            value=self.config_mgr.get("delay_between_rows", 0.8)
        )
        ttk.Spinbox(delay_frame, from_=0.3, to=3.0, increment=0.1,
                    textvariable=self._delay_row, width=6).grid(
            row=0, column=3, padx=8
        )

        # ── 진행상황 ─────────────────────────────────────────────────────────
        prog_frame = ttk.LabelFrame(self, text=" 진행상황 ", padding=8)
        prog_frame.grid(row=3, column=0, sticky="ew", **PAD)

        self._prog_var = tk.IntVar(value=0)
        self._prog_bar = ttk.Progressbar(
            prog_frame, variable=self._prog_var, maximum=100, length=420
        )
        self._prog_bar.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))

        self._prog_label = tk.StringVar(value="대기 중")
        ttk.Label(prog_frame, textvariable=self._prog_label).grid(
            row=1, column=0, sticky="w"
        )

        self._stat_label = tk.StringVar(value="성공: 0  실패: 0  오류: 0")
        ttk.Label(prog_frame, textvariable=self._stat_label,
                  foreground="#444").grid(row=1, column=2, sticky="e")

        # ── 로그 ─────────────────────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self, text=" 로그 ", padding=8)
        log_frame.grid(row=4, column=0, sticky="ew", **PAD)

        self._log_box = scrolledtext.ScrolledText(
            log_frame, height=10, width=62, state="disabled",
            font=("Consolas", 9), background="#1e1e1e", foreground="#d4d4d4"
        )
        self._log_box.grid(row=0, column=0)

        # ── 버튼 ─────────────────────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, pady=10)

        self._start_btn = ttk.Button(
            btn_frame, text="▶  매크로 시작", width=20,
            command=self._start_macro
        )
        self._start_btn.grid(row=0, column=0, padx=8)

        self._stop_btn = ttk.Button(
            btn_frame, text="■  중지", width=12,
            command=self._stop_macro, state="disabled"
        )
        self._stop_btn.grid(row=0, column=1, padx=8)

    # ── 캘리브레이션 ──────────────────────────────────────────────────────────
    def _start_capture(self, key: str):
        """창을 최소화하고 다음 클릭의 절대 좌표를 기록한다."""
        for row in self._calib_rows:
            row["btn"].configure(state="disabled")
        self._start_btn.configure(state="disabled")

        self._log("위치 등록 대기 중... JB메신저 창에서 해당 위치를 클릭하세요.")
        self.iconify()
        time.sleep(0.3)

        def on_click(x, y):
            # 절대 좌표를 그대로 저장
            self.config_mgr.set(key, [x, y])
            self.config_mgr.save()
            msg = f"저장됨: ({x}, {y})"
            self.after(100, lambda: self._on_capture_done(msg))

        ClickCapturer(on_click).start()

    def _on_capture_done(self, msg: str):
        self.deiconify()
        self._log(msg)
        self._refresh_calib_status()
        for row in self._calib_rows:
            row["btn"].configure(state="normal")
        self._start_btn.configure(state="normal")

    def _refresh_calib_status(self):
        for row in self._calib_rows:
            val = self.config_mgr.get(row["key"])
            if val:
                row["coord_var"].set(f"({val[0]}, {val[1]})")
            else:
                row["coord_var"].set("미설정")

    def _reset_calib(self):
        if not messagebox.askyesno("초기화", "캘리브레이션 설정을 초기화할까요?"):
            return
        for key, _, _ in CALIB_STEPS:
            self.config_mgr.set(key, None)
        self.config_mgr.save()
        self._refresh_calib_status()
        self._log("캘리브레이션 초기화 완료.")

    # ── 엑셀 ─────────────────────────────────────────────────────────────────
    def _browse_excel(self):
        path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel 파일", "*.xlsx *.xls"), ("모든 파일", "*.*")]
        )
        if path:
            self._excel_path.set(path)

    # ── 매크로 실행 ───────────────────────────────────────────────────────────
    def _start_macro(self):
        if not self.config_mgr.is_calibrated():
            messagebox.showwarning("캘리브레이션 필요",
                                   "4개의 UI 위치를 모두 등록해주세요.")
            return

        excel = self._excel_path.get().strip()
        if not excel or not os.path.exists(excel):
            messagebox.showwarning("엑셀 파일 없음", "엑셀 파일을 선택해주세요.")
            return

        self.config_mgr.set("delay_after_search", self._delay_search.get())
        self.config_mgr.set("delay_between_rows", self._delay_row.get())
        self.config_mgr.save()

        self._stop_flag.clear()
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")

        self._macro_thread = threading.Thread(
            target=self._run_macro, args=(excel,), daemon=True
        )
        self._macro_thread.start()

    def _stop_macro(self):
        self._stop_flag.set()
        self._log("중지 요청됨...")
        self._stop_btn.configure(state="disabled")

    def _run_macro(self, excel_path: str):
        success, fail, skip = 0, 0, 0
        try:
            reader = ExcelReader(excel_path)
            rows = reader.get_all_rows()
            total = len(rows)
            self._log(f"엑셀 로드: 총 {total}명")

            if total == 0:
                self._log("처리할 데이터가 없습니다.")
                return

            searcher = Searcher(self.config_mgr)
            matcher = ResultMatcher(self.config_mgr)

            self.after(0, lambda: self._prog_bar.configure(maximum=total))

            for idx, (org, name) in enumerate(rows, start=1):
                if self._stop_flag.is_set():
                    break

                self._log(f"[{idx}/{total}] {name} | {org[:30]}")
                self.after(0, lambda i=idx, t=total, n=name: (
                    self._prog_var.set(i),
                    self._prog_label.set(f"{i} / {t}  처리 중: {n}")
                ))

                try:
                    searcher.search(name)
                    time.sleep(self.config_mgr.get("delay_after_search", 1.5))

                    ok = matcher.find_and_click(org, name=name, person_label=f"{name}_{idx}")
                    if ok:
                        success += 1
                        self._log("  ✓ 추가 성공")
                    else:
                        fail += 1
                        self._log("  ✗ 소속 불일치 또는 결과 없음")

                except Exception as e:
                    skip += 1
                    self._log(f"  ✗ 오류: {e}")

                s, f, sk = success, fail, skip
                self.after(0, lambda s=s, f=f, sk=sk:
                    self._stat_label.set(f"성공: {s}  실패: {f}  오류: {sk}")
                )

                time.sleep(self.config_mgr.get("delay_between_rows", 0.8))

        finally:
            self._log(f"\n완료!  성공: {success}  실패: {fail}  오류: {skip}")
            self.after(0, lambda: (
                self._start_btn.configure(state="normal"),
                self._stop_btn.configure(state="disabled"),
                self._prog_label.set(
                    f"완료  성공: {success}  실패: {fail}  오류: {skip}"
                )
            ))

    # ── 로그 출력 ─────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        def _append():
            self._log_box.configure(state="normal")
            self._log_box.insert("end", msg + "\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")
        self.after(0, _append)
        self.logger.info(msg)

    # ── 종료 ─────────────────────────────────────────────────────────────────
    def _on_close(self):
        self._stop_flag.set()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
