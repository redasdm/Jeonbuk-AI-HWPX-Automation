export const NS = {
  hp: "http://www.hancom.co.kr/hwpml/2011/paragraph",
  hs: "http://www.hancom.co.kr/hwpml/2011/section",
  hc: "http://www.hancom.co.kr/hwpml/2011/core",
  hh: "http://www.hancom.co.kr/hwpml/2011/head",
  opf: "http://www.idpf.org/2007/opf/"
};

export const MIMETYPE = "application/hwp+zip";

export const A4_WIDTH = 59528;
export const A4_HEIGHT = 84186;
export const CONTENT_WIDTH = 42520; // A4_WIDTH - left margin - right margin

export const AVAILABLE_TEMPLATES = [
  { id: "base", name: "기본", desc: "최소 스타일, 빈 문서 시작점" },
  { id: "gonmun", name: "공문", desc: "기관명, 수신처, 시행일자, 연락처 탑재" },
  { id: "report", name: "보고서", desc: "섹션 헤더, 체크박스 스타일" },
  { id: "minutes", name: "회의록", desc: "회의록 포맷, 섹션 라벨" },
  { id: "proposal", name: "제안서", desc: "색상 헤더, 번호 뱃지" }
];
