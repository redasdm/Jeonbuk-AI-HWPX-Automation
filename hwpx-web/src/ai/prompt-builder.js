// System Prompt
export const SYSTEM_PROMPT = `당신은 한글(HWPX) 문서 작성/기획 전문가입니다.
사용자의 요청에 따라 문서의 전체 구조와 내용을 기획하여 응답해야 합니다.

요청 내용에 맞게 아래 JSON 형식으로만 응답하세요. 다른 부연 설명이나 마크다운 백틱(\`\`\`) 없이 순수 JSON만 출력하세요.

{
  "title": "문서 제목",
  "template": "관련 템플릿(base, gonmun, report, minutes, proposal 중 택1)",
  "blocks": [
    {
      "type": "paragraph",
      "style": "기본 본문",
      "text": "..."
    },
    {
      "type": "table",
      "headers": ["컬럼1", "컬럼2"],
      "rows": [
        ["값1", "값2"]
      ]
    },
    {
      "type": "blank"
    }
  ]
}

- 공문, 기안은 'gonmun', 보고서는 'report', 회의록은 'minutes', 제안서나 사업계획서는 'proposal' 템플릿을 선택하세요.
- paragraph block에서 여러 줄이 필요하면 text 값 안에 \\n 을 사용하세요.
- 각 section은 paragraph 블록으로 나누어 표현하고 빈 줄이 필요하면 blank 블록을 사용하세요.
`;

// Helper to map abstract styles to template-specific paraPr/charPr
export function parseResponseBlocks(blocks, template) {
  return blocks.map(block => {
    if (block.type === 'paragraph') {
      let paraPrId = "0";
      let charPrId = "0";

      // Very simple mapping heuristic based on text content or 'style' field
      if (template === 'gonmun') {
        if (block.text && block.text.match(/^제목\s*:|^\[.*\]/)) {
          charPrId = "7"; // 22pt bold
          paraPrId = "20"; // Center
        }
      } else if (template === 'report') {
        if (block.style && block.style.includes('제목')) {
          charPrId = "7";
        } else if (block.text && block.text.match(/^\d\./)) {
          charPrId = "8";
        }
      } else if (template === 'minutes') {
        if (block.style && block.style.includes('제목') || block.text && block.text.endsWith('회의록')) {
          charPrId = "7";
          paraPrId = "20";
        }
      }

      return {
        type: "paragraph",
        styleId: paraPrId,
        charStyleId: charPrId,
        text: block.text
      };
    } else if (block.type === 'table') {
      return block;
    } else {
      return { type: "blank" }
    }
  });
}
