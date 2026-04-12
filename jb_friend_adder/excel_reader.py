"""
엑셀 읽기 모듈
- A열: 소속
- B열: 이름
- 1행은 헤더(있으면 자동 감지해서 스킵)
"""
import openpyxl


class ExcelReader:
    def __init__(self, path: str):
        self.path = path
        self.wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        self.ws = self.wb.active

    def get_all_rows(self) -> list[tuple[str, str]]:
        """(소속, 이름) 튜플 리스트 반환. 빈 행 및 헤더 자동 제외."""
        rows = []
        for i, row in enumerate(self.ws.iter_rows(values_only=True), start=1):
            org = str(row[0]).strip() if row[0] is not None else ""
            name = str(row[1]).strip() if row[1] is not None else ""

            # 빈 행 스킵
            if not org or not name:
                continue

            # 첫 행이 헤더처럼 보이면 스킵
            if i == 1 and name in ("이름", "성명", "name"):
                continue

            rows.append((org, name))

        self.wb.close()
        return rows
