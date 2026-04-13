import { buildSectionXml } from './core/xml-builder.js';
import { buildHwpx, downloadHwpx } from './core/hwpx-packager.js';
import { validateHwpx } from './core/hwpx-validator.js';
import { Templates } from './templates/bundled.js';
import { initSettingsModal } from './settings/settings-modal.js';
import { generateDocument } from './ai/ai-manager.js';

let blocks = [
  { type: "paragraph", styleId: "0", charStyleId: "0", text: "여기에 내용을 입력하세요." }
];

function renderBlocks() {
  const container = document.getElementById('block-list');
  container.innerHTML = '';

  blocks.forEach((block, index) => {
    const item = document.createElement('div');
    item.className = 'block-item';
    
    const typeLabel = document.createElement('div');
    typeLabel.style.width = '60px';
    typeLabel.style.fontSize = '0.8rem';
    typeLabel.style.color = 'var(--text-secondary)';
    typeLabel.textContent = block.type === 'paragraph' ? '문단' : (block.type === 'table' ? '표' : '빈줄');

    const contentDiv = document.createElement('div');
    contentDiv.className = 'block-content';
    contentDiv.style.flex = '1';

    if (block.type === 'paragraph') {
      const ta = document.createElement('textarea');
      ta.value = block.text;
      ta.rows = block.text.split('\n').length || 1;
      ta.addEventListener('input', (e) => {
        blocks[index].text = e.target.value;
        renderPreview();
      });
      contentDiv.appendChild(ta);
    } else if (block.type === 'table') {
      const lbl = document.createElement('div');
      lbl.textContent = `${block.headers ? block.headers.length : 0}개의 열, ${block.rows ? block.rows.length : 0}개의 행`;
      contentDiv.appendChild(lbl);
    } else {
      contentDiv.textContent = "[빈 줄]";
    }

    const delBtn = document.createElement('button');
    delBtn.className = 'icon-btn';
    delBtn.textContent = '❌';
    delBtn.style.padding = '0.2rem 0.5rem';
    delBtn.onclick = () => {
      blocks.splice(index, 1);
      renderBlocks();
      renderPreview();
    };

    item.appendChild(typeLabel);
    item.appendChild(contentDiv);
    item.appendChild(delBtn);
    container.appendChild(item);
  });
}

function renderPreview() {
  const container = document.getElementById('preview-panel');
  container.innerHTML = '';
  
  // A superficial HTML preview just to give a sense
  blocks.forEach(block => {
    if (block.type === 'paragraph') {
      const p = document.createElement('div');
      p.style.marginBottom = '8px';
      p.style.lineHeight = '1.6';
      
      if (block.styleId === "20") p.style.textAlign = 'center';
      if (block.charStyleId === "7" || block.charStyleId === "10") {
        p.style.fontWeight = 'bold';
        p.style.fontSize = '1.2rem';
      }

      p.textContent = block.text;
      container.appendChild(p);
    } else if (block.type === 'blank') {
      const br = document.createElement('br');
      container.appendChild(br);
    } else if (block.type === 'table') {
      const t = document.createElement('table');
      t.style.width = '100%';
      t.style.borderCollapse = 'collapse';
      t.style.marginBottom = '8px';
      
      if (block.headers && block.headers.length > 0) {
        const tr = document.createElement('tr');
        block.headers.forEach(h => {
          const th = document.createElement('th');
          th.textContent = h;
          th.style.border = '1px solid black';
          th.style.padding = '4px';
          th.style.background = '#f1f5f9';
          tr.appendChild(th);
        });
        t.appendChild(tr);
      }
      if (block.rows) {
        block.rows.forEach(row => {
          const tr = document.createElement('tr');
          row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell;
            td.style.border = '1px solid black';
            td.style.padding = '4px';
            tr.appendChild(td);
          });
          t.appendChild(tr);
        });
      }
      container.appendChild(t);
    }
  });
}

async function handleGenerateAI() {
  const prompt = document.getElementById('ai-prompt').value;
  if (!prompt) {
    alert("프롬프트를 입력하세요.");
    return;
  }
  
  const modelType = document.getElementById('ai-model-select').value;
  const btn = document.getElementById('btn-generate-ai');
  
  btn.disabled = true;
  btn.textContent = "생성 중...";

  try {
    const aiResult = await generateDocument(prompt, modelType);
    console.log(aiResult);
    
    if (aiResult.template) {
      const templateSelect = document.getElementById('template-select');
      const exists = [...templateSelect.options].some(o => o.value === aiResult.template);
      if (exists) {
        templateSelect.value = aiResult.template;
      }
    }
    
    if (aiResult.blocks) {
      blocks = aiResult.blocks;
      renderBlocks();
      renderPreview();
    }
    
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "AI로 생성하기 ▶";
  }
}

async function getBaseSectionDoc() {
  const baseSectionStr = Templates['base']['Contents/section0.xml'].content;
  const parser = new DOMParser();
  return parser.parseFromString(baseSectionStr, "application/xml");
}

async function handleDownload() {
  const templateName = document.getElementById('template-select').value;
  const baseDoc = await getBaseSectionDoc();
  
  const sectionXml = buildSectionXml(blocks, baseDoc);
  
  // pack
  const blob = await buildHwpx(templateName, "Generated Document", "AI Generator", sectionXml);
  
  // validate optionally
  const errors = await validateHwpx(blob);
  if (errors.length > 0) {
    console.warn("Validation Warning:", errors);
    // don't block download, just warn
    // alert("검증 경고가 있습니다. 콘솔을 확인하세요.");
  }

  downloadHwpx(blob, `document_${Date.now()}.hwpx`);
}

document.addEventListener('DOMContentLoaded', () => {
  initSettingsModal();
  
  renderBlocks();
  renderPreview();

  document.getElementById('btn-generate-ai').addEventListener('click', handleGenerateAI);
  document.getElementById('btn-download').addEventListener('click', handleDownload);
  
  document.getElementById('btn-add-block').addEventListener('click', () => {
    blocks.push({ type: "paragraph", styleId: "0", charStyleId: "0", text: "" });
    renderBlocks();
    renderPreview();
  });
});
