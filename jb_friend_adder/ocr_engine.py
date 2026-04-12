"""
Windows 내장 OCR API 래퍼
- winsdk.windows.media.ocr 사용
- 한국어 UI 텍스트에 최적화
- 결과: [{"text": str, "x": int, "y": int, "cy": int}, ...]
  (좌표는 입력 이미지 기준 픽셀)
"""
import io
import asyncio
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger("macro")


class WindowsOCR:
    def __init__(self, lang: str = "ko"):
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language

        language = Language(lang)
        self._engine = OcrEngine.try_create_from_language(language)
        if self._engine is None:
            raise RuntimeError(
                f"Windows OCR: '{lang}' 언어 팩이 설치되지 않았습니다.\n"
                "설정 → 시간 및 언어 → 언어 → 한국어 → 언어 팩 설치 후 재시도하세요."
            )
        logger.info(f"Windows OCR 초기화 완료 (언어: {lang})")

    def recognize(self, img: np.ndarray) -> list[dict]:
        """numpy 이미지(RGB) → OCR 결과 리스트"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._recognize_async(img))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"  OCR 오류: {e}")
            return []

    async def _recognize_async(self, img: np.ndarray) -> list[dict]:
        from winsdk.windows.graphics.imaging import (
            SoftwareBitmap, BitmapPixelFormat,
            BitmapAlphaMode, BitmapDecoder,
        )
        from winsdk.windows.storage.streams import (
            InMemoryRandomAccessStream, DataWriter,
        )

        # numpy → PNG bytes
        pil = Image.fromarray(img)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        # bytes → IRandomAccessStream
        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream.get_output_stream_at(0))
        writer.write_bytes(raw_bytes)
        await writer.store_async()
        stream.seek(0)

        # stream → SoftwareBitmap
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        bitmap = SoftwareBitmap.convert(
            bitmap,
            BitmapPixelFormat.BGRA8,
            BitmapAlphaMode.PREMULTIPLIED,
        )

        # OCR 실행
        result = await self._engine.recognize_async(bitmap)

        items = []
        for line in result.lines:
            for word in line.words:
                r = word.bounding_rect
                items.append({
                    "text": word.text,
                    "x": int(r.x),
                    "y": int(r.y),
                    "cy": int(r.y + r.height / 2),
                })
        return items
