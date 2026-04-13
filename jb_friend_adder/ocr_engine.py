"""
EasyOCR 래퍼 (Windows OCR 대체)
- 딥러닝(CRAFT + CRNN) 기반으로 폰트 변형에 강함
- 한국어 UI 텍스트의 얇은 회색 글씨도 인식 가능
- 결과: [{"text": str, "x": int, "y": int, "cy": int}, ...]
"""
import logging
import numpy as np

logger = logging.getLogger("macro")


class WindowsOCR:
    """EasyOCR 기반 OCR 엔진 (기존 WindowsOCR 인터페이스 유지)"""

    def __init__(self, lang: str = "ko"):  # noqa: ARG002
        import easyocr
        logger.info("EasyOCR 초기화 중 (최초 1회 모델 로딩)...")
        self._reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        logger.info("EasyOCR 초기화 완료")

    def recognize(self, img: np.ndarray) -> list[dict]:
        """numpy 이미지(RGB) → OCR 결과 리스트"""
        try:
            # EasyOCR: detail=1 → [(bbox, text, conf), ...]
            # bbox = [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
            results = self._reader.readtext(img, detail=1, paragraph=False)
            items = []
            for bbox, text, conf in results:
                if not text.strip():
                    continue
                x1 = int(min(p[0] for p in bbox))
                y1 = int(min(p[1] for p in bbox))
                y2 = int(max(p[1] for p in bbox))
                items.append({
                    "text": text.strip(),
                    "x": x1,
                    "y": y1,
                    "cy": (y1 + y2) // 2,
                })
            return items
        except Exception as e:
            logger.error(f"  OCR 오류: {e}")
            return []
