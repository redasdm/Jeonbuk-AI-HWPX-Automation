"""
hwpx_utils.py — HWPX MCP 공통 유틸리티 모음

사용법:
    python hwpx_utils.py --action text   --file "경로/파일.hwpx"
    python hwpx_utils.py --action para   --file "경로/파일.hwpx"
    python hwpx_utils.py --action cells  --file "경로/파일.hwpx" --tables 1 2 3
"""
import asyncio
import json
import sys
import argparse
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.stdout.reconfigure(encoding='utf-8')

MCP_ARGS = ["C:/Users/redas/OneDrive/Desktop/AntiGravity/hwpx-mcp/mcp-server/dist/index.js"]


async def open_doc(session, file_path: str) -> str:
    """문서를 열고 doc_id 반환"""
    result = await session.call_tool("open_document", {"file_path": file_path})
    return json.loads(result.content[0].text).get("doc_id")


async def save_doc(session, doc_id: str, output_path: str):
    """문서를 지정 경로에 저장하고 닫기"""
    await session.call_tool("save_document", {
        "doc_id": doc_id,
        "output_path": output_path,
        "create_backup": False,
        "verify_integrity": False
    })
    await session.call_tool("close_document", {"doc_id": doc_id})


async def get_text(session, doc_id: str) -> str:
    """전체 텍스트 반환"""
    result = await session.call_tool("get_document_text", {"doc_id": doc_id})
    return json.loads(result.content[0].text).get("text", "")


async def get_paragraphs(session, doc_id: str) -> list:
    """단락 목록 반환 [{index, text}, ...]"""
    result = await session.call_tool("get_paragraphs", {"doc_id": doc_id, "section_index": 0})
    raw = json.loads(result.content[0].text)
    return raw.get("paragraphs", raw)


async def get_table_cells(session, doc_id: str, table_idx: int) -> list:
    """표 셀 목록 반환 (text 있는 것만)"""
    result = await session.call_tool("get_table", {
        "doc_id": doc_id, "section_index": 0, "table_index": table_idx
    })
    data = json.loads(result.content[0].text).get("data", [])
    cells = []
    for r, row in enumerate(data):
        for c, cell in enumerate(row):
            if isinstance(cell, dict):
                text = cell.get("text", "").strip()
                if text:
                    cells.append({"row": r, "col": c, "text": text})
    return cells


async def update_paragraphs(session, doc_id: str, updates: list):
    """단락 일괄 업데이트 [{"index": int, "text": str}, ...]"""
    for upd in updates:
        try:
            await session.call_tool("update_paragraph_text", {
                "doc_id": doc_id,
                "section_index": 0,
                "paragraph_index": upd["index"],
                "text": upd["text"]
            })
            print(f"  [단락 {upd['index']}] ✓")
        except Exception as e:
            print(f"  [단락 {upd['index']}] ✗ {e}")


async def batch_replace(session, doc_id: str, replacements: list):
    """텍스트 일괄 교체 [{"old_text": str, "new_text": str}, ...]"""
    await session.call_tool("batch_replace", {"doc_id": doc_id, "replacements": replacements})


async def update_cell(session, doc_id: str, table_idx: int, row: int, col: int, text: str):
    """표 셀 업데이트"""
    await session.call_tool("update_table_cell", {
        "doc_id": doc_id, "section_index": 0,
        "table_index": table_idx, "row": row, "col": col, "text": text
    })


async def cli(args):
    async with stdio_client(StdioServerParameters(command="node", args=MCP_ARGS)) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            doc_id = await open_doc(session, args.file)
            print(f"문서 열림: {doc_id}")

            if args.action == "text":
                # 전체 텍스트 출력
                text = await get_text(session, doc_id)
                print(text)

            elif args.action == "para":
                # 단락 인덱스 목록 출력
                paras = await get_paragraphs(session, doc_id)
                for p in paras:
                    idx = p.get("index", "?")
                    text = p.get("text", "").strip()
                    if text:
                        print(f"[{idx}] {text[:120]}")

            elif args.action == "cells":
                # 지정 표의 셀 내용 출력
                table_indices = [int(x) for x in (args.tables or ["1"])]
                for t in table_indices:
                    print(f"\n=== Table {t} ===")
                    cells = await get_table_cells(session, doc_id, t)
                    for cell in cells:
                        print(f"  [{cell['row']},{cell['col']}] {cell['text'][:100]}")

            await session.call_tool("close_document", {"doc_id": doc_id})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HWPX MCP 유틸리티")
    parser.add_argument("--action", choices=["text", "para", "cells"], required=True)
    parser.add_argument("--file", required=True, help="HWPX 파일 경로")
    parser.add_argument("--tables", nargs="*", help="cells 조회시 테이블 인덱스 목록")
    asyncio.run(cli(parser.parse_args()))
