# 바탕화면 파일 정리 및 위키/옵시디언 동기화 스킬 (Desktop Organizer Skill)

## 🎯 목적 (Purpose)
바탕화면에 있는 다양한 문서 파일들(.hwp, .hwpx, .pdf, .docx, .xlsx, .pptx, .txt 등)의 이름과 본문 내용을 파악하여,
1) 업무 폴더(`업무`) 내 적절한 프로젝트 서브 폴더로 분류 및 이동시킵니다.
2) 문서 내용을 로컬 LLM(Ollama gemma4)으로 요약하고 대표 태그를 생성하여 옵시디언 볼트(`ObsidianVault`)에 마크다운 요약 노트를 생성합니다.
3) 최종적으로 `업무-wiki` 빌드 자동화를 실행하여 LLM 위키에 동기화합니다.

---

## 📂 기본 경로 설정 (Paths)
- **바탕화면 경로**: `C:\Users\redas\OneDrive\Desktop`
- **업무 원본 폴더**: `C:\Users\redas\OneDrive\Desktop\업무`
- **옵시디언 볼트**: `C:\Users\redas\OneDrive\Desktop\ObsidianVault`
- **업무 위키**: `C:\Users\redas\OneDrive\Desktop\업무-wiki`

---

## ⚙️ 실행 방법 및 명령 (Execution Instructions)

자동화는 `organize_desktop.py` 스크립트를 통해 작동하며, 윈도우 파워쉘/터미널 등에서 아래 명령어로 직접 가동하거나 에이전트가 호출할 수 있습니다.

### 1. 드라이 런 / 시뮬레이션 모드 (Dry Run)
실제 바탕화면의 파일을 이동하거나 옵시디언 노트를 저장하지 않고, 분석 결과를 미리 스크린으로 확인하고 싶을 때 사용합니다.
```powershell
python C:\Users\redas\OneDrive\Desktop\AntiGravity\organize_desktop.py --dry-run
```

### 2. 실제 실행 모드 (Live Execution)
바탕화면의 파일들을 분류하여 이동하고, 옵시디언 노트를 빌드한 뒤, 위키 색인 업데이트까지 한 번에 완수합니다.
```powershell
python C:\Users\redas\OneDrive\Desktop\AntiGravity\organize_desktop.py
```

---

## 🧠 핵심 프로세스 흐름 (Workflow)

1. **바탕화면 스캔**: 바탕화면에 임시 혹은 새로 추가된 `.hwp`, `.hwpx`, `.pdf` 등 문서 파일들을 감지합니다.
2. **텍스트 추출**: 각 문서 유형의 바이너리 및 XML 노드를 직접 읽어와 본문 앞부분(최대 4000자)을 텍스트로 추출합니다.
3. **LLM 분류**: 로컬 Ollama (`gemma4:latest`)를 활용해 파일명 및 본문을 분석하여 `업무` 폴더의 하위 폴더 중 가장 어울리는 폴더명과 옵시디언 프로젝트 폴더명을 자동으로 매칭합니다. (매칭하기 힘든 경우 `기타`/`00 Inbox` 폴더로 지정)
4. **안전한 이동**: 파일명 충돌을 방지하기 위해 동일 이름의 파일이 목적지에 있을 경우 고유 번호 접미사(예: `_1`)를 부여하여 안전하게 이동시킵니다.
5. **옵시디언 요약본 및 태그 작성**: 
   - 프론트매터(YAML) 메타데이터(제목, 이동일, 원본파일경로, 태그) 및 `## 개요`, `## 요약`, `## 본문 일부` 형식을 갖춘 요약 노트(.md)를 매칭된 프로젝트 폴더에 직접 생성합니다.
   - 태그는 규칙 기반 키워드 매핑과 LLM 추천 태그를 결합하여 지능적으로 할당합니다.
6. **업무 위키 갱신**: 파일 이동 후 `update_work_wiki.bat` 파일을 실행하여, 새로 정리된 문서들이 LLM 위키 인덱스에 자동 반영되도록 갱신합니다.
