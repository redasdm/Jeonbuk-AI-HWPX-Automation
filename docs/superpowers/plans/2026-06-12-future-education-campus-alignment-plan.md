# 「미래교육캠퍼스」 연계 전북 특화 진로·일자리 체험을 통한 지역 정주형 미래인재 육성 방안 보고요지 생성 계획서 (최종 수정본)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 미래교육캠퍼스 추진현황 및 인수위 공약 매칭 내용을 바탕으로, 교육감 보고용 한글 보고요지 파일(`미래교육캠퍼스_연계_맞춤형_진로_성장_체계_구축_방안_보고요지.hwpx`)을 자동 생성하는 파이썬 스크립트 `create_campus_briefing_plan.py`를 개발한다.

**Architecture:** 기존 한글 문서 템플릿의 서식 XML(`ref2_section.xml`)을 `lxml` 라이브러리로 파싱하여, 공약 매칭 테이블 및 최종 개관 로드맵 테이블을 포함한 새로운 서식 본문 XML(`campus_briefing_section0.xml`)을 동적으로 빌드한다. 이후 내장된 `build_hwpx.py` 패키징 도구를 실행하여 한글 파일을 생성한다.

**Tech Stack:** Python 3, lxml, subprocess, HWPX-MCP 라이브러리

---

### Task 1: 미래교육캠퍼스 보고요지 생성 스크립트 작성 및 빌드

**Files:**
- Create: `create_campus_briefing_plan.py`
- Test: `tests/test_campus_briefing.py`

- [ ] **Step 1: HWPX 생성을 위한 기본 단위 테스트 작성 (TDD)**
  
  정상적으로 스크립트가 실행되어 출력 경로에 HWPX 파일이 손상 없이 생성되는지 검증하는 테스트 코드를 작성합니다.

  ```python
  # tests/test_campus_briefing.py
  import os
  from pathlib import Path
  import subprocess

  def test_campus_briefing_generation():
      output_dir = Path("C:/Users/redas/OneDrive/Desktop/업무/보고자료")
      output_file = output_dir / "미래교육캠퍼스_연계_맞춤형_진로_성장_체계_구축_방안_보고요지.hwpx"
      
      # 이전 파일이 존재한다면 삭제
      if output_file.exists():
          output_file.unlink()
          
      # 생성 스크립트 실행
      result = subprocess.run(
          ["python", "create_campus_briefing_plan.py"],
          capture_output=True,
          text=True,
          check=True
      )
      
      # HWPX 파일 생성 여부 검증
      assert output_file.exists(), "HWPX 파일이 정상적으로 생성되지 않았습니다."
      assert output_file.stat().st_size > 10000, f"HWPX 파일 용량이 비정상적입니다: {output_file.stat().st_size} bytes"
  ```

- [ ] **Step 2: 단위 테스트 실행 및 실패 확인**

  Run: `pytest tests/test_campus_briefing.py -v` (또는 `python tests/test_campus_briefing.py`)
  Expected: FAIL

- [ ] **Step 3: 미래교육캠퍼스 보고요지 빌더 스크립트 구현**

  전북의 4대 지역 특화 산업(농생명, 친환경 로보틱스, 미래 모빌리티, 피지컬 AI) 및 관련 실제 지역 일자리를 매칭하고, 최종 개관 로드맵(2028년 4월)과 공종 분리를 반영한 한글 빌더 코드를 구현합니다.

  ```python
  # create_campus_briefing_plan.py
  import os
  import subprocess
  from pathlib import Path
  from lxml import etree
  import copy

  def build_campus_briefing_xml():
      base_xml = Path('ref2_section.xml')
      if not base_xml.exists():
          raise FileNotFoundError("ref2_section.xml 템플릿 파일이 없습니다.")
          
      tree = etree.parse(str(base_xml))
      root = tree.getroot()
      nsmap = root.nsmap

      new_root = etree.Element(f"{{{nsmap['hs']}}}sec", nsmap=nsmap)
      
      original_p_list = root.xpath('.//hp:p', namespaces=nsmap)
      first_p = original_p_list[0]
      new_first_p = copy.deepcopy(first_p)
      for t in new_first_p.xpath('.//hp:t', namespaces=nsmap):
          t.text = ''
      new_root.append(new_first_p)
      
      pid = 1500000001
      
      # 스타일 ID 정의
      TITLE_P, TITLE_C = 17, 58      # 제목 스타일
      SEC_P, SEC_C = 77, 71           # 대주제 스타일 (Ⅰ, Ⅱ, Ⅲ 등)
      BOX_P, BOX_C = 77, 19           # 중주제/내용 박스 스타일 (◦)
      BULLET_P, BULLET_C = 79, 19     # 소주제 스타일 (-)
      BLANK_P = 8                     # 빈 줄 스타일
      
      def add_p(para_pr, char_pr, text):
          nonlocal pid
          p = etree.SubElement(new_root, f"{{{nsmap['hp']}}}p", id=str(pid), paraPrIDRef=str(para_pr), styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
          pid += 1
          run = etree.SubElement(p, f"{{{nsmap['hp']}}}run", charPrIDRef=str(char_pr))
          if text:
              t = etree.SubElement(run, f"{{{nsmap['hp']}}}t")
              t.text = text
          else:
              etree.SubElement(run, f"{{{nsmap['hp']}}}t")
          return p

      def add_blank():
          add_p(BLANK_P, 0, "")

      def add_table(header_cols, rows_data, col_widths):
          nonlocal pid
          p = etree.SubElement(new_root, f"{{{nsmap['hp']}}}p", id=str(pid), paraPrIDRef="1", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
          pid += 1
          run = etree.SubElement(p, f"{{{nsmap['hp']}}}run", charPrIDRef="0")
          
          tbl = etree.SubElement(run, f"{{{nsmap['hp']}}}tbl", id=str(pid), zOrder="0", numberingType="TABLE", textWrap="TOP_AND_BOTTOM", textFlow="BOTH_SIDES", lock="0", dropcapstyle="None", pageBreak="CELL", repeatHeader="1", rowCnt=str(len(rows_data)+1), colCnt=str(len(header_cols)), cellSpacing="0", borderFillIDRef="4", noAdjust="0")
          pid += 1
          
          total_w = sum(col_widths)
          etree.SubElement(tbl, f"{{{nsmap['hp']}}}sz", width=str(total_w), widthRelTo="ABSOLUTE", height="10000", heightRelTo="ABSOLUTE", protect="0")
          etree.SubElement(tbl, f"{{{nsmap['hp']}}}pos", treatAsChar="1", affectLSpacing="0", flowWithText="1", allowOverlap="0", holdAnchorAndSO="0", vertRelTo="PARA", horzRelTo="COLUMN", vertAlign="TOP", horzAlign="LEFT", vertOffset="0", horzOffset="0")
          etree.SubElement(tbl, f"{{{nsmap['hp']}}}outMargin", left="0", right="0", top="0", bottom="0")
          etree.SubElement(tbl, f"{{{nsmap['hp']}}}inMargin", left="0", right="0", top="0", bottom="0")

          # 테이블 헤더 생성
          tr = etree.SubElement(tbl, f"{{{nsmap['hp']}}}tr")
          for i, text in enumerate(header_cols):
              tc = etree.SubElement(tr, f"{{{nsmap['hp']}}}tc", name="", header="1", hasMargin="0", protect="0", editable="0", dirty="0", borderFillIDRef="4")
              subList = etree.SubElement(tc, f"{{{nsmap['hp']}}}subList", id="", textDirection="HORIZONTAL", lineWrap="BREAK", vertAlign="CENTER", linkListIDRef="0", linkListNextIDRef="0", textWidth="0", textHeight="0", hasTextRef="0", hasNumRef="0")
              p_cell = etree.SubElement(subList, f"{{{nsmap['hp']}}}p", id=str(pid), paraPrIDRef="74", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
              pid += 1
              r_cell = etree.SubElement(p_cell, f"{{{nsmap['hp']}}}run", charPrIDRef="70")
              t_cell = etree.SubElement(r_cell, f"{{{nsmap['hp']}}}t")
              t_cell.text = text
              etree.SubElement(tc, f"{{{nsmap['hp']}}}cellAddr", colAddr=str(i), rowAddr="0")
              etree.SubElement(tc, f"{{{nsmap['hp']}}}cellSpan", colSpan="1", rowSpan="1")
              etree.SubElement(tc, f"{{{nsmap['hp']}}}cellSz", width=str(col_widths[i]), height="3000")
              etree.SubElement(tc, f"{{{nsmap['hp']}}}cellMargin", left="141", right="141", top="141", bottom="141")

          # 데이터 행 생성
          for r_idx, row in enumerate(rows_data, 1):
              tr = etree.SubElement(tbl, f"{{{nsmap['hp']}}}tr")
              for i, text in enumerate(row):
                  tc = etree.SubElement(tr, f"{{{nsmap['hp']}}}tc", name="", header="0", hasMargin="0", protect="0", editable="0", dirty="0", borderFillIDRef="4")
                  subList = etree.SubElement(tc, f"{{{nsmap['hp']}}}subList", id="", textDirection="HORIZONTAL", lineWrap="BREAK", vertAlign="CENTER", linkListIDRef="0", linkListNextIDRef="0", textWidth="0", textHeight="0", hasTextRef="0", hasNumRef="0")
                  lines = text.split('\n')
                  for line in lines:
                      p_cell = etree.SubElement(subList, f"{{{nsmap['hp']}}}p", id=str(pid), paraPrIDRef="76", styleIDRef="0", pageBreak="0", columnBreak="0", merged="0")
                      pid += 1
                      r_cell = etree.SubElement(p_cell, f"{{{nsmap['hp']}}}run", charPrIDRef="10")
                      if line.strip():
                          t_cell = etree.SubElement(r_cell, f"{{{nsmap['hp']}}}t")
                          t_cell.text = line.strip()
                      else:
                          etree.SubElement(r_cell, f"{{{nsmap['hp']}}}t")
                  etree.SubElement(tc, f"{{{nsmap['hp']}}}cellAddr", colAddr=str(i), rowAddr=str(r_idx))
                  etree.SubElement(tc, f"{{{nsmap['hp']}}}cellSpan", colSpan="1", rowSpan="1")
                  etree.SubElement(tc, f"{{{nsmap['hp']}}}cellSz", width=str(col_widths[i]), height="3000")
                  etree.SubElement(tc, f"{{{nsmap['hp']}}}cellMargin", left="141", right="141", top="141", bottom="141")

      # ==========================================
      # 본문 작성 시작
      # ==========================================
      add_p(TITLE_P, TITLE_C, "「미래교육캠퍼스」 연계 전북 특화 진로·일자리 체험을 통한 지역 정주형 미래인재 육성 방안(안)")
      add_blank()

      # Ⅰ. 추진 배경 및 설립 목적
      add_p(SEC_P, SEC_C, "Ⅰ. 추진 배경 및 설립 목적")
      add_p(BOX_P, BOX_C, "◦ 단 한 명도 소외되지 않는 전북 맞춤형 진로 복지 실현")
      add_p(BULLET_P, BULLET_C, "- 지역 간 교육 격차를 해소하고 도내 모든 학생에게 최상의 미래 진로 탐색 기회 제공")
      add_p(BOX_P, BOX_C, "◦ 전북 특화 산업 및 지역 일자리 연계형 진로 교육")
      add_p(BULLET_P, BULLET_C, "- 전북의 4대 지역전략산업과 실제 일자리를 연계하여 실무 탐구형 진로 설계 지원")
      add_p(BOX_P, BOX_C, "◦ 지역 소멸 위기에 대응하는 정주형 미래인재 양성")
      add_p(BULLET_P, BULLET_C, "- 지역 미래 성장 동력을 조기 학습하여 도내 대학 및 향토 기업으로 정주·성장하는 선순환 구조 확립")
      add_blank()

      # Ⅱ. 미래교육캠퍼스 설립 현황 및 추진 내용
      add_p(SEC_P, SEC_C, "Ⅱ. 미래교육캠퍼스 설립 현황 및 추진 내용")
      add_p(BOX_P, BOX_C, "◦ 공정 현황: 지하 골조 공사가 차질 없이 진행 중이며, 1층 바닥 콘크리트 타설 준비 중")
      add_p(BOX_P, BOX_C, "◦ 협상 현황: 우선협상대상자와 '전북 일자리 연계 및 체험 시나리오 구체화' 중심 실무 협상 가동 중")
      add_blank()

      # Ⅲ. 인수위 10대 정책과의 공간별 매칭 체계
      add_p(SEC_P, SEC_C, "Ⅲ. 인수위 10대 정책과의 공간별 매칭 체계")
      add_table(
          ["캠퍼스 공간", "교육감 정책 연계", "구체적인 연계 방안 (체험 예시)"],
          [
              ["맞이공간 및\n디지털도서관", "기본에 충실한 교육\n(독서 300 프로젝트,\n문해력 신장 교육)", "인공지능 기반 독서 문해력 진단 코너 및\n개인별 맞춤 도서 추천 서비스 운영"],
              ["미래기술체험관", "인공지능 미래 교육\n(전북형 AI 인재 육성,\n지역 전략산업 교육)", "전북 4대 핵심 산업(농생명, 친환경 로보틱스, 미래\n모빌리티, 피지컬 AI) 기반 도내 일자리 미션 수행"],
              ["미래교육관", "성공하는 진학·진로 교육\n(전북학생 미래인재 성장 단계,\n진로 맞춤 교육)", "체험 활동 데이터를 누적하여 '전북형 진로·일자리\n성장 리포트' 발급 및 진학 상담·생활기록부 연동"],
              ["미래교육 아레나", "학교공동체 회복 및\n민주시민 양성\n(만민공동회, 평화 갈등 해결)", "(e스포츠 배제) 전북 지역 일자리 창출 및 지역 소멸\n극복을 주제로 한 청소년 자치 의회, 토론회 운영"]
          ],
          col_widths=[10000, 12000, 20520]
      )
      add_blank()

      # Ⅳ. 핵심 추진 과제
      add_p(SEC_P, SEC_C, "Ⅳ. 핵심 추진 과제")
      add_p(BOX_P, BOX_C, "◦ 1. 전북 4대 특화 산업과 지역 일자리 연계형 미래 진로 체험 고도화")
      add_p(BULLET_P, BULLET_C, "- 농생명 구역: 농생명 혁신도시 기반 스마트팜 연구원 및 바이오 식품 공학자 업무 시뮬레이션")
      add_p(BULLET_P, BULLET_C, "- 친환경 로보틱스 구역: 새만금 신재생에너지 단지 연계 리사이클링 엔지니어 및 이차전지 공학자 체험")
      add_p(BULLET_P, BULLET_C, "- 미래 모빌리티 구역: 군산 전기차 클러스터 기반 자율주행 제어 엔지니어 및 미래 교통 디자이너 실습")
      add_p(BULLET_P, BULLET_C, "- 피지컬 AI 구역: 전북 피지컬 AI 실증단지 기반 인간-로봇 상호작용 개발자 역량 분석")
      add_p(BOX_P, BOX_C, "◦ 2. 지역 정주를 유도하는 맞춤형 진로 진학 연동 체계 구축")
      add_p(BULLET_P, BULLET_C, "- 도교육청-지자체-지역 대학-향토 기업 간 협력 체계를 통해 축적된 진로 데이터를 도내 고교·대학 진학 경로와 연계")
      add_p(BULLET_P, BULLET_C, "- 학생 진로 성장 포트폴리오를 도내 기업 인턴십 및 취업 매칭 기초 자료로 제공하여 전북 정주율 제고")
      add_blank()

      # Ⅴ. 기대 효과 및 향후 계획
      add_p(SEC_P, SEC_C, "Ⅴ. 기대 효과 및 향후 계획")
      add_p(BOX_P, BOX_C, "◦ 가. 기대 효과")
      add_p(BULLET_P, BULLET_C, "- 도내 전략산업 맞춤형 인재 육성을 통한 지역 정주율 제고 및 지역 소멸 방지")
      add_p(BULLET_P, BULLET_C, "- 소외 지역 배려 수송 대책 연계로 교육 공공성 및 무상 진로 복지 실현")
      add_p(BULLET_P, BULLET_C, "- 협동형 문제 해결을 통한 공동체 역량과 배려·소통을 실천하는 인성 함양")
      add_p(BOX_P, BOX_C, "◦ 나. 향후 추진 계획 (로드맵)")
      add_table(
          ["구분", "일정", "주요 협상 및 공정 내용"],
          [
              ["협상 및 계약", "2026. 06. ~ 07.", "• 우선협상대상자와 운영 시나리오 보완 협상 마무리 및 본계약 체결"],
              ["건축 공사", "2026. 11.\n2027. 05.", "• 건축 골조 공사 완료\n• 건축물 사용승인 및 준공"],
              ["전시체험물 공사", "2026. 07. ~ 12.\n2027. 01. ~ 12.", "• 전시 및 인테리어 세부 설계 및 공장 제작\n• 현장 인테리어 공사 및 전시체험물 설치 완료\n(12월 최종 공사 마무리)"],
              ["시운전 및 개관", "2028. 01. ~ 03.\n2028. 04.", "• 시스템 시운전 및 교사·학생 시범 운영 (3개월간)\n• 미래교육캠퍼스 정식 개관"]
          ],
          col_widths=[8000, 10000, 24520]
      )

      # 임시 XML 저장
      output_xml = "campus_briefing_section0.xml"
      with open(output_xml, 'w', encoding='utf-8') as f:
          f.write(etree.tostring(new_root, pretty_print=False, xml_declaration=True, encoding='UTF-8').decode('utf-8'))
      print(f"임시 XML '{output_xml}' 생성 완료.")

  if __name__ == '__main__':
      build_campus_briefing_xml()
      
      output_dir = r"C:\Users\redas\OneDrive\Desktop\업무\보고자료"
      os.makedirs(output_dir, exist_ok=True)
      out_file = os.path.join(output_dir, "미래교육캠퍼스_연계_맞춤형_진로_성장_체계_구축_방안_보고요지.hwpx")
      
      # HWPX 빌드 스크립트 호출
      subprocess.run([
          'python', 'hwpx/scripts/build_hwpx.py', 
          '--header', 'ref2_header.xml',
          '--section', 'campus_briefing_section0.xml',
          '--output', out_file
      ], check=True)
      print(f"최종 HWPX 파일 '{out_file}' 생성 성공.")
  ```

- [ ] **Step 4: 단위 테스트 실행 및 통과 검증**

  Run: `python tests/test_campus_briefing.py`
  Expected: PASS

- [ ] **Step 5: 소스 코드 커밋**

  ```bash
  git add create_campus_briefing_plan.py tests/test_campus_briefing.py
  git commit -m "feat: update briefing plan generator with Jeonbuk-tailored jobs and career alignment"
  ```
