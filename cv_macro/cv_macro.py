"""
cv_macro/cv_macro.py  v2.0
===========================
전북교육연수원(jbstudy.kr) OpenCV 기반 자동 수강 매크로

[ 동작 흐름 ]
  ┌─ 일반 루프 ──────────────────────────────────────────────┐
  │  1. 사이드바에서 초록 '재생중' 배지 감지 (HSV 색상)         │
  │  2. 재생중 사라짐 → 다음 '학습전' 항목의 텍스트(왼쪽) 클릭  │
  │  3. 학습전 항목 없음 → '다음 차시' 버튼 클릭               │
  └──────────────────────────────────────────────────────────┘
           ↓  [다음 차시 클릭 후 특별 시퀀스]
  ┌─ 차시 진입 시퀀스 ──────────────────────────────────────────┐
  │  Step A. 다음 차시 버튼 클릭                                │
  │  Step B. 드롭다운에서 첫 번째 차시 항목(텍스트 왼쪽) 클릭    │
  │  Step C. 새 화면 로드 후 맨 위 '학습전' 배지(아이콘) 직접 클릭│
  │  Step D. 일반 루프로 복귀                                   │
  └────────────────────────────────────────────────────────────┘

[ 필요 템플릿 이미지 (templates 폴더) ]
  - badge_before.png       : '학습전' 회색 배지
  - btn_next_chapter.png   : '다음 차시' 버튼
"""

try:
    import cv2
except ImportError:
    print("[ERROR] OpenCV (cv2) is not installed. Please run 'run.bat' to install required packages.")
    import sys
    sys.exit(1)
import numpy as np
import pyautogui
import time
import os
import sys

try:
    import win32gui
    import win32ui
    import win32con
    import ctypes
except ImportError:
    print("[ERROR] pywin32 is not installed. Please run 'run.bat' again.")
    sys.exit(1)

# Ensure console supports utf-8 emojis on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────
# 설정값
# ─────────────────────────────────────────────
SCAN_INTERVAL    = 2.0   # 일반 루프 감시 주기 (초)
MATCH_THRESHOLD  = 0.75  # 템플릿 매칭 임계값 (0~1, 낮출수록 관대)
CLICK_OFFSET_X   = -80   # '학습전' 배지 기준으로 왼쪽 텍스트 클릭 오프셋 (px)
DEBOUNCE_COUNT   = 2     # '재생중 없음'을 N번 연속 감지 후 행동

# 사이드바만 스캔하려면 (x, y, w, h) 형태로 설정. None = 전체 화면
SIDEBAR_REGION   = None

# 차시 진입 시퀀스 딜레이 (초)
DELAY_AFTER_NEXT_CHAPTER_CLICK = 1.5  # 다음차시 클릭 후 드롭다운 표시 대기
DELAY_AFTER_CHAPTER_ITEM_CLICK = 3.0  # 차시 항목 클릭 후 새 화면 로드 대기

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

# ─────────────────────────────────────────────
# 윈도우 창 추적 기능 (HWND)
# ─────────────────────────────────────────────
TARGET_HWND = None

def get_target_hwnd():
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if '강의실' in title and 'Chrome' in title:
                hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None

def capture(region=None):
    global TARGET_HWND
    if TARGET_HWND is None or not win32gui.IsWindow(TARGET_HWND):
        TARGET_HWND = get_target_hwnd()

    if TARGET_HWND is None:
        # 백그라운드 타겟을 찾지 못하면 기존처럼 전체 화면 캡처
        shot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)

    # 윈도우 백그라운드 캡처 (가려져 있어도 캡처 가능)
    try:
        left, top, right, bot = win32gui.GetWindowRect(TARGET_HWND)
        w = right - left
        h = bot - top
        if w <= 0 or h <= 0:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        hwndDC = win32gui.GetWindowDC(TARGET_HWND)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
        saveDC.SelectObject(saveBitMap)

        # PW_RENDERFULLCONTENT = 3 (하드웨어 가속 창 캡처용 플래그)
        ctypes.windll.user32.PrintWindow(TARGET_HWND, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(TARGET_HWND, hwndDC)

        if region:
            rx, ry, rw, rh = region
            img = img[ry:ry+rh, rx:rx+rw]

        return img
    except Exception as e:
        log(f"  ⚠️ 백그라운드 캡처 실패: {e}")
        # 오류 시 전체 캡처로 폴백
        shot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)

def load_template(name):
    path = os.path.join(TEMPLATES_DIR, name)
    if not os.path.exists(path):
        return None
    return cv2.imread(path)

def find_all_templates(screen_bgr, template_bgr, threshold=None):
    """
    화면에서 템플릿과 일치하는 모든 위치 반환.
    반환: [(cx, cy, confidence), ...]  — y좌표 오름차순 (위→아래)
    """
    if template_bgr is None or screen_bgr is None:
        return []
        
    sh, sw = screen_bgr.shape[:2]
    th_h, tw_w = template_bgr.shape[:2]
    
    # 크기 검증: 화면(창) 캡처 영역이 템플릿 이미지보다 작으면 OpenCV 에러 발생 방지
    if sh < th_h or sw < tw_w:
        return []

    th = threshold if threshold is not None else MATCH_THRESHOLD
    try:
        result = cv2.matchTemplate(screen_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)
    except cv2.error as e:
        log(f"  ⚠️ matchTemplate 오류: {e}")
        return []
        
    h, w   = template_bgr.shape[:2]
    locs   = np.where(result >= th)
    matches = []
    for pt in zip(*locs[::-1]):
        cx   = pt[0] + w // 2
        cy   = pt[1] + h // 2
        conf = float(result[pt[1], pt[0]])
        matches.append((cx, cy, conf))
    matches = _dedup(matches)
    matches.sort(key=lambda m: m[1])   # 위→아래 정렬
    return matches

def _dedup(matches, min_dist=20):
    kept = []
    for m in matches:
        if not any(abs(m[0]-k[0]) < min_dist and abs(m[1]-k[1]) < min_dist for k in kept):
            kept.append(m)
    return kept

def is_playing(screen_bgr, tpl_playing=None):
    """
    '재생중' 배지가 있는지 확인.
    템플릿이 제공된 경우 템플릿 매칭을 사용하고, 없으면 HSV 색상을 사용.
    """
    if tpl_playing is not None:
        matches = find_all_templates(screen_bgr, tpl_playing, threshold=0.75)
        return len(matches) > 0
    else:
        # Fallback: 단순 초록색 면적 검사 (오작동 확률 높음)
        hsv   = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
        lower = np.array([40, 120, 100])
        upper = np.array([90, 255, 255])
        mask  = cv2.inRange(hsv, lower, upper)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return any(cv2.contourArea(c) > 200 for c in cnts)

def safe_click(x, y, label=''):
    global TARGET_HWND
    
    prev_hwnd = None
    if TARGET_HWND and win32gui.IsWindow(TARGET_HWND):
        prev_hwnd = win32gui.GetForegroundWindow()
        
        # 최소화되어 있다면 복원
        if win32gui.IsIconic(TARGET_HWND):
            win32gui.ShowWindow(TARGET_HWND, win32con.SW_RESTORE)
            
        try:
            # 창을 앞으로 소환
            win32gui.SetForegroundWindow(TARGET_HWND)
            time.sleep(0.3)  # 창이 앞으로 나올 시간 대기
        except Exception as e:
            log(f"  ⚠️ 팝업 창을 앞으로 가져오는 데 실패: {e}")

    sw, sh = pyautogui.size()
    if 0 <= x <= sw and 0 <= y <= sh:
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.15)
        pyautogui.click()
        log(f'  ✅ 클릭 ({x}, {y}) {label}')
        
        # 클릭 후 원래 창으로 포커스 복원
        if prev_hwnd and prev_hwnd != TARGET_HWND and win32gui.IsWindow(prev_hwnd):
            time.sleep(0.2)
            try:
                if win32gui.IsIconic(prev_hwnd):
                    win32gui.ShowWindow(prev_hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(prev_hwnd)
            except Exception:
                pass
        return True
        
    log(f'  ⚠️  좌표 범위 초과 ({x}, {y}) — 클릭 취소')
    return False

def screen_offset():
    """타겟 윈도우가 있으면 윈도우의 절대 좌표를 오프셋으로 반환"""
    ox, oy = 0, 0
    if TARGET_HWND and win32gui.IsWindow(TARGET_HWND):
        try:
            left, top, right, bot = win32gui.GetWindowRect(TARGET_HWND)
            ox, oy = left, top
        except Exception:
            pass
            
    if SIDEBAR_REGION:
        return ox + SIDEBAR_REGION[0], oy + SIDEBAR_REGION[1]
    return ox, oy

# ─────────────────────────────────────────────
# 클릭 헬퍼
# ─────────────────────────────────────────────
def click_first_badge_text(matches, label='학습전 텍스트'):
    """
    학습전 배지 목록에서 가장 위의 항목을 찾아
    배지 왼쪽 텍스트 영역을 클릭
    """
    if not matches:
        return False
    bx, by, _ = matches[0]
    ox, oy = screen_offset()
    return safe_click(bx + ox + CLICK_OFFSET_X, by + oy, f'[{label}]')

def click_first_badge_icon(matches, label='학습전 배지'):
    """
    학습전 배지 목록에서 가장 위의 항목의
    배지(아이콘) 자체를 클릭 (텍스트 왼쪽이 아님)
    """
    if not matches:
        return False
    bx, by, _ = matches[0]
    ox, oy = screen_offset()
    return safe_click(bx + ox, by + oy, f'[{label} 아이콘]')

# ─────────────────────────────────────────────
# 차시 진입 시퀀스
# ─────────────────────────────────────────────
def run_chapter_enter_sequence(tpl_before, tpl_next):
    """
    '다음 차시' 버튼 클릭 후 실행되는 특별 시퀀스:
      A. 다음 차시 클릭
      B. 드롭다운 첫 번째 차시 항목 텍스트(왼쪽) 클릭
      C. 새 화면에서 맨 위 '학습전' 배지(아이콘) 직접 클릭
    """
    log('── 차시 진입 시퀀스 시작 ──')

    # ── Step A: 다음 차시 버튼 클릭 ──
    screen = capture(SIDEBAR_REGION)
    nexts  = find_all_templates(screen, tpl_next, threshold=0.70)
    if not nexts:
        log('  ⚠️  [A] 다음 차시 버튼을 찾지 못했습니다.')
        return False
    nx, ny, _ = nexts[0]
    ox, oy = screen_offset()
    log('[A] 다음 차시 버튼 클릭')
    safe_click(nx + ox, ny + oy, '[다음 차시]')

    # ── Step B: 드롭다운 첫 번째 항목(텍스트) 클릭 ──
    log(f'[B] {DELAY_AFTER_NEXT_CHAPTER_CLICK}s 대기 후 드롭다운 스캔...')
    time.sleep(DELAY_AFTER_NEXT_CHAPTER_CLICK)

    screen  = capture(SIDEBAR_REGION)
    befores = find_all_templates(screen, tpl_before)

    if not befores:
        log('  ⚠️  [B] 드롭다운에서 학습전 항목을 찾지 못했습니다.')
        return False

    log(f'[B] 드롭다운 첫 번째 항목 클릭 (총 {len(befores)}개 감지됨)')
    click_first_badge_text(befores, label='드롭다운 첫 항목')

    # ── Step C: 새 화면 로드 후 맨 위 학습전 배지 아이콘 클릭 ──
    log(f'[C] {DELAY_AFTER_CHAPTER_ITEM_CLICK}s 대기 후 새 화면 스캔...')
    time.sleep(DELAY_AFTER_CHAPTER_ITEM_CLICK)

    screen  = capture(SIDEBAR_REGION)
    befores = find_all_templates(screen, tpl_before)

    if not befores:
        log('  ⚠️  [C] 새 화면에서 학습전 항목을 찾지 못했습니다.')
        return False

    log(f'[C] 새 화면 맨 위 학습전 배지(아이콘) 직접 클릭')
    click_first_badge_icon(befores, label='새 화면 첫 학습전')

    log('── 차시 진입 시퀀스 완료 → 일반 루프 복귀 ──')
    time.sleep(2.0)
    return True

# ─────────────────────────────────────────────
# 메인 루프
# ─────────────────────────────────────────────
def run():
    log('🤖 AntiGravity CV 매크로 v2.0 시작 (Ctrl+C 로 종료)')

    tpl_playing = load_template('badge_playing.png')
    tpl_before  = load_template('badge_before.png')
    tpl_complete= load_template('badge_complete.png')
    tpl_next    = load_template('btn_next_chapter.png')
    
    # 돌발 버튼들
    tpl_quiz_done = load_template('btn_quiz_done.png')
    tpl_player_next = load_template('btn_player_next.png')

    if tpl_playing is None:
        log('⚠️  templates/badge_playing.png 없음 → 기존 색상 인식 방식으로 작동합니다 (오작동 가능성 있음)')
        log('   capture_templates.py 를 실행해서 "재생중" 배지를 캡처하시길 권장합니다.')
    if tpl_before is None:
        log('❌  templates/badge_before.png 없음 → capture_templates.py 먼저 실행하세요')
        sys.exit(1)
    if tpl_next is None:
        log('⚠️  templates/btn_next_chapter.png 없음 → 다음 차시 자동 클릭 불가')

    debounce    = 0
    was_playing = False

    try:
        while True:
            screen = capture(SIDEBAR_REGION)

            # ── 1. 돌발 상황(팝업 버튼) 감지 및 즉시 클릭 ──
            interrupted = False
            for btn_tpl, btn_name in [(tpl_quiz_done, '학습(퀴즈)완료 버튼'), (tpl_player_next, '플레이어 다음 버튼')]:
                if btn_tpl is not None:
                    btn_matches = find_all_templates(screen, btn_tpl, threshold=0.75)
                    if btn_matches:
                        log(f'🚨 돌발 버튼 감지: {btn_name} ➜ 자동 클릭 실행')
                        cx, cy, _ = btn_matches[0]
                        ox, oy = screen_offset()
                        safe_click(cx + ox, cy + oy, f'[{btn_name}]')
                        time.sleep(2.0)  # 클릭 후 화면 전환 대기
                        interrupted = True
                        break  # 한 번에 하나씩만 처리
            
            if interrupted:
                continue  # 버튼을 눌렀으면 처음부터 다시 스크린샷 캡처 및 상태 분석

            # ── 2. 기본 재생 상태 분석 ──
            if is_playing(screen, tpl_playing):
                if debounce > 0:
                    log('🟢 재생중 배지 재감지 → 디바운스 초기화 (시청 계속)')
                else:
                    log('▶️ 정상 시청 중... 초록색 "재생중" 배지 감지됨')
                debounce    = 0
                was_playing = True

            else:
                if was_playing:
                    debounce += 1
                    log(f'🔍 재생중 없음 ({debounce}/{DEBOUNCE_COUNT})')

                    if debounce >= DEBOUNCE_COUNT:
                        debounce    = 0
                        was_playing = False
                        log('✨ 강의 완료 감지 → 다음 항목 탐색')
                        time.sleep(1.0)

                        screen  = capture(SIDEBAR_REGION)
                        befores = find_all_templates(screen, tpl_before)

                        if befores:
                            # ── 같은 차시 내 다음 강의로 이동 (텍스트 클릭) ──
                            log(f'📋 학습전 {len(befores)}개 발견 → 첫 번째 텍스트 클릭')
                            click_first_badge_text(befores)
                            time.sleep(2.0)
                            was_playing = False

                        elif tpl_next is not None:
                            # ── 다음 차시 진입 시퀀스 ──
                            log('🏁 모든 항목 완료 → 차시 진입 시퀀스 실행')
                            run_chapter_enter_sequence(tpl_before, tpl_next)
                            was_playing = False

                        else:
                            log('⚠️  학습전 없음 & 다음차시 템플릿 없음 → 수동 조작 필요')
                else:
                    # 현재 재생중 배지도 없고, 이전에 재생중이지도 않았던 경우
                    msg = '⏳ 대기 중... 현재 화면에서 초록색 "재생중" 배지를 찾고 있습니다.'
                    global TARGET_HWND
                    if TARGET_HWND:
                        try:
                            msg += f' [타겟 창 캡처 중: {win32gui.GetWindowText(TARGET_HWND)}]'
                        except:
                            TARGET_HWND = None

                    if tpl_complete is not None:
                        complete_matches = find_all_templates(screen, tpl_complete, threshold=0.75)
                        if len(complete_matches) > 0:
                            msg += f' (참고: "학습완료" 배지 {len(complete_matches)}개 감지됨)'
                    log(msg)

            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        log('👋 매크로 종료')

if __name__ == '__main__':
    run()
