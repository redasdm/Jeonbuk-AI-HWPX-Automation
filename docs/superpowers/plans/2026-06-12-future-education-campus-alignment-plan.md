# 「미래교육캠퍼스」 연계 맞춤형 진로 성장 체체 구축 방안 보고요지 생성 계획서

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
      assert output_file.stat().st_size > 100000, "HWPX 파일 용량이 비정상적입니다."
  ```

- [ ] **Step 2: 단위 테스트 실행 및 실패 확인**

  Run: `pytest tests/test_campus_briefing.py -v`
  Expected: FAIL (스크립트 파일이 없으므로 ModuleNotFoundError 혹은 FileNotFoundError 발생)

- [ ] **Step 3: 미래교육캠퍼스 보고요지 빌더 스크립트 구현**

  외래어를 배제하고, 천호성 교육감 구호(학력·인성·청렴) 및 정식 개관 일정(2028년 4월), 건축과 전시 공정 분리안을 모두 담아 HWPX 본문 구조를 동적으로 생성하는 스크립트를 구현합니다.

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
      SEC_P, SEC_C = 77, 71           # 대주제 스타일 (❍, )
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
      add_p(TITLE_P, TITLE_C, "「미래교육캠퍼스」 연계 맞춤형 진로 성장 체체 구축 방안(안)")
      add_blank()

      # Ⅰ. 추진 배경 및 설립 목적
      add_p(SEC_P, SEC_C, " Ⅰ. 추진 배경 및 설립 목적")
      add_p(BOX_P, BOX_C, "◦ 단 한 명도 배움에서 소외되지 않는 맞춤형 미래 학력 신장")
      add_p(BULLET_P, BULLET_C, "- 학생 개개인의 미래 역량을 수집하여 적성과 소질에 부합하는 개별 성장 기회 보장")
      add_p(BOX_P, BOX_C, "◦ 지역과 세계를 잇는 미래형 진로 개척")
      add_p(BULLET_P, BULLET_C, "- 인공지능 기초 원리를 탐구하고, 전북 지역 전략산업과 연계하여 지역 정주형 인재 양성")
      add_p(BOX_P, BOX_C, "◦ 배려와 소통을 실천하는 민주시민 역량 함양")
      add_p(BULLET_P, BULLET_C, "- 협력적 문제 해결력 및 자치 토론 활성화로 더불어 성장하는 공동체 가치 구현")
      add_blank()

      # Ⅱ. 미래교육캠퍼스 설립 현황 및 추진 내용
      add_p(SEC_P, SEC_C, " Ⅱ. 미래교육캠퍼스 설립 현황 및 추진 내용")
      add_p(BOX_P, BOX_C, "◦ 공정 현황: 지하 골조 공사가 차질 없이 진행 중이며, 1층 바닥 콘크리트 타설 준비 중")
      add_p(BOX_P, BOX_C, "◦ 협상 현황: 우선협상대상자와 단순 관람을 배제한 교육과정 연계 체험 시나리오 중심 협상 가동 중")
      add_blank()

      # Ⅲ. 인수위 10대 정책과의 공간별 매칭 체계
      add_p(SEC_P, SEC_C, " Ⅲ. 인수위 10대 정책과의 공간별 매칭 체계")
      add_table(
          ["캠퍼스 공간", "교육감 정책 연계", "구체적인 연계 방안 (체험 예시)"],
          [
              ["맞이공간 및\n디지털도서관", "기본에 충실한 교육\n(독서 300 프로젝트,\n문해력 신장 교육)", "인공지능 기반 독서 문해력 진단 코너 및\n개인별 맞춤 도서 추천 서비스 운영"],
              ["미래기술체험관", "인공지능 미래 교육\n(전북형 AI 인재 육성,\n지역 미래산업 교육)", "피지컬 AI 기술과 전북 지역 전략산업(지능형\n자동차, 자율 바이오 등) 융합 시뮬레이터 운영"],
              ["미래교육관", "성공하는 진학·진로 교육\n(전북학생 미래인재 성장 단계,\n진로 맞춤 교육)", "체험 활동 데이터를 누적하여 '진로 성장 리포트'\n발급 및 학교 진로 지도·생활기록부 연동"],
              ["미래교육 아레나", "학교공동체 회복 및\n민주시민 양성\n(만민공동회, 평화 갈등 해결)", "(e스포츠 배제) 실제 사회 현안 토론 및 대안을\n제시하는 자치 의회, 갈등 조정 역할극 운영"]
          ],
          col_widths=[10000, 12000, 20520]
      )
      add_blank()

      # Ⅳ. 핵심 추진 과제
      add_p(SEC_P, SEC_C, " Ⅳ. 핵심 추진 과제")
      add_p(BOX_P, BOX_C, "◦ 1. 인공지능 기반 개인 맞춤형 진로 성장 설계")
      add_p(BULLET_P, BULLET_C, "- 캠퍼스 체험 활동 결과를 학생 개인 카드로 자동 기록하여 '진로 성장 포트폴리오'로 체계화")
      add_p(BULLET_P, BULLET_C, "- 예비 고교생 대상 스타트업 캠프, 고1~2학년 대상 스텝업 프로젝트 등 단계별 교육과정 연동")
      add_p(BOX_P, BOX_C, "◦ 2. 전북 전략산업 및 민주시민 역량 연계형 진로 생태계 구축")
      add_p(BULLET_P, BULLET_C, "- 피지컬 AI, 농생명, 친환경 모빌리티 등 전북 미래 전략기술 체험 확대 및 교육과정 이수단위화 기반 마련")
      add_p(BULLET_P, BULLET_C, "- 공동체 역량 함양을 위해 '학생·청소년 만민공동회 체험 프로그램'을 정규 교육과정의 민주시민 파트와 연계")
      add_blank()

      # Ⅴ. 기대 효과 및 향후 계획
      add_p(SEC_P, SEC_C, " Ⅴ. 기대 효과 및 향후 계획")
      add_p(BOX_P, BOX_C, "◦ 가. 기대 효과")
      add_p(BULLET_P, BULLET_C, "- 소외 지역 학생 중심 지원을 통한 보편적 진로·학습 복지 실현")
      add_p(BULLET_P, BULLET_C, "- 지역 미래 신산업 관련 진로 관심 촉발로 지역 정주형 선순환 생태계 활성화")
      add_p(BULLET_P, BULLET_C, "- 배려와 소통을 실천하는 균형 잡힌 인권 감수성 및 민주시민 자질 함양")
      add_p(BOX_P, BOX_C, "◦ 나. 향후 추진 계획 (로드맵)")
      add_table(
          ["구분", "일정", "주요 협상 및 공정 내용"],
          [
              ["협상 및 계약", "2026. 06. ~ 07.", "• 우선협상대상자와 운영 시나리오 보완 협상 마무리 및 본계약 체결"],
              ["건축 공사", "2026. 11.\n2027. 05.", "• 건축 골조 공사 완료\n• 건축물 사용승인 및 준공"],
              ["전시체험물 공사", "2026. 07. ~ 12.\n2027. 01. ~ 12.", "• 전시 및 인테리어 세부 설계 및 공장 제작\n• 현장 인테리어 공사 및 전시체험물 설치 완료"],
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

  Run: `pytest tests/test_campus_briefing.py -v`
  Expected: PASS (테스트 통과 및 출력 경로에 정상적으로 한글 보고요지 파일 생성 완료)

- [ ] **Step 5: 소스 코드 커밋**

  ```bash
  git add create_campus_briefing_plan.py tests/test_campus_briefing.py
  git commit -m "feat: add future education campus briefing plan generator script"
  ```
