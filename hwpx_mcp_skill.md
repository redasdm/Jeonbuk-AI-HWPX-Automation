# HWPX MCP 기반 공문서 자동 생성 스킬

## 개요
전북교육청 공문서(운영계획, 추진계획 등)를 기존 HWPX 표준 양식에 새 내용을 자동으로 채워 넣어
완성된 문서를 생성하고 Git으로 버전 관리하는 작업 방법입니다.

## 핵심 원칙
1. **표준 양식 파일**을 열어서 내용만 교체한다 (구조·서식은 절대 수정 안 함)
2. **HWPX MCP 서버**(`hwpx-mcp`)만 사용한다 — 저수준 XML 조작 금지
3. 교체할 텍스트는 **단락 인덱스 기반(update_paragraph_text)** 이 가장 정확하다
4. 표 내부 구조 데이터는 **update_table_cell(row, col)** 로 직접 지정한다
5. **표 내 본문 셀(헤더 제외)은 글씨체·크기를 반드시 동일하게 맞춘다** → `set_text_style` 로 일괄 적용

---

## 작업 순서 (표준 절차)

### Step 0: 표준 양식 경로 확인
```
표준 양식 폴더: C:\Users\redas\OneDrive\Desktop\hwpx\
대상 산출 폴더: C:\Users\redas\OneDrive\Desktop\업무\★251020)AI교육 정책 종합계획 수립(안)\0.실무추진\
```

### Step 1: 양식 구조 분석 (처음 한 번만)
```python
# 실행: python get_all_text.py    → 전체 텍스트 확인
# 실행: python get_paragraphs.py  → 단락 인덱스 목록 파악
# 실행: python inspect_cells.py   → 표 셀 좌표 파악 (cols·rows)
```

#### 분석으로 파악해야 할 것
- `get_document_outline` → 표 목록과 element_index 확인
- `get_paragraphs` → 각 단락 인덱스와 텍스트 확인 → **치환 대상 목록 작성**
- `get_table` (data 키 사용) → 표 셀 내용 확인 (TF구성표, 일정표 등)

### Step 2: 내용 교체 스크립트 작성 (build_*.py)

#### 2-1. batch_replace: 단순 텍스트 교체 (전 문서 범위)
```python
await session.call_tool("batch_replace", {
    "doc_id": doc_id,
    "replacements": [
        {"old_text": "교체할 텍스트", "new_text": "새 텍스트"},
        ...
    ]
})
```
> ⚠️ 주의: 앞뒤 공백, ❐ 기호 포함 여부에 따라 매칭 실패 가능 → Step 3으로 보완

#### 2-2. update_paragraph_text: 단락 인덱스 기반 정밀 교체 (가장 신뢰성 높음)
```python
# get_paragraphs.py로 인덱스를 먼저 확인한 후 사용
await session.call_tool("update_paragraph_text", {
    "doc_id": doc_id,
    "section_index": 0,
    "paragraph_index": 9,      # get_paragraphs로 파악한 인덱스
    "text": "❐ 새로운 내용"
})
```

#### 2-3. update_table_cell: 표 셀 직접 지정
```python
await session.call_tool("update_table_cell", {
    "doc_id": doc_id,
    "section_index": 0,
    "table_index": 5,   # get_table_map으로 파악한 테이블 인덱스
    "row": 1,           # 0-based
    "col": 0,           # 0-based
    "text": "새 내용"
})
```

#### 2-4. set_text_style: 표 본문 셀 글씨체·크기 통일 (필수)

> ⚠️ **규칙**: `update_table_cell`로 내용을 넣은 후에는 반드시 **헤더 행(row 0)을 제외한 모든 본문 셀**에 동일한 글씨체·크기를 적용한다. 헤더 셀(row 0)은 원래 서식을 그대로 유지한다.

표 내 단락의 인덱스는 **`get_paragraphs`로는 파악되지 않으므로** 아래처럼 `get_table` 데이터에서 각 셀의 단락 인덱스를 추출하거나, `set_text_style`을 셀 내부 단락 인덱스 기준으로 호출한다.

```python
# 표 본문 셀 글씨 통일 헬퍼 함수
async def normalize_table_font(session, doc_id, table_idx, total_rows, total_cols,
                                font_name="함초롬바탕", font_size=10, skip_header=True):
    """헤더(row 0) 제외 본문 셀 전체 글씨체·크기 통일"""
    result = await session.call_tool("get_table", {
        "doc_id": doc_id, "section_index": 0, "table_index": table_idx
    })
    data = json.loads(result.content[0].text).get("data", [])
    start_row = 1 if skip_header else 0
    for row in data[start_row:]:
        for cell in row:
            if not isinstance(cell, dict): continue
            for para in cell.get("style", {}).get("paragraphs", []):
                para_idx = int(para.get("id", 0))  # 셀 내 단락 인덱스는 별도 확인 필요
                try:
                    await session.call_tool("set_text_style", {
                        "doc_id": doc_id, "section_index": 0,
                        "paragraph_index": para_idx,
                        "font_name": font_name, "font_size": font_size
                    })
                except: pass
```

> 📌 **실무 권장**: 표 단락 ID 추출이 복잡할 경우, 내용을 넣은 직후 build 스크립트 내에서 셀별로 `set_text_style` 을 명시적으로 호출하여 스타일을 지정하는 것이 가장 안전하다.

```python
# 명시적 적용 예시 (build_*.py 내부)
# update_table_cell 직후 set_text_style 한 쌍으로 묶어서 사용
await session.call_tool("update_table_cell", {...})
await session.call_tool("set_text_style", {
    "doc_id": doc_id, "section_index": 0,
    "paragraph_index": CELL_PARA_IDX,   # 해당 셀 안의 단락 인덱스
    "font_name": "함초롬바탕",
    "font_size": 10
})
```

### Step 3: 미교체 여부 검증 후 보완
```python
# get_all_text.py 재실행 → template_text.txt 확인
# 여전히 남아있는 구 텍스트가 있으면 precise_update.py 방식으로 보완
```

### Step 3-B: 불필요한 표/행 삭제

내용이 교체되지 않아 구 내용이 남아있거나, 해당 문서에 필요 없는 표/행은 삭제한다.

> ⚠️ **주의**: 삭제 전에 반드시 `get_table`로 행 수 확인 후, **큰 인덱스부터 역순으로 삭제**해야 인덱스 밀림이 없다.
> ⚠️ **주의**: 저장 전에 한글(HWP) 프로그램에서 해당 파일이 열려있으면 `EBUSY` 오류 발생 → 닫고 재실행

```python
# 행 단위 삭제 (큰 인덱스부터!)
for row_idx in range(last_row, keep_until, -1):
    await session.call_tool("delete_table_row", {
        "doc_id": doc_id, "section_index": 0,
        "table_index": 8, "row_index": row_idx
    })

# 표 전체 삭제
await session.call_tool("delete_table", {
    "doc_id": doc_id, "section_index": 0,
    "table_index": 11   # 큰 번호 표부터 삭제
})

# 단락 삭제
await session.call_tool("delete_paragraph", {
    "doc_id": doc_id, "section_index": 0,
    "paragraph_index": 36
})
```


```python
# 저장
await session.call_tool("save_document", {
    "doc_id": doc_id,
    "output_path": r"C:\...\결과파일.HWPX",
    "create_backup": False,
    "verify_integrity": False
})

# Git 커밋
git -C "대상폴더" add "파일명.HWPX"
git -C "대상폴더" commit -m "커밋 메시지"
```

---

## 주의사항 / 알려진 함정

| 상황 | 원인 | 해결책 |
|------|------|--------|
| batch_replace가 매칭 안 됨 | 텍스트 앞에 공백 있거나 ❐ 기호 포함 | get_paragraphs로 인덱스 파악 후 update_paragraph_text 사용 |
| get_table 파싱 오류 | 응답 JSON 키가 `data` 임 | `json.loads(raw).get("data", [])` 로 파싱 |
| 표 셀이 비어있어 매칭 안 됨 | 내용이 셀이 아닌 단락(paragraph)에 있음 | get_paragraphs 먼저 확인 |
| 부분 교체로 이상한 텍스트 생성 | SW→AI 교육, 범용→"" 같은 단어 단위 치환 | 전체 문장 단위로 old_text 지정 |
| **표 셀마다 글씨 크기가 달라짐** | update_table_cell이 새 서식으로 삽입함 | 내용 삽입 후 set_text_style로 헤더 제외 전 셀 통일 적용 |

---

## Python MCP 클라이언트 기본 템플릿

```python
import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.stdout.reconfigure(encoding='utf-8')

MCP_SERVER = ["node", "C:/Users/redas/OneDrive/Desktop/AntiGravity/hwpx-mcp/mcp-server/dist/index.js"]
TEMPLATE_DIR = "C:/Users/redas/OneDrive/Desktop/hwpx/"
OUTPUT_DIR   = r"C:\Users\redas\OneDrive\Desktop\업무\★251020)AI교육 정책 종합계획 수립(안)\0.실무추진"

async def open_doc(session, file_path):
    result = await session.call_tool("open_document", {"file_path": file_path})
    return json.loads(result.content[0].text).get("doc_id")

async def save_doc(session, doc_id, output_path):
    await session.call_tool("save_document", {
        "doc_id": doc_id, "output_path": output_path,
        "create_backup": False, "verify_integrity": False
    })
    await session.call_tool("close_document", {"doc_id": doc_id})

async def main():
    async with stdio_client(StdioServerParameters(command="node", args=MCP_SERVER[1:])) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            doc_id = await open_doc(session, TEMPLATE_DIR + "표준양식.hwpx")
            
            # === 여기에 작업 내용 작성 ===
            
            await save_doc(session, doc_id, os.path.join(OUTPUT_DIR, "결과파일.HWPX"))

asyncio.run(main())
```

---

## 현재 실무추진단 운영 계획 작업에서 파악된 양식 구조
### 표준 양식: `2025년 교육용 범용 SW 구독 개선 TF 운영계획.hwpx`

| 표 인덱스 | 크기 | 내용 | 단락 위치 |
|-----------|------|------|-----------|
| Table 0   | 4×1  | 문서 제목/표지 | - |
| Table 1   | 8×6  | 장 헤더 (Ⅰ) - 제목만 있음 | 단락 [4~5] 에 내용 |
| Table 2   | 8×6  | 장 헤더 (Ⅱ) | 단락 [9~12] 에 내용 |
| Table 3   | 8×6  | 장 헤더 (Ⅲ) | 단락 [16~18] 에 내용 |
| Table 4   | 1×1  | 주요 과업 내용 (본문 텍스트) | row:0, col:0 |
| Table 5   | 6×5  | 추진단(TF) 구성 명단 | row:1~5, col:0~4 |
| Table 6   | 5×3  | 추진 일정 [단계, 기간, 내용] | row:1~4, col:0~2 |
| Table 7   | 8×6  | 장 헤더 (Ⅳ) | 단락 [31~39] 에 내용 |
| Table 8   | 16×3 | 추진 경과 [기간, 내용, 비고] | row:1~15, col:0~2 |
| Table 9   | 7×5  | 분과별 활동 시기 (간트표) | row:0~6, col:0~4 |
| Table 10  | 8×6  | 장 헤더 (Ⅴ) | 단락 [65~69] 에 내용 |
| Table 12  | 3×3  | 비교표 [구분, 전, 후] | row:0~2, col:0~2 |
| Table 13  | 7×2  | 분야별 개요 [분류, 내용] | row:0~5, col:0~1 |
| Table 14  | 8×6  | 장 헤더 (Ⅵ) | - |
| Table 15  | 4×4  | 예산 [구분, 항목, 산출, 계] | row:0~3, col:0~3 |
| Table 16  | 8×6  | 장 헤더 (Ⅶ) | 단락 [85~87] 에 내용 |

### 핵심 단락 인덱스 (AI교육 종합계획 실무추진단 운영 계획(안).HWPX 기준)
```
[4]  1장 내용 1 (추진 배경)
[5]  1장 내용 2 (추진 배경)
[9]  2장 내용 1 (운영 방침 - 현장중심)
[10] 2장 내용 2 (자립적 판단)
[11] 2장 내용 3 (공개 투명)
[12] 2장 내용 4 (융합 거버넌스)
[16] 3장 내용 1 (명칭)
[17] 3장 내용 2 (운영 기간)
[18] 3장 내용 3 (주요 과업 소제목)
[31~36] 4장 추진 경과 세부 내용
[85~87] 7장 기대 효과 3가지
```

---

## 재사용 도구 스크립트 경로
```
C:\Users\redas\OneDrive\Desktop\AntiGravity\get_all_text.py        ← 전체 텍스트 덤프
C:\Users\redas\OneDrive\Desktop\AntiGravity\get_paragraphs.py      ← 단락 인덱스 목록
C:\Users\redas\OneDrive\Desktop\AntiGravity\inspect_cells.py       ← 표 셀 내용 확인
C:\Users\redas\OneDrive\Desktop\AntiGravity\hwpx_utils.py          ← 범용 유틸리티 (CLI 모드)
C:\Users\redas\OneDrive\Desktop\AntiGravity\build_tf_plan_final.py ← 최신 생성 스크립트 (9단계)
C:\Users\redas\OneDrive\Desktop\AntiGravity\update_policy_tf.py   ← 추진단 구성·배경 업데이트
C:\Users\redas\OneDrive\Desktop\AntiGravity\cleanup_tables_v2.py  ← 불필요 행·표 삭제
C:\Users\redas\OneDrive\Desktop\AntiGravity\precise_update.py     ← 단락 인덱스 정밀 교체
```
