"""
검색 동작 모듈
- 검색창에 이름을 붙여넣고 검색 버튼을 클릭한다.
- 한글은 typewrite로 입력 불가 → pyperclip으로 클립보드 경유 붙여넣기
"""
import time
import pyautogui
import pyperclip

pyautogui.FAILSAFE = False  # 화면 모서리 이동 시 예외 비활성화


class Searcher:
    def __init__(self, config):
        self.config = config

    def search(self, name: str):
        bx, by = self.config.get("search_box")
        sx, sy = self.config.get("search_btn")

        # 1. 검색 입력창 클릭 → 전체 선택 → 삭제
        pyautogui.click(bx, by)
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.05)
        pyautogui.press("delete")
        time.sleep(0.1)

        # 2. 한글 이름을 클립보드로 붙여넣기
        pyperclip.copy(name)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.15)

        # 3. 검색 버튼 클릭
        pyautogui.click(sx, sy)
