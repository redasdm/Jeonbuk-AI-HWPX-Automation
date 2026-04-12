"""
검색 결과 파싱 및 클릭 모듈
- Windows OCR → 텍스트 정제 → 학교 고유명 기반 매칭 → HoughCircles 링 버튼 클릭
"""
import os
import re
import cv2
import time
import logging
import ctypes
import numpy as np
import pyautogui
from PIL import Image, ImageGrab, ImageEnhance

from ocr_engine import WindowsOCR

pyautogui.FAILSAFE = False
logger = logging.getLogger("macro")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG_DIR = os.path.join(BASE_DIR, "log", "debug_captures")

_ocr: WindowsOCR | None = None


def _get_ocr() -> WindowsOCR:
    global _ocr
    if _ocr is None:
        _ocr = WindowsOCR(lang="ko")
    return _ocr


def _get_dpi_scale() -> float:
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi / 96.0
    except Exception:
        return 1.0


# ── OCR 텍스트 정제 ─────────────────────────────────────────────────────────
_CORRECTIONS = [
    (r"즈등학교", "초등학교"),
    (r"조등학교", "초등학교"),
    (r"즈등",     "초등"),
    (r"조등",     "초등"),
    (r"교육지원정", "교육지원청"),
    (r"교육지원씬", "교육지원청"),
    (r"교육지원진", "교육지원청"),
    (r"지원정",   "지원청"),
    (r"교육정",   "교육청"),
    (r"\s*\(\s*1\s*\)\s*$", ""),
    (r"^\s*\(\s*1\s*\)\s*", ""),
    (r"^\s*0\s+", ""),
    (r"\s+0\s+",  " "),
    (r"[ⅹ•`,卜八人昌仄]", ""),
    (r"\s{2,}",   " "),
]

def _clean(text: str) -> str:
    for pattern, repl in _CORRECTIONS:
        text = re.sub(pattern, repl, text)
    return text.strip()


# ── 학교명 고유부분 추출 ─────────────────────────────────────────────────────
_SCHOOL_SUFFIXES = ["교육지원청", "교육청", "초등학교", "중학교", "고등학교"]

def _extract_specific(org: str) -> tuple[str, str]:
    """'태인초등학교' → ('태인', '초등학교')"""
    org_c = _clean(org).replace(" ", "")
    for suffix in _SCHOOL_SUFFIXES:
        if org_c.endswith(suffix):
            return org_c[:-len(suffix)], suffix
    return org_c, ""


def _fuzzy_contains(needle: str, haystack: str, max_err: int) -> bool:
    """
    haystack 내에 needle과 max_err 이하 문자 차이 부분문자열이 있으면 True.
    예: _fuzzy_contains("태인", "대인초등학교", 1) → True (태≠대, 1개 오차)
    """
    n = len(needle)
    if n == 0:
        return True
    for i in range(len(haystack) - n + 1):
        errs = sum(a != b for a, b in zip(needle, haystack[i:i+n]))
        if errs <= max_err:
            return True
    return False


class ResultMatcher:
    def __init__(self, config):
        self.config = config
        self.ocr = _get_ocr()
        self._dpi = _get_dpi_scale()
        logger.info(f"DPI 배율: {self._dpi:.2f}x")

    # ── 좌표 ─────────────────────────────────────────────────────────────────
    def _results_rect(self):
        tl = self.config.get("results_tl")
        br = self.config.get("results_br")
        return tl[0], tl[1], br[0], br[1]

    def _scroll_center(self):
        tl = self.config.get("results_tl")
        br = self.config.get("results_br")
        return (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

    def _safe_pos(self):
        sx, sy = self.config.get("search_btn")
        return sx, sy - 40

    # ── 스크롤 ───────────────────────────────────────────────────────────────
    def _scroll_to_top(self):
        cx, cy = self._scroll_center()
        pyautogui.moveTo(cx, cy, duration=0.1)
        time.sleep(0.1)
        for _ in range(5):
            pyautogui.scroll(10)
            time.sleep(0.05)
        pyautogui.moveTo(*self._safe_pos(), duration=0.1)
        time.sleep(0.4)

    def _scroll_down(self, clicks: int = 3):
        cx, cy = self._scroll_center()
        pyautogui.moveTo(cx, cy, duration=0.1)
        time.sleep(0.1)
        pyautogui.scroll(-clicks)
        pyautogui.moveTo(*self._safe_pos(), duration=0.1)
        time.sleep(0.5)

    # ── 캡처 ─────────────────────────────────────────────────────────────────
    def _capture(self, save_debug: bool = False, label: str = "") -> tuple[np.ndarray, float]:
        pyautogui.moveTo(*self._safe_pos(), duration=0.1)
        time.sleep(0.3)

        rect = self._results_rect()
        d = self._dpi
        phys = (int(rect[0]*d), int(rect[1]*d), int(rect[2]*d), int(rect[3]*d))
        img = ImageGrab.grab(bbox=phys, all_screens=True)

        if save_debug:
            os.makedirs(DEBUG_DIR, exist_ok=True)
            img.save(os.path.join(DEBUG_DIR, f"{label}_raw.png"))

        scale = 2.0
        w, h = img.size
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.5)

        return np.array(img.convert("RGB")), d * scale

    # ── 행 그룹핑 ─────────────────────────────────────────────────────────────
    def _group_rows(self, items: list[dict], scale: float = 1.0) -> list[list[dict]]:
        threshold = int(self.config.get("row_group_threshold", 10) * scale)
        sorted_items = sorted(items, key=lambda i: i["cy"])
        rows, cur, last_cy = [], [], None
        for item in sorted_items:
            if last_cy is None or abs(item["cy"] - last_cy) <= threshold:
                cur.append(item)
            else:
                rows.append(cur)
                cur = [item]
            last_cy = item["cy"]
        if cur:
            rows.append(cur)
        return rows

    def _row_text(self, row: list[dict]) -> str:
        raw = " ".join(i["text"] for i in sorted(row, key=lambda i: i["x"]))
        return _clean(raw)

    # ── 소속 매칭 ─────────────────────────────────────────────────────────────
    def _match_org(self, org: str, row_text: str) -> bool:
        """
        학교 고유명 기반 매칭:
        1단계: 직접 포함
        2단계: 학교 종류(초등학교 등) + 고유명 fuzzy 매칭
               고유명에서 1/3 글자까지 오인식 허용 (최소 1자 허용)
        """
        org_c   = _clean(org).replace(" ", "")
        row_c   = row_text.replace(" ", "")

        if not org_c:
            return False

        # 1단계: 직접 포함
        if org_c in row_c:
            return True

        # 2단계: 고유명 + 학교종류 분리 매칭
        specific, suffix = _extract_specific(org)
        spec_c = specific.replace(" ", "")

        if suffix:
            # 학교 종류(또는 앞 2글자)가 행에 있어야 함
            if suffix not in row_c and suffix[:2] not in row_c:
                return False

            if not spec_c:
                return True  # 고유명이 없으면 종류만으로 통과

            # 고유명 글자수에 따른 허용 오차 (짧은 이름도 1자 허용)
            max_err = max(1, len(spec_c) // 3)
            matched = _fuzzy_contains(spec_c, row_c, max_err)
            if matched:
                return True

        # 3단계 (비학교 기관): 단어 단위 매칭
        words = [w for w in _clean(org).split() if len(w) >= 2]
        if words and any(w in row_text for w in words):
            return True

        return False

    # ── 링 버튼 감지 (HoughCircles) ──────────────────────────────────────────
    def _find_ring_button(self, screen_y: int) -> tuple[int, int]:
        """
        결과 영역 오른쪽에서 HoughCircles로 링 버튼 원의 중심을 찾는다.
        못 찾으면 기본 offset으로 fallback.
        """
        br = self.config.get("results_br")
        tl = self.config.get("results_tl")
        margin = 35

        x1 = br[0] - 75
        x2 = br[0] + 10
        y1 = max(tl[1], screen_y - margin)
        y2 = min(br[1], screen_y + margin)

        region = np.array(ImageGrab.grab(bbox=(x1, y1, x2, y2)))
        gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=20,
            param1=50,
            param2=12,
            minRadius=6,
            maxRadius=16,
        )

        if circles is not None:
            circles = np.round(circles[0]).astype(int)
            # 가장 오른쪽 원을 링 버튼으로 선택
            best = sorted(circles, key=lambda c: -c[0])[0]
            cx, cy, r = best
            abs_x, abs_y = x1 + cx, y1 + cy
            logger.info(f"  링 버튼 감지: ({abs_x}, {abs_y}) 반지름={r}px")
            return abs_x, abs_y

        # fallback
        offset = self.config.get("circle_x_offset", 22)
        logger.warning(f"  링 버튼 미감지 → offset 사용: ({br[0] - offset}, {screen_y})")
        return br[0] - offset, screen_y

    # ── 메인 ────────────────────────────────────────────────────────────────
    def find_and_click(self, org: str, name: str = "", person_label: str = "") -> bool:
        tl  = self.config.get("results_tl")
        results_top = tl[1]
        max_scrolls = self.config.get("max_scroll_attempts", 15)

        self._scroll_to_top()
        prev_texts: frozenset = frozenset()

        for attempt in range(max_scrolls + 1):
            img, scale = self._capture(
                save_debug=True,
                label=f"{person_label or name or org}_s{attempt}"
            )
            items = self.ocr.recognize(img)
            rows  = self._group_rows(items, scale=scale)

            suffix = f" (스크롤 {attempt}회)" if attempt > 0 else ""
            logger.info(f"  OCR {len(rows)}행 감지{suffix}")
            for r in rows:
                logger.info(f"    행: '{self._row_text(r)}'")

            for row in rows:
                row_text = self._row_text(row)
                if not self._match_org(org, row_text):
                    continue

                # 매칭 행의 화면 Y
                cy = sum(i["cy"] for i in row) / len(row)
                screen_y = results_top + int(cy / scale)

                # HoughCircles로 링 버튼 정확한 위치 탐지
                btn_x, btn_y = self._find_ring_button(screen_y)

                logger.info(f"  ✓ 매칭: '{row_text[:40]}' → 클릭 ({btn_x}, {btn_y})")
                pyautogui.click(btn_x, btn_y)
                time.sleep(self.config.get("delay_after_click", 0.3))

                if self._verify_selected(btn_x, btn_y):
                    return True
                logger.warning("  선택 미확인, 재시도...")
                pyautogui.click(btn_x, btn_y)
                time.sleep(0.4)
                return True

            current_texts = frozenset(self._row_text(r) for r in rows)
            if current_texts and current_texts == prev_texts:
                logger.info("  목록 끝 도달")
                break
            if current_texts:
                prev_texts = current_texts

            if attempt < max_scrolls:
                logger.info(f"  ↓ 스크롤 ({attempt+1}/{max_scrolls})")
                self._scroll_down(clicks=3)

        logger.warning(f"  '{name}({org})' 일치 항목 없음")
        return False

    # ── 선택 확인 ─────────────────────────────────────────────────────────────
    def _verify_selected(self, cx: int, cy: int) -> bool:
        try:
            region = ImageGrab.grab(bbox=(cx-15, cy-15, cx+15, cy+15))
            arr = np.array(region)
            r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
            return int(np.sum((r < 120) & (g < 180) & (b > 150))) > 20
        except Exception:
            return True
