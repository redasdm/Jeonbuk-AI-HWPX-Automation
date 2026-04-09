"""
cv_macro/capture_templates.py
==============================
매크로가 화면에서 찾아야 할 템플릿 이미지를 캡처하는 도우미 스크립트.

실행 방법:
  python capture_templates.py

캡처 순서:
  1. badge_before.png  : '학습전' 회색 배지
  2. btn_next_chapter.png : '다음 차시' 버튼

캡처 방법:
  - 안내 메시지가 나오면 강의 화면을 적절히 띄워 두세요.
  - Enter 를 누르면 3초 후 자동으로 화면 전체를 캡처합니다.
  - 캡처된 이미지에서 해당 부분만 자동으로 ROI 선택 창이 열립니다.
  - 마우스로 해당 배지/버튼 부분을 드래그하고 Enter 로 확정하세요. (ESC = 취소)
"""

import cv2
import numpy as np
import pyautogui
import time
import os
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(TEMPLATES_DIR, exist_ok=True)


def capture_with_delay(delay=3):
    """delay초 카운트다운 후 전체 화면 캡처"""
    for i in range(delay, 0, -1):
        print(f'  {i}초 후 캡처...')
        time.sleep(1)
    shot = pyautogui.screenshot()
    bgr  = cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
    print('  📸 캡처 완료!')
    return bgr


def select_and_save(screen_bgr, filename, label):
    """
    ROI 선택 창을 띄워 사용자가 드래그로 범위 지정 후 저장
    """
    win_name = f'[드래그로 선택] {label}  →  Enter 확정 / ESC 취소'
    # 화면이 크면 표시가 어려우므로 50% 축소해서 보여줌
    h, w = screen_bgr.shape[:2]
    scale = min(1.0, 1400 / w)
    preview = cv2.resize(screen_bgr, (int(w * scale), int(h * scale)))

    roi = cv2.selectROI(win_name, preview, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()

    x, y, rw, rh = roi
    if rw == 0 or rh == 0:
        print(f'  ⚠️  선택 취소됨 ({filename} 저장 생략)')
        return False

    # 원본 해상도로 역변환
    x_orig  = int(x  / scale)
    y_orig  = int(y  / scale)
    rw_orig = int(rw / scale)
    rh_orig = int(rh / scale)

    crop    = screen_bgr[y_orig:y_orig + rh_orig, x_orig:x_orig + rw_orig]
    save_path = os.path.join(TEMPLATES_DIR, filename)
    cv2.imwrite(save_path, crop)
    print(f'  ✅ 저장 완료: {save_path}  ({rw_orig}x{rh_orig}px)')
    return True


def main():
    targets = [
        ('badge_playing.png',      "'재생중' 초록 배지 아이콘만 드래그해서 선택하세요"),
        ('badge_before.png',       "'학습전' 회색 배지 아이콘만 드래그해서 선택하세요"),
        ('badge_complete.png',     "'학습완료' 배지 아이콘만 드래그해서 선택하세요 (선택)"),
        ('btn_next_chapter.png',   "'다음 차시' 파란 버튼 전체를 드래그해서 선택하세요"),
    ]

    print('=' * 55)
    print('  AntiGravity — 템플릿 이미지 캡처 도우미')
    print('=' * 55)

    for filename, label in targets:
        print(f'\n[{filename}]')
        print(f'  → 화면에 [{label}]가 보이도록 준비한 뒤 Enter 를 누르세요.')
        input('  준비됐으면 Enter ▶ ')
        screen = capture_with_delay(3)
        select_and_save(screen, filename, label)

    print('\n✨ 모든 템플릿 캡처 완료!')
    print(f'   저장 위치: {TEMPLATES_DIR}')
    print('   이제 cv_macro.py 를 실행하세요.')


if __name__ == '__main__':
    main()
