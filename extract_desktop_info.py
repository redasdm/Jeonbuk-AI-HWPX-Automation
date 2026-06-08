# -*- coding: utf-8 -*-
"""
바탕화면 문서 텍스트 추출기 (Desktop Text Extractor for Gemini)

이 스크립트는 바탕화면의 모든 문서를 스캔하고 본문 텍스트를 추출하여
Gemini 에이전트가 읽을 수 있도록 JSON 파일로 병합 저장합니다.
"""

import os
import re
import json
import zipfile
import zlib
import struct
import sys

DESKTOP_DIR = r"C:\Users\redas\OneDrive\Desktop"
OUTPUT_JSON = r"C:\Users\redas\.gemini\antigravity\brain\48219d81-e4d8-4230-8f36-af86eb7d8050\scratch\desktop_files_info.json"

ALLOWED_EXTENSIONS = {
    ".hwp", ".hwpx", ".pdf", ".docx", ".doc",
    ".xlsx", ".xls", ".xlsm", ".pptx", ".ppt",
    ".txt", ".md"
}

# ==========================================
# 텍스트 추출 엔진 (Text Extraction Engines)
# ==========================================

def decompress_hwp_stream(data):
    try:
        return zlib.decompress(data, -15)
    except Exception:
        try:
            return zlib.decompress(data)
        except Exception:
            return data

def extract_text_from_hwp_section(raw_data):
    pos = 0
    texts = []
    while pos + 4 <= len(raw_data):
        tag_info = struct.unpack_from('<I', raw_data, pos)[0]
        tag = tag_info & 0x3FF
        level = (tag_info >> 10) & 0xF
        size = (tag_info >> 14) & 0xFFF
        if size == 0xFFF:
            if pos + 8 <= len(raw_data):
                size = struct.unpack_from('<I', raw_data, pos + 4)[0]
                pos += 8
            else:
                break
        else:
            pos += 4
        
        if pos + size > len(raw_data):
            break
            
        chunk = raw_data[pos:pos+size]
        
        if tag == 67: # HWPTAG_PARA_TEXT
            try:
                text = chunk.decode('utf-16-le', errors='ignore')
                texts.append(text)
            except Exception:
                pass
        
        pos += size
    return texts

def extract_hwp(path, max_chars=4000):
    try:
        import olefile
        ole = olefile.OleFileIO(path)
        dirs = ole.listdir()
        section_paths = []
        for d in dirs:
            if len(d) == 2 and d[0] == 'BodyText' and d[1].startswith('Section'):
                section_paths.append(d)
        
        section_paths.sort()
        all_paragraphs = []
        
        for s_path in section_paths:
            data = ole.openstream(s_path).read()
            raw = decompress_hwp_stream(data)
            texts = extract_text_from_hwp_section(raw)
            for t in texts:
                clean_t = "".join(c for c in t if ord(c) >= 32 or c in '\n\t')
                clean_t = clean_t.strip()
                if clean_t:
                    all_paragraphs.append(clean_t)
            if sum(len(p) for p in all_paragraphs) >= max_chars:
                break
        ole.close()
        return "\n\n".join(all_paragraphs)[:max_chars]
    except Exception as e:
        return f"[HWP 추출 실패: {e}]"

def extract_hwpx(path, max_chars=4000):
    paragraphs = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.lower().endswith("prvtext.txt"):
                    return archive.read(name).decode("utf-8", errors="ignore")[:max_chars]
            
            xml_names = [
                name for name in archive.namelist()
                if name.lower().endswith(".xml")
                and ("contents/" in name.lower() or "section" in name.lower())
                and "bindata/" not in name.lower()
            ]
            for name in sorted(xml_names):
                if sum(len(p) for p in paragraphs) >= max_chars:
                    break
                data = archive.read(name)
                try:
                    from xml.etree import ElementTree
                    root = ElementTree.fromstring(data)
                    current = []
                    for node in root.iter():
                        suffix = node.tag.rsplit("}", 1)[-1]
                        if suffix == "t" and node.text:
                            current.append(node.text)
                        if suffix in {"p", "tr"} and current:
                            paragraph = "".join(current).strip()
                            if paragraph:
                                paragraphs.append(paragraph)
                            current = []
                except Exception:
                    pass
        return "\n\n".join(paragraphs)[:max_chars]
    except Exception as e:
        return f"[HWPX 추출 실패: {e}]"

def extract_pdf(path, max_chars=4000):
    try:
        import pypdf
        pages = []
        reader = pypdf.PdfReader(path)
        for idx, page in enumerate(reader.pages):
            if sum(len(p) for p in pages) >= max_chars:
                break
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text.strip())
        return "\n\n".join(pages)[:max_chars]
    except Exception as e:
        return f"[PDF 추출 실패: {e}]"

def extract_docx(path, max_chars=4000):
    try:
        from xml.etree import ElementTree
        paragraphs = []
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ElementTree.fromstring(xml_content)
            for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                texts = [node.text for node in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                if texts:
                    paragraphs.append("".join(texts).strip())
        return "\n\n".join(paragraphs)[:max_chars]
    except Exception as e:
        return f"[DOCX 추출 실패: {e}]"

def extract_pptx(path, max_chars=4000):
    try:
        from xml.etree import ElementTree
        paragraphs = []
        with zipfile.ZipFile(path) as pptx:
            slide_names = [name for name in pptx.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
            slide_names.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else x)
            for name in slide_names:
                if sum(len(p) for p in paragraphs) >= max_chars:
                    break
                xml_content = pptx.read(name)
                root = ElementTree.fromstring(xml_content)
                texts = [node.text for node in root.iter() if node.tag.endswith('t') and node.text]
                if texts:
                    paragraphs.append(" ".join(texts).strip())
        return "\n\n".join(paragraphs)[:max_chars]
    except Exception as e:
        return f"[PPTX 추출 실패: {e}]"

def extract_xlsx(path, max_chars=4000):
    try:
        import openpyxl
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        chunks = []
        for sheet in workbook.worksheets[:3]:
            rows = []
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
                values = [str(value).strip() for value in row if value is not None and str(value).strip()]
                if values:
                    rows.append(" | ".join(values[:10]))
                if row_idx >= 30:
                    break
            if rows:
                chunks.append(f"[{sheet.title}]\n" + "\n".join(rows))
            if sum(len(c) for c in chunks) >= max_chars:
                break
        workbook.close()
        return "\n\n".join(chunks)[:max_chars]
    except Exception as e:
        return f"[Excel 추출 실패: {e}]"

def extract_txt(path, max_chars=4000):
    try:
        with open(path, 'rb') as f:
            data = f.read()
        for encoding in ('utf-8-sig', 'utf-8', 'cp949', 'euc-kr'):
            try:
                return data.decode(encoding)[:max_chars]
            except UnicodeDecodeError:
                continue
        return data.decode('utf-8', errors='replace')[:max_chars]
    except Exception as e:
        return f"[TXT 추출 실패: {e}]"

def extract_document_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".hwp":
        return extract_hwp(path)
    elif ext == ".hwpx":
        return extract_hwpx(path)
    elif ext == ".pdf":
        return extract_pdf(path)
    elif ext == ".docx":
        return extract_docx(path)
    elif ext == ".xlsx" or ext == ".xls" or ext == ".xlsm":
        return extract_xlsx(path)
    elif ext == ".pptx" or ext == ".ppt":
        return extract_pptx(path)
    elif ext == ".txt" or ext == ".md":
        return extract_txt(path)
    return ""

def main():
    if not os.path.exists(DESKTOP_DIR):
        print(f"Error: Desktop directory {DESKTOP_DIR} not found.")
        return 1
        
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
    files_to_organize = []
    for entry in os.scandir(DESKTOP_DIR):
        if entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in ALLOWED_EXTENSIONS and not entry.name.startswith("~") and not entry.name.startswith("."):
                if entry.name.lower() not in ["desktop.ini"]:
                    files_to_organize.append(entry)

    print(f"Found {len(files_to_organize)} files to extract.")
    
    records = []
    for idx, entry in enumerate(files_to_organize, start=1):
        print(f"[{idx}/{len(files_to_organize)}] Extracting: {entry.name}")
        content = extract_document_text(entry.path)
        records.append({
            "path": entry.path,
            "filename": entry.name,
            "content": content
        })
        
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
        
    print(f"Extraction complete. Saved {len(records)} records to {OUTPUT_JSON}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
