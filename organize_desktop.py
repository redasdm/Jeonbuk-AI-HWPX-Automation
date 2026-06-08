# -*- coding: utf-8 -*-
"""
바탕화면 파일 정리 및 위키/옵시디언 동기화 자동화 스크립트
(Desktop File Organizer and Sync Skill)

이 스크립트는 바탕화면의 주요 문서 파일들을 읽어 내용을 분석하고,
1) 업무 폴더 내의 가장 어울리는 하위 폴더로 이동합니다.
2) 문서 내용을 로컬 LLM(Ollama gemma4)으로 요약하여 옵시디언 볼트에 노트를 생성합니다.
3) 업무 위키(LLM 위키) 갱신 스크립트를 실행하여 위키 색인을 최신화합니다.
"""

import os
import shutil
import re
import urllib.request
import json
import datetime as dt
import zipfile
import zlib
import struct
import argparse
import sys

# ==========================================
# 0. 인코딩 안전 출력 함수 정의 (Safe Print Redefinition)
# ==========================================
_original_print = print

def print(*args, **kwargs):
    file = kwargs.get('file', sys.stdout)
    if file not in (sys.stdout, sys.stderr):
        _original_print(*args, **kwargs)
        return
        
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    msg = sep.join(str(arg) for arg in args) + end
    
    try:
        file.write(msg)
        file.flush()
    except UnicodeEncodeError:
        encoding = getattr(file, 'encoding', 'utf-8') or 'utf-8'
        safe_msg = msg.encode(encoding, errors='replace').decode(encoding)
        file.write(safe_msg)
        file.flush()


# 기본 설정 경로
DESKTOP_DIR = r"C:\Users\redas\OneDrive\Desktop"
WORK_DIR = r"C:\Users\redas\OneDrive\Desktop\업무"
OBSIDIAN_DIR = r"C:\Users\redas\OneDrive\Desktop\ObsidianVault"
WIKI_DIR = r"C:\Users\redas\OneDrive\Desktop\업무-wiki"

# 대상 문서 확장자
ALLOWED_EXTENSIONS = {
    ".hwp", ".hwpx", ".pdf", ".docx", ".doc",
    ".xlsx", ".xls", ".xlsm", ".pptx", ".ppt",
    ".txt", ".md"
}

# 로컬 Ollama API 설정
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "gemma4:latest"

# ==========================================
# 1. 텍스트 추출 엔진 (Text Extraction Engines)
# ==========================================

def decompress_hwp_stream(data):
    """HWP 스트림 데이터 압축 해제"""
    try:
        return zlib.decompress(data, -15)
    except Exception:
        try:
            return zlib.decompress(data)
        except Exception:
            return data

def extract_text_from_hwp_section(raw_data):
    """HWP Section 바이너리에서 텍스트 태그(HWPTAG_PARA_TEXT=67) 추출"""
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
        
        # Tag 67: HWPTAG_PARA_TEXT
        if tag == 67:
            try:
                text = chunk.decode('utf-16-le', errors='ignore')
                texts.append(text)
            except Exception:
                pass
        
        pos += size
    return texts

def extract_hwp(path, max_chars=4000):
    """OLE HWP 파일에서 텍스트 추출"""
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
                # 제어 문자 제거 및 정제
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
    """Zip HWPX 파일에서 텍스트 추출"""
    paragraphs = []
    try:
        with zipfile.ZipFile(path) as archive:
            # prvText.txt가 존재하면 우선적으로 사용
            for name in archive.namelist():
                if name.lower().endswith("prvtext.txt"):
                    return archive.read(name).decode("utf-8", errors="ignore")[:max_chars]
            
            # 그렇지 않으면 section XML 파일들을 순회 파싱
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
    """PDF 파일에서 텍스트 추출"""
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
    """Word DOCX 파일에서 w:t 노드 파싱하여 텍스트 추출 (외부 라이브러리 의존성 없음)"""
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
    """PowerPoint PPTX 파일에서 슬라이드별 a:t 노드 파싱하여 텍스트 추출"""
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
    """Excel XLSX 파일 시트별 데이터 추출"""
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
    """인코딩 감지 후 텍스트 파일 로드"""
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
    """확장자별 알맞은 텍스트 추출 함수 매핑"""
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

# ==========================================
# 2. 로컬 LLM (Ollama) 연동 및 행정 기능
# ==========================================

def ask_ollama(prompt, system_instruction=""):
    """로컬 Ollama 서비스에 질의 수행"""
    data = {
        "model": OLLAMA_MODEL,
        "messages": [],
        "options": {
            "temperature": 0.1
        },
        "stream": False
    }
    if system_instruction:
        data["messages"].append({"role": "system", "content": system_instruction})
    data["messages"].append({"role": "user", "content": prompt})
    
    req = urllib.request.Request(
        OLLAMA_API_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["message"]["content"].strip()
    except Exception as e:
        print(f"Ollama 호출 오류: {e}")
        return f"Error: {e}"

def get_work_folders(work_dir):
    """업무 폴더의 하위 폴더 목록 로드"""
    folders = []
    if not os.path.exists(work_dir):
        return []
    for entry in os.scandir(work_dir):
        if entry.is_dir() and not entry.name.startswith('.') and entry.name not in ['hwpx', 'hwpx-only-repo']:
            folders.append(entry.name)
    folders.sort()
    return folders

def get_obsidian_project_folders(obsidian_dir):
    """옵시디언의 프로젝트 폴더 목록 로드"""
    projects_dir = os.path.join(obsidian_dir, "10 Projects")
    if not os.path.exists(projects_dir):
        return []
    folders = []
    for entry in os.scandir(projects_dir):
        if entry.is_dir() and not entry.name.startswith('.'):
            folders.append(entry.name)
    folders.sort()
    return folders

def classify_file(filename, file_content, work_folders):
    """파일을 업무 폴더 중 적합한 곳으로 분류"""
    folders_str = "\n".join(f"- {f}" for f in work_folders)
    prompt = f"""당신은 전북교육청의 교육전문직원 업무 문서를 관리하는 지능형 에이전트입니다.
제시된 파일명과 파일 내용 일부를 분석하여, 아래의 업무 폴더 리스트 중 가장 어울리는 폴더 하나를 매칭해 주세요.

[분류 대상 파일 정보]
- 파일명: {filename}
- 파일 내용 일부 (앞부분):
{file_content[:1500]}

[업무 폴더 후보 리스트]
{folders_str}

[매칭 규칙]
1. 반드시 위의 후보 리스트에 나열된 폴더 이름 중 하나만 정확하게 선택해 주세요.
2. 어떤 폴더에도 명확히 어울리지 않거나 판단이 어려울 경우 '기타'를 선택해 주세요.
3. 응답할 때는 다른 수식어나 마크다운 기호 없이 오직 **선택한 폴더 이름만 단 한 줄로** 출력해 주세요. 예: '26 AI 중점학교' 또는 '미래교육캠퍼스'
"""
    system_instruction = "당신은 주어진 파일에 가장 적절한 폴더명을 후보 목록에서 하나만 정확히 선택해 출력하는 로봇입니다. 부가적인 텍스트나 설명은 절대 하지 마십시오."
    result = ask_ollama(prompt, system_instruction)
    result = result.strip().strip("'\"`*[]")
    
    if result in work_folders:
        return result
    
    # 유사 매칭
    for folder in work_folders:
        if folder.lower() in result.lower() or result.lower() in folder.lower():
            return folder
            
    return "기타"

def classify_obsidian_folder(chosen_work_folder, obsidian_folders):
    """업무 폴더명을 옵시디언 프로젝트 폴더명에 매칭"""
    if chosen_work_folder == "기타":
        return "00 Inbox"
    
    if chosen_work_folder in obsidian_folders:
        return f"10 Projects/{chosen_work_folder}"
        
    folders_str = "\n".join(f"- {f}" for f in obsidian_folders)
    prompt = f"""업무 분류 폴더명 '{chosen_work_folder}'에 가장 대응되는 옵시디언 프로젝트 폴더를 선택해 주세요.

[옵시디언 프로젝트 폴더 리스트]
{folders_str}

[매칭 규칙]
1. 반드시 위의 리스트에 있는 폴더 이름 중 하나만 선택해 주세요.
2. 어울리는 프로젝트 폴더가 전혀 없을 경우 '00 Inbox'를 반환해 주세요.
3. 응답 시 다른 설명 없이 오직 **매칭되는 폴더 이름만** 출력해 주세요. 예: '26 AI 중점학교'
"""
    system_instruction = "주어진 리스트에서 가장 매칭되는 폴더명을 단 한 줄로 정확히 출력하세요."
    result = ask_ollama(prompt, system_instruction).strip().strip("'\"`*[]")
    
    if result in obsidian_folders:
        return f"10 Projects/{result}"
        
    # 유사 매칭
    for folder in obsidian_folders:
        if folder.lower() in result.lower() or result.lower() in folder.lower():
            return f"10 Projects/{folder}"
            
    return "00 Inbox"

def generate_summary(filename, file_content):
    """문서 내용 한글 요약본 작성"""
    # 에러 메시지나 빈 텍스트 체크
    if not file_content.strip() or file_content.startswith("[") and file_content.endswith("]"):
        return f"- 파일 이름: {filename}\n- 텍스트를 추출할 수 없어 요약을 생성하지 못했습니다. 원본 문서를 참고해 주세요."

    prompt = f"""다음 교육청 문서의 내용을 읽고, 핵심 사항을 3~5개의 개조식 문장(Bullet points)으로 한글 요약해 주세요.

문서 제목: {filename}
문서 내용:
{file_content[:3000]}

[요약 규칙]
1. 문서의 핵심 목적, 추진 계획, 주요 내용, 관련 담당 또는 예산 정보를 포함해 주세요.
2. 격식 있는 교육청 공문서 요약 투(~함, ~계획임, ~것으로 판단됨 등) 또는 명확한 존댓말로 작성해 주세요.
3. 요약 외에 다른 불필요한 설명은 하지 마십시오.
"""
    system_instruction = "당신은 교육청 업무 문서를 읽고 핵심 내용을 간결하게 개조식으로 요약하는 행정 전문가입니다."
    return ask_ollama(prompt, system_instruction)

def determine_tags(filename, summary, file_content):
    """문서 분류 태그 결정"""
    tags = set()
    filename_lower = filename.lower()
    
    # 룰 기반 기본 키워드 매핑
    if "ai" in filename_lower or "중점학교" in filename_lower or "인공지능" in filename_lower:
        tags.add("AI")
    if "교육" in filename_lower or "학습" in filename_lower or "에듀테크" in filename_lower:
        tags.add("education")
    if "보고서" in filename_lower or "계획" in filename_lower or "요약" in filename_lower:
        tags.add("report")
    if "예산" in filename_lower or "추경" in filename_lower or "정산" in filename_lower:
        tags.add("budget")
    if "미래교육캠퍼스" in filename_lower:
        tags.add("미래교육캠퍼스")
        tags.add("project")
    if "협상" in filename_lower or "계약" in filename_lower:
        tags.add("negotiation")
    if "평가" in filename_lower or "정성평가" in filename_lower:
        tags.add("evaluation")
        
    # LLM 태그 추천 질의
    prompt = f"""파일명 '{filename}'과 아래 문서 요약의 맥락에 어울리는 대표 한글 태그 2~3개를 쉼표(,)로 구분해서 작성해 주세요.
(예: 'AI, 교육혁신, 계획서')

[문서 요약]
{summary}

응답에는 다른 설명 없이 오직 태그만 쉼표로 구분해서 한 줄로 적어주세요.
"""
    system_instruction = "문서의 핵심 맥락에 어울리는 태그 2~3개를 쉼표로만 구분해서 출력하세요."
    res = ask_ollama(prompt, system_instruction).strip().strip("'\"`*[]")
    
    for t in res.split(","):
        t_clean = t.strip()
        if t_clean and len(t_clean) < 15 and not t_clean.startswith("Error"):
            tags.add(t_clean)
            
    return sorted(list(tags))

# ==========================================
# 3. 파일 작업 실행 및 연동
# ==========================================

def move_file_with_collision_handling(src_path, dest_dir, dry_run=False):
    """파일 이동 및 충돌 시 고유 숫자 접미사 부여"""
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)
    
    if not os.path.exists(dest_dir) and not dry_run:
        os.makedirs(dest_dir, exist_ok=True)
        
    if not os.path.exists(dest_path):
        if not dry_run:
            shutil.move(src_path, dest_path)
        return dest_path
        
    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_dest_path = os.path.join(dest_dir, new_filename)
        if not os.path.exists(new_dest_path):
            if not dry_run:
                shutil.move(src_path, new_dest_path)
            return new_dest_path
        counter += 1

def create_obsidian_note(filename, dest_path, category_folder, summary, file_content, tags, obsidian_dir, dry_run=False):
    """옵시디언 마크다운 요약 노트 생성"""
    target_vault_dir = os.path.join(obsidian_dir, category_folder)
    
    name, _ = os.path.splitext(filename)
    note_filename = f"{name}.md"
    note_path = os.path.join(target_vault_dir, note_filename)
    
    # 메타데이터를 위한 파일 스태트
    mtime = dt.datetime.now().isoformat(timespec="seconds")
    size = 0
    if os.path.exists(dest_path):
        stat = os.stat(dest_path)
        mtime = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        size = stat.st_size
    
    # Frontmatter 태그 배열 포맷
    tags_formatted = ", ".join(f"'{t}'" for t in tags)
    
    # 텍스트 노출 제한
    preview_content = file_content[:1500] if file_content else "(본문 텍스트 없음)"
    
    lines = [
        "---",
        f"title: \"{name}\"",
        f"source_path: \"{dest_path.replace('\\\\', '/').replace('\\', '/')}\"",
        f"created_at: \"{dt.datetime.now().isoformat(timespec='seconds')}\"",
        f"mtime: \"{mtime}\"",
        f"size: {size}",
        f"tags: [{tags_formatted}]",
        "---",
        "",
        f"# {name}",
        "",
        "## 📌 문서 개요 및 요약",
        "",
        summary,
        "",
        "## 📂 파일 정보",
        "",
        f"- **실제 파일 경로**: `{dest_path}`",
        f"- **파일 크기**: `{size:,} bytes`" if size > 0 else "- **파일 크기**: (이동 대기 중)",
        f"- **최종 수정일**: `{mtime}`",
        "",
        "## 📝 주요 본문 발췌 (앞부분)",
        "",
        "```text",
        preview_content,
        "```"
    ]
    
    note_content = "\n".join(lines) + "\n"
    
    if not dry_run:
        os.makedirs(target_vault_dir, exist_ok=True)
        # 만약 옵시디언 파일명 충돌이 나면 덮어쓰거나 고유하게 만듦
        if os.path.exists(note_path):
            note_name_stem, note_ext = os.path.splitext(note_filename)
            c = 1
            while True:
                new_note_filename = f"{note_name_stem}_{c}{note_ext}"
                new_note_path = os.path.join(target_vault_dir, new_note_filename)
                if not os.path.exists(new_note_path):
                    note_path = new_note_path
                    break
                c += 1
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(note_content)
            
    return note_path, note_content

def rebuild_wiki(wiki_dir):
    """업무-wiki 빌드 스크립트 실행"""
    bat_path = os.path.join(wiki_dir, "update_work_wiki.bat")
    if os.path.exists(bat_path):
        print("=" * 60)
        print("업무 위키(LLM 위키) 인덱스 업데이트 빌드를 수행합니다...")
        import subprocess
        try:
            # 윈도우 환경에서 비동기 배치가 아닌 동기 실행
            result = subprocess.run([bat_path], cwd=wiki_dir, capture_output=True, text=True, shell=True)
            print("위키 업데이트 빌드 완료.")
            print(result.stdout[:500] + "\n..." if len(result.stdout) > 500 else result.stdout)
            if result.stderr:
                print("위키 빌드 경고/오류:")
                print(result.stderr)
        except Exception as e:
            print(f"위키 스크립트 실행 실패: {e}")
    else:
        print(f"경고: 위키 업데이트 배치 파일({bat_path})을 찾을 수 없습니다.")

# ==========================================
# 4. 메인 실행 엔트리
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="바탕화면의 파일들을 분류 정리하고 요약 노트를 생성합니다.")
    parser.add_argument("--source", default=DESKTOP_DIR, help="정리할 소스 폴더 (기본: 바탕화면)")
    parser.add_argument("--work", default=WORK_DIR, help="업무 원본 폴더 경로")
    parser.add_argument("--obsidian", default=OBSIDIAN_DIR, help="옵시디언 볼트 폴더 경로")
    parser.add_argument("--wiki", default=WIKI_DIR, help="업무-wiki 폴더 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 이동이나 파일 작성을 하지 않고 화면에 작업 시뮬레이션 출력")
    args = parser.parse_args()

    print("=" * 60)
    print("바탕화면 파일 정리 및 요약/동기화 스킬 스크립트 시작")
    print(f"모드: {'[시뮬레이션 모드 (Dry Run)]' if args.dry_run else '[실제 실행 모드 (Live)]'}")
    print(f"소스 폴더: {args.source}")
    print(f"업무 폴더: {args.work}")
    print(f"옵시디언 볼트: {args.obsidian}")
    print(f"업무 위키: {args.wiki}")
    print("=" * 60)

    # 1. 대상 폴더 존재 확인 및 초기 설정
    if not os.path.exists(args.source):
        print(f"오류: 소스 폴더가 존재하지 않습니다. ({args.source})")
        return 1
    
    work_folders = get_work_folders(args.work)
    obsidian_project_folders = get_obsidian_project_folders(args.obsidian)
    
    if not work_folders:
        print(f"경고: 업무 폴더 내의 하위 폴더들을 찾을 수 없습니다. 경로를 확인해 주세요. ({args.work})")
        return 1

    # 2. 바탕화면의 파일 수집
    files_to_organize = []
    for entry in os.scandir(args.source):
        # 파일이며, 점 파일이나 지정하지 않은 확장자 제외
        if entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in ALLOWED_EXTENSIONS and not entry.name.startswith("~") and not entry.name.startswith("."):
                # desktop.ini 또는 스크립트 파일들 제외
                if entry.name.lower() not in ["desktop.ini"]:
                    files_to_organize.append(entry.path)

    print(f"정리 대상 파일 목록 ({len(files_to_organize)}개 발견):")
    for f in files_to_organize:
        print(f"  - {os.path.basename(f)}")
    print("-" * 60)

    if not files_to_organize:
        print("정리할 대상 문서 파일이 바탕화면에 없습니다. 작업을 종료합니다.")
        return 0

    processed_count = 0

    # 3. 파일 순회 처리
    for file_path in files_to_organize:
        filename = os.path.basename(file_path)
        print(f"\n[{processed_count + 1}/{len(files_to_organize)}] 분석 중: {filename}")
        
        # 3.1. 텍스트 추출
        print("  -> 텍스트 추출 중...")
        content = extract_document_text(file_path)
        print(f"  -> 텍스트 추출 완료 (길이: {len(content)}자)")
        
        # 3.2. 업무 폴더 분류
        print("  -> Ollama 분류 중...")
        chosen_work_folder = classify_file(filename, content, work_folders)
        print(f"  -> 분류 결과: [업무/{chosen_work_folder}]")
        
        # 3.3. Obsidian 매칭 폴더 분류
        print("  -> Obsidian 대응 폴더 매칭 중...")
        chosen_obsidian_folder = classify_obsidian_folder(chosen_work_folder, obsidian_project_folders)
        print(f"  -> 매칭 결과: [Obsidian/{chosen_obsidian_folder}]")
        
        # 3.4. 요약 생성
        print("  -> 문서 요약 작성 중...")
        summary = generate_summary(filename, content)
        print("  -> 요약 완료.")
        
        # 3.5. 태그 추천
        print("  -> 태그 분석 중...")
        tags = determine_tags(filename, summary, content)
        print(f"  -> 추천 태그: {tags}")
        
        # 3.6. 파일 이동
        target_dir = os.path.join(args.work, chosen_work_folder)
        print(f"  -> 파일 이동 중: {filename} -> 업무/{chosen_work_folder}/")
        
        if args.dry_run:
            # 시뮬레이션 경로 설정
            new_file_path = os.path.join(target_dir, filename)
            print(f"  [Dry Run] 이동될 실제 파일 경로 (예정): {new_file_path}")
        else:
            new_file_path = move_file_with_collision_handling(file_path, target_dir, dry_run=False)
            print(f"  -> 이동 완료: {os.path.basename(new_file_path)}")
            
        # 3.7. Obsidian 노트 생성
        print(f"  -> Obsidian 노트 생성 중: {chosen_obsidian_folder}/")
        note_path, note_content = create_obsidian_note(
            filename, new_file_path, chosen_obsidian_folder,
            summary, content, tags, args.obsidian, args.dry_run
        )
        
        if args.dry_run:
            print(f"  [Dry Run] Obsidian 노트 저장 위치 (예정): {note_path}")
            print("  --- [시뮬레이션 생성된 노트 내용] ---")
            print(note_content[:600] + "\n...(생략)\n----------------------------------")
        else:
            print(f"  -> Obsidian 노트 생성 완료: {os.path.basename(note_path)}")
            
        processed_count += 1

    print("\n" + "=" * 60)
    print(f"모든 파일의 이동 및 옵시디언 요약 노트 생성 완료. (총 {processed_count}개)")
    print("=" * 60)

    # 4. 최종 LLM 위키 빌드 갱신
    if not args.dry_run:
        rebuild_wiki(args.wiki)
    else:
        print("[Dry Run] 위키 빌드 갱신 시뮬레이션 (실제로는 update_work_wiki.bat를 가동함)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
