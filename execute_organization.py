# -*- coding: utf-8 -*-
"""
바탕화면 파일 정리 및 위키/옵시디언 동기화 실행 스크립트
(High-Precision Desktop File Organizer and Sync Executor)

이 스크립트는 Gemini 에이전트가 완벽히 분석한 분류, 요약, 태그 데이터를 바탕으로
실제 파일 이동, 옵시디언 노트 작성, 업무 위키 빌드를 일괄 수행합니다.
"""

import os
import shutil
import json
import datetime as dt
import subprocess
import sys
import unicodedata

# 기본 설정 경로
DESKTOP_DIR = r"C:\Users\redas\OneDrive\Desktop"
WORK_DIR = r"C:\Users\redas\OneDrive\Desktop\업무"
OBSIDIAN_DIR = r"C:\Users\redas\OneDrive\Desktop\ObsidianVault"
WIKI_DIR = r"C:\Users\redas\OneDrive\Desktop\업무-wiki"
JSON_PATH = r"C:\Users\redas\.gemini\antigravity\brain\48219d81-e4d8-4230-8f36-af86eb7d8050\scratch\desktop_files_info.json"

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

# ==========================================
# 1. 고정밀 분류 및 요약 데이터 세트 (Gemini Analysis Data)
# ==========================================

MAPPINGS = [
  {
    "filename": "(미래교육과) 20대 교육감 공약별 예산 편성 현황(AI디지털).xlsx",
    "work_folder": "예산",
    "obsidian_folder": "예산",
    "summary": "- 20대 교육감 공약 사업에 따른 미래교육과의 예산 편성 현황입니다.\n- 주요 사업으로는 AI교육 중점학교(9.3억), 미래교육캠퍼스 증축(81.2억), 디지털 튜터 운영(50.5억), 교육용 범용 SW 지원(7.5억) 등이 포함되어 있습니다.\n- 각 공약의 주요 정책 과제(AI 학습코칭 플랫폼 구축, 기초학력 책임제 등)와 1회 추경 요구액, 기정 예산 현황을 총괄적으로 정리하고 있습니다.",
    "tags": ["예산", "공약", "AI디지털"]
  },
  {
    "filename": "(미래교육과-N1 (첨부)) 붙임_미래교육캠퍼스 협상기본안 작성 회의 참석자 명단.hwp",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 협상 기본안 작성을 위한 회의 참석자 명단 파일입니다.\n- 캠퍼스 설립 관련 과업 지시 및 세부 협상 추진을 조율하기 위해 구성된 관계자들의 정보가 수록되어 있습니다.",
    "tags": ["미래교육캠퍼스", "협상", "회의참석자"]
  },
  {
    "filename": "(붙임1) 온라인 연수 안내.hwp",
    "work_folder": "기타",
    "obsidian_folder": "00 Inbox",
    "summary": "- 교원을 대상으로 하는 '학교 수업·업무에 바로 쓰는 AI 활용법' 온라인 연수 안내 문서입니다.\n- AI 도구(issamGPT 및 미리캔버스)를 활용한 수업 지도 및 업무 효율화 방법을 다룹니다.\n- 일시는 2026년 6월 2일(화) 18:30 ~ 21:00이며, 실시간 라이브로 무료 중계 및 진행되는 일정과 프로그램 정보를 포함하고 있습니다.",
    "tags": ["연수", "AI활용", "미리캔버스"]
  },
  {
    "filename": "(작성) 2026년 제1회 추경 주민참여 의견서에 대한 검토의견 및 향후 대책.hwp",
    "work_folder": "예산",
    "obsidian_folder": "예산",
    "summary": "- 2026년도 제1회 추가경정예산안(추경) 중 주민참여 예산 의견서에 대한 미래교육과의 공식 검토 의견 및 대응 대책 수립 문서입니다.\n- 주민들이 제안한 에듀테크 및 미래교육 사업의 실효성을 분석하고, 향후 대책 예산 확보 필요성을 소명하고 있습니다.",
    "tags": ["예산", "추경", "주민참여"]
  },
  {
    "filename": "2. 2026 교육학습공동체 모집 현황(000).xlsx",
    "work_folder": "연구회운영",
    "obsidian_folder": "연구회운영",
    "summary": "- 2026학년도 도교육청 부서별 교육학습공동체(연구회, 교사연수회, 학생 동아리 등) 모집 및 편성 현황 계획입니다.\n- 인문·예술교육 교과연구회, 독서 동아리, 장애학생 행동중재 연구회 등 부서별 공동체 운영 계획과 1팀당 지원 금액(100만~200만 원 선), 담당 부서 및 담당 장학사 연락처가 상세히 기록되어 있습니다.",
    "tags": ["연구회운영", "교육학습공동체", "교사지원"]
  },
  {
    "filename": "2024_2025_AI정보교육_운영성과_발전적방향.pdf",
    "work_folder": "26 AI 중점학교",
    "obsidian_folder": "26 AI 중점학교",
    "summary": "- 2024년(101개교) 및 2025년(92개교) AI정보교육 중심학교의 운영 성과와 애로사항을 비교 분석한 정성평가용 결과서입니다.\n- 장비 도입 중심(2024)에서 수업 내실화 및 생성형 AI 윤리·저작권 교육 요구 등 질적 고도화(2025)로 수요가 진화했음을 보여줍니다.\n- 인프라 고도화, 교원 전문성, 교육과정 연계, 예산 지원 정책 분석을 토대로 향후 정책 수립 시사점(에듀테크 소프트랩 연계 등)을 제안합니다.",
    "tags": ["AI정보교육", "정성평가", "중심학교"]
  },
  {
    "filename": "2026년 AI 중점학교 보조인력 지원 운영 계획(안).hwp",
    "work_folder": "26 AI 중점학교",
    "obsidian_folder": "26 AI 중점학교",
    "summary": "- 2026년 AI 중점학교의 원활한 운영 및 교원 행정 업무 경감을 위한 보조인력 채용 및 지원 세부 계획안입니다.\n- 보조인력의 자격 요건, 근태 관리, 담당 업무(AI 실습 수업 보조, 장비 관리 및 연수 기획 등)와 예산 지원 지침을 명시하고 있습니다.",
    "tags": ["AI중점학교", "보조인력", "운영계획"]
  },
  {
    "filename": "2026년 제3차 디지털교육혁신 특별교부금(AI 중점학교) 수요조사 계획v2(전북).hwpx",
    "work_folder": "26 AI 중점학교",
    "obsidian_folder": "26 AI 중점학교",
    "summary": "- 교육부 인공지능교육진흥과 주관 2026년 제3차 디지털 교육혁신 특별교부금(AI 중점학교) 배분을 위한 예산 수요조사 계획입니다.\n- 2026년 6월~12월 동안 운영되는 AI 중점학교 보조인력 예산 지원(총 120억 원 규모)이 핵심이며, 전북의 경우 81개교를 대상으로 29.6억 원이 예산 배분안으로 수립되어 이에 대한 시도교육청별 수요를 제출하도록 하고 있습니다.",
    "tags": ["특별교부금", "AI중점학교", "수요조사"]
  },
  {
    "filename": "2026년 하반기 주요업무보고(취합중).hwp",
    "work_folder": "주요업무보고",
    "obsidian_folder": "보고자료",
    "summary": "- 2026년 하반기 미래교육과의 주요 업무 추진 계획 및 예산 집행 현황을 취합한 보고서 초안입니다.\n- 전년도 이월 예산 및 집행 예산 현황, 세부 사업명과 상반기 추진 실적 및 하반기 전략적 방향성을 명시하고 있습니다.",
    "tags": ["업무보고", "예산집행", "미래교육과"]
  },
  {
    "filename": "2027년 전북 AI중점학교 81개교 설정근거 분석 보고서.pdf",
    "work_folder": "26 AI 중점학교",
    "obsidian_folder": "26 AI 중점학교",
    "summary": "- 2027년 전북 AI 중점학교의 81개교 체제 보존 타당성과 예산 삭감 우려에 대한 재정 복원력 확보 방안을 담은 분석 보고서입니다.\n- 윤석열 정부의 AIDT 사업 폐지에 대응하여, 기보급된 스마트기기 인프라(CapEx 0원 선언)를 백분 활용하는 소프트웨어/운영 중심(OpEx) 모델을 제안합니다.\n- 특별교부금(74%)과 도교육청 자체예산(26%) 구조 하에서 지정 학교 수의 유지와 '탄력적 예산 슬라이딩 배분 모델' 수립 필요성을 증명합니다.",
    "tags": ["AI중점학교", "재정분석", "정책연구"]
  },
  {
    "filename": "교사지원단 전시체험물 운영 시나리오 기초 요약 2026-05-26.pdf",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 전시체험관 내 5개 핵심 구역(맞이공간·디지털도서관, 문화관광, 농생명, 스마트모빌리티, 스마트시티)의 운영 시나리오를 협상 기본자료 관점에서 요약한 보고서입니다.\n- ZEP 기반 안전교육, 안면인식/RFID 인증, AI 영화 제작, 로봇 시약 분주 신약 개발 미션 등 학생 활동의 단계적 구성 요소(조작-선택-결과확인-기록)와 필요 기자재 목록을 구체적으로 도식화했습니다.",
    "tags": ["미래교육캠퍼스", "전시체험", "시나리오"]
  },
  {
    "filename": "교사지원단 전시체험물 운영 시나리오 요약 (인쇄용) 2026-05-26.pdf",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 교사지원단이 작성한 미래교육캠퍼스 전시체험관 시나리오의 인쇄 및 배포용 요약 보고서입니다.\n- 「교사들의 아이디어」와 「실제 예산·운영 현실」의 격차를 해소하기 위해 5대 구역별 동시 수용 인원(총 40명 등), 활동 목표, 흐름(4단계 구조) 및 핵심 도입 장비 규격을 핵심 테이블 형태로 간결하게 정리했습니다.",
    "tags": ["미래교육캠퍼스", "협상자료", "시나리오"]
  },
  {
    "filename": "교육부 인공지능교육진흥과_2026년 제3차 디지털교육혁신 특별교부금(1-2， 1-8) 지원 계획.hwpx",
    "work_folder": "26 AI 중점학교",
    "obsidian_folder": "26 AI 중점학교",
    "summary": "- 교육부의 2026년 제3차 디지털 교육혁신 특별교부금 사업(교원 AI 역량 강화, AI 중점학교 운영 및 역량 지원)에 대한 공식 공공 추진 계획안입니다.\n- 총 859억 원 규모의 디지털 특별교부금 예산 편성 현황(1차, 2차, 3차 구분)과 시도교육청별 분담 예산 배분표, 추진 목적 및 지방교육재정교부금법 근거 등을 구체적으로 서술하고 있습니다.",
    "tags": ["특별교부금", "교육부계획", "AI중점학교"]
  },
  {
    "filename": "교육용SW_행감지적사항_개선계획_보고자료.hwpx",
    "work_folder": "행정사무감사",
    "obsidian_folder": "행정사무감사",
    "summary": "- 미래교육과 에듀테크팀에서 작성한 2025년도 교육용 범용 SW 및 플랫폼(미리캔버스, 퀴즈앤 등) 도입 관련 도의회 행정사무감사(행감) 지적 우려에 대한 종합 개선계획서입니다.\n- 입찰 자격(SaaS CSAP 보완인증 해석), 평가항목 적정성(LRS 데이터 연동 등 특정 기술 기준), 사전 정보 유출 방지 조치 및 공동수급(하도급) 논란 해소를 위한 표준 계약 구조 개선 방향을 명확하게 제시하고 있습니다.",
    "tags": ["행정사무감사", "에듀테크", "계약개선"]
  },
  {
    "filename": "교육용SW보급현황_인수위업무보고_2026.docx",
    "work_folder": "인수위자료",
    "obsidian_folder": "교육용SW사업",
    "summary": "- 2026년도 신임 교육감 인수위원회(인수위) 보고용으로 작성된 교육용 범용 소프트웨어(SW) 4종 보급 현황 및 추경 예산 확보 필요성 긴급 보고서입니다.\n- 전북 Graphics(미리캔버스), 전북 Quiz(퀴즈앤), 전북 Writing(키위티), 전북 GPT 등 4대 SW의 높은 교육 활용 성과와 만족도 조사 결과(1,259명 교원 참여)를 담고 있습니다.\n- 본예산 삭감으로 인해 2026년 9월 사용 중단 위험에 처해 있음을 알리고, 추경 예산(7.57억) 확보 당위성을 피력합니다.",
    "tags": ["인수위보고", "교육용SW", "예산확보"]
  },
  {
    "filename": "미래교육캠퍼스 교사지원단 협상안 작성 계획.hwp",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 전시체험물 설계·제작 업체의 제안 내역과 교사들의 시나리오를 바탕으로 최적의 협의 논거를 마련하기 위한 교사지원단 협상안 작성 계획입니다.\n- 기술 분야 및 콘텐츠 항목별 견적 차이를 교차 분석하고, 세부 실행 로드맵과 회의 일정을 규정하고 있습니다.",
    "tags": ["미래교육캠퍼스", "협상계획", "교사지원단"]
  },
  {
    "filename": "미래교육캠퍼스 교사지원단 협상안 제작 계획(안).hwp",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 교사지원단의 협상안 제작 계획 수립을 위한 최종 내부 검토 기획(안)입니다.\n- 업체와 미래교육과 사이의 세부 장비 단가 조율 절차와 콘텐츠 실증을 위한 교사 그룹의 세부 워크숍 편성 내용을 담고 있습니다.",
    "tags": ["미래교육캠퍼스", "협상계획", "워크숍"]
  },
  {
    "filename": "미래교육캠퍼스 전시체험관 운영 시나리오 취합양식.hwp",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 내 전시체험관 시나리오 수집을 위한 표준 취합 서식 양식입니다.\n- 구역명, 교육목표, 하드웨어 장비 구성, 소프트웨어 기능, 체험 흐름 및 AI 패스포트 연동 LRS 항목을 일관되게 기록할 수 있도록 설계되어 있습니다.",
    "tags": ["미래교육캠퍼스", "시나리오양식", "체험관"]
  },
  {
    "filename": "미래교육캠퍼스 피엔제안서 발췌.pdf",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스(JETA)의 맞이영역 및 디지털도서관 설치 관련 제안서 발췌 파일입니다.\n- 웰컴존 안내데스크, 제타 라이브러리(AI 챗봇 기반 대화형 도서 탐색 라운지 및 미니북 출력기 등), UE5 엔진 미디어월 등 캠퍼스 초입 구역의 정체성과 공간 설계 조감도 및 층별 배치 개념을 포함하고 있습니다.",
    "tags": ["미래교육캠퍼스", "JETA제안서", "공간설계"]
  },
  {
    "filename": "미래교육캠퍼스_설립_현황_및_추진_계획_보고서.hwpx",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스의 전반적인 설립 현황과 향후 중점 추진 계획을 보고하기 위해 작성된 공식 보고요지서입니다.\n- 2026년 4~5월에 실시된 4종 교육용 SW(미리캔버스 4.25점, 퀴즈앤 4.09점, 전북GPT 4.05점, 키위티 3.77점) 만족도 조사 세부 결과와 이에 따른 학교 보급 및 교육 현장 적합성 제고 계획을 상세히 보고하고 있습니다.",
    "tags": ["미래교육캠퍼스", "보고요지", "만족도조사"]
  },
  {
    "filename": "미래교육캠퍼스_설립_현황_및_추진_계획_보고서.md",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 설립의 추진 단계별 경과와 향후 세부 로드맵을 기록한 한글 마크다운 보고서입니다.\n- 1단계 설립 기획(2022~2023 전주시 MOU), 2단계 중앙투자심사 통과(2023.11), 3단계 사전기획 완료 및 착공(2024~2025) 등을 시간순으로 기록하고 있습니다.",
    "tags": ["미래교육캠퍼스", "설립추진", "중앙투자심사"]
  },
  {
    "filename": "미래교육캠퍼스_현장점검_결과보고.docx",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 공사 현장에 대한 관리 상태 및 추진 공정을 현장 점검하고 기록한 보고서입니다.\n- 2026년 3월 23일 건설사 착공을 기점으로 2027년 5월 26일 준공 목표를 위해 진행되고 있는 세부 골조 공사 일정(지하 피트 작업 완료 등)과 현장 사업 감리단 조직도(단장 강기정)를 포함하고 있습니다.\n- 전시체험물 설치 업체와의 계약 미체결로 인한 전기 배관 설치 일정 조율의 시급성을 강조하고 있습니다.",
    "tags": ["미래교육캠퍼스", "공사현장", "감리점검"]
  },
  {
    "filename": "미래교육캠퍼스_협상_추진계획서_초안_v2.docx",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 전시체험관 사업비 조율 및 계약 문안 확정을 위한 협상 추진 계획서 초안(v2)입니다.\n- 교사지원단의 5대 체험관 시나리오 조율 경과와 업체 견적 간의 격차 검증 절차(4단계 로드맵: 브레인스토밍-자료제작-전문가 컨설팅-협상안 완성)를 제시하여 최적의 행정 근거를 확보하고자 하는 목적을 서술합니다.",
    "tags": ["미래교육캠퍼스", "협상계획", "견적검증"]
  },
  {
    "filename": "붙임_미래교육캠퍼스 협상기본안 작성 회의 참석자 명단.hwp",
    "work_folder": "미래교육캠퍼스",
    "obsidian_folder": "미래교육캠퍼스",
    "summary": "- 미래교육캠퍼스 협상 기본안 작성을 위한 기안 회의용 참석자 인적사항 등록 서식 문서입니다.",
    "tags": ["미래교육캠퍼스", "회의참석자", "명단"]
  },
  {
    "filename": "신임교육감 정책반영계획_AI디지털_1.hwp",
    "work_folder": "인수위자료",
    "obsidian_folder": "보고자료",
    "summary": "- 신임 교육감 공약 및 핵심 정책 기조 반영을 위한 AI·디지털 미래교육 실행 계획안입니다.\n- 주요 과제로 교육용 SW/전북GPT 지원(예산 30.9억), 학교 무선망 디지털 튜터 지원(예산 49.5억, 250개교), AI 중점학교 운영(예산 40억, 81개교), 미래교육캠퍼스 설립(예산 478억), 인공지능 창의캠프 등 핵심 6대 사업의 예산 편성 규모와 소관 담당 부서를 명시했습니다.",
    "tags": ["인수위", "공약반영", "AI디지털"]
  },
  {
    "filename": "자체평가서 및 평가결과표(0518,최규옥2)(1).hwpx",
    "work_folder": "교육부정성평가",
    "obsidian_folder": "교육부정성평가",
    "summary": "- 2025년도 미래교육과 에듀테크활용지원 사업에 대한 자체평가서 및 결과 보고서입니다.\n- 에듀테크 기반 환경 구축(5개교 완료), 스마트교육연구회 운영(20개 완료), 종단/횡단연구 추진(1건 완료) 및 에듀테크활용 수업 지원(99개교 완료) 등 목표 대비 주요 정량/정성 성과 지표와 공교육 에듀테크 활성화 달성도를 분석하고 있습니다.\n- 소관 부서는 미래교육과 에듀테크팀이며, 담당자는 신재우, 최규옥 장학사입니다.",
    "tags": ["자체평가", "에듀테크", "성과보고"]
  },
  {
    "filename": "자체평가서 및 평가결과표(디지털기반조성).hwpx",
    "work_folder": "교육부정성평가",
    "obsidian_folder": "교육부정성평가",
    "summary": "- 미래교육과 디지털기반조성 사업에 대한 2025년도 자체평가서입니다.\n- 디지털 스마트게시대 설치 지원(12개교 완료), 전북 에듀테크소프트랩(전주교대) 구축 및 운영 지원, 에듀테크 멘토링제 운영(282팀 지원), 지역단위 정보교육지원단 운영(15개 완료) 등 정량적 성과 목표 달성율과 예산 집행 타당성을 소상히 기록하고 있습니다.\n- 담당 장학사는 최규옥, 김석중 장학사입니다.",
    "tags": ["자체평가", "디지털기반조성", "성과지표"]
  },
  {
    "filename": "통합 문서1 (version 2).xlsx",
    "work_folder": "예산",
    "obsidian_folder": "예산",
    "summary": "- 디지털 기반 교육혁신 지원 사업(디지털 선도학교, 디지털 연구학교, 매칭데이, 교원 워크숍, 교육혁신지원단 운영 등)의 예산 배정 현황 및 지출 내역 정산 엑셀 시트입니다.\n- 세부 지출 목별(210 여비, 220 업무추진비, 230 수당 등) 예산 현액, 원인행위잔액, 교부잔액 및 지출액 현황이 숫자로 기록되어 있습니다.",
    "tags": ["예산정산", "디지털선도학교", "지출내역"]
  }
]

# ==========================================
# 2. 실행 프로세스
# ==========================================

def load_extracted_content():
    """JSON 파일로부터 추출된 본문 로드"""
    if not os.path.exists(JSON_PATH):
        print("경고: 본문 추출 JSON 파일이 존재하지 않아 본문 발췌 없이 노트를 작성합니다.")
        return {}
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {item['filename']: item['content'] for item in data}
    except Exception as e:
        print(f"JSON 로드 오류: {e}")
        return {}

def find_desktop_file(filename):
    """NFC 정규화를 고려하여 바탕화면 파일 실경로 검색"""
    norm_filename = unicodedata.normalize('NFC', filename)
    for name in os.listdir(DESKTOP_DIR):
        if unicodedata.normalize('NFC', name) == norm_filename:
            return os.path.join(DESKTOP_DIR, name)
    return None

def move_file_with_collision_handling(src_path, dest_dir):
    """파일 이동 및 이름 충돌 제어 (잠금 상태일 경우 복사로 대체)"""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)
    
    # 1. 대상 경로 결정 (충돌 방지 포함)
    target_path = dest_path
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_filename = f"{name}_{counter}{ext}"
            new_dest_path = os.path.join(dest_dir, new_filename)
            if not os.path.exists(new_dest_path):
                target_path = new_dest_path
                break
            counter += 1
            
    # 2. 이동 시도
    try:
        shutil.move(src_path, target_path)
        return target_path
    except PermissionError:
        # 파일 잠금 상태 -> 복사 후 원본 유지
        try:
            shutil.copy2(src_path, target_path)
            print(f"  [경고] '{filename}' 파일이 사용 중이어서 이동 대신 복사했습니다. (문서를 닫은 후 바탕화면에서 수동 삭제해 주세요)")
            return target_path
        except Exception as copy_error:
            raise RuntimeError(f"파일을 복사할 수 없습니다: {copy_error}")

def create_obsidian_note(filename, dest_path, obsidian_folder, summary, content, tags):
    """옵시디언 마크다운 노트 파일 작성"""
    # 00 Inbox 인지 10 Projects 인지 판단
    if obsidian_folder == "00 Inbox":
        target_dir = os.path.join(OBSIDIAN_DIR, "00 Inbox")
    else:
        target_dir = os.path.join(OBSIDIAN_DIR, "10 Projects", obsidian_folder)
        
    os.makedirs(target_dir, exist_ok=True)
    
    name, _ = os.path.splitext(filename)
    note_filename = f"{name}.md"
    note_path = os.path.join(target_dir, note_filename)
    
    # 크기 및 최종수정일 산출
    size = 0
    mtime = dt.datetime.now().isoformat(timespec="seconds")
    if os.path.exists(dest_path):
        stat = os.stat(dest_path)
        size = stat.st_size
        mtime = dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        
    tags_formatted = ", ".join(f"'{t}'" for t in tags)
    preview_content = content[:1500].strip() if content else "(본문 없음)"
    
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
        f"- **파일 크기**: `{size:,} bytes`",
        f"- **최종 수정일**: `{mtime}`",
        "",
        "## 📝 주요 본문 발췌 (앞부분)",
        "",
        "```text",
        preview_content,
        "```"
    ]
    
    # 파일명 충돌 해결
    if os.path.exists(note_path):
        stem, ext = os.path.splitext(note_filename)
        c = 1
        while True:
            new_note_path = os.path.join(target_dir, f"{stem}_{c}{ext}")
            if not os.path.exists(new_note_path):
                note_path = new_note_path
                break
            c += 1
            
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    return note_path

def rebuild_wiki():
    """업무-wiki 빌드 스크립트 실행"""
    bat_path = os.path.join(WIKI_DIR, "update_work_wiki.bat")
    if os.path.exists(bat_path):
        print("=" * 60)
        print("업무 위키(LLM 위키) 인덱스 업데이트 빌드를 수행합니다...")
        try:
            result = subprocess.run([bat_path], cwd=WIKI_DIR, capture_output=True, text=True, shell=True)
            print("위키 업데이트 빌드 완료.")
            print(result.stdout[:500] + "\n..." if len(result.stdout) > 500 else result.stdout)
            if result.stderr:
                print("위키 빌드 경고/오류:")
                print(result.stderr)
        except Exception as e:
            print(f"위키 스크립트 실행 실패: {e}")
    else:
        print(f"경고: 위키 업데이트 배치 파일({bat_path})을 찾을 수 없습니다.")

def main():
    print("=" * 60)
    print("바탕화면 고정밀 정리/요약 동기화 작업 시작 (Gemini Direct Mode)")
    print("=" * 60)
    
    content_map = load_extracted_content()
    moved_count = 0
    obsidian_count = 0
    
    for idx, mapping in enumerate(MAPPINGS, start=1):
        filename = mapping["filename"]
        work_sub = mapping["work_folder"]
        obs_sub = mapping["obsidian_folder"]
        summary = mapping["summary"]
        tags = mapping["tags"]
        
        # 파일 확인
        src_path = find_desktop_file(filename)
        if not src_path:
            print(f"[{idx}/{len(MAPPINGS)}] 경고: 파일을 바탕화면에서 찾을 수 없습니다: {filename}")
            continue
            
        print(f"[{idx}/{len(MAPPINGS)}] 처리 중: {filename}")
        
        # 1. 파일 이동
        dest_dir = os.path.join(WORK_DIR, work_sub)
        print(f"  -> 업무/{work_sub}/ 폴더로 이동 중...")
        actual_dest_path = move_file_with_collision_handling(src_path, dest_dir)
        print(f"  -> 이동 완료: {os.path.basename(actual_dest_path)}")
        moved_count += 1
        
        # 2. 옵시디언 노트 작성
        print(f"  -> 옵시디언 {obs_sub} 폴더에 요약 노트 생성 중...")
        content = content_map.get(filename, "")
        note_path = create_obsidian_note(filename, actual_dest_path, obs_sub, summary, content, tags)
        print(f"  -> 요약 노트 생성 완료: {os.path.basename(note_path)}")
        obsidian_count += 1
        
    print("=" * 60)
    print(f"정리 결과: 파일 이동 {moved_count}건, 옵시디언 요약 {obsidian_count}건 완료")
    print("=" * 60)
    
    # 3. LLM 위키 빌드 갱신
    rebuild_wiki()
    return 0

if __name__ == "__main__":
    sys.exit(main())
