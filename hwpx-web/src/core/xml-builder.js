import { NS } from '../utils/constants.js';

let pidCounter = 1000000001;
function genPid() {
  return (pidCounter++).toString();
}

/**
 * Build section0.xml from a list of blocks.
 * @param {Array} blocks 
 * @param {Document} baseSection0Doc The base section0.xml parsed into a DOM Document (to copy secPr and colPr)
 */
export function buildSectionXml(blocks, baseSection0Doc) {
  const doc = document.implementation.createDocument(NS.hs, "hs:sec", null);
  doc.documentElement.setAttribute("xmlns:hs", NS.hs);
  doc.documentElement.setAttribute("xmlns:hp", NS.hp);
  doc.documentElement.setAttribute("xmlns:hc", NS.hc);
  doc.documentElement.setAttribute("xmlns:hh", NS.hh);

  // Copy first paragraph from base document to preserve secPr and colPr
  const baseFirstP = baseSection0Doc.querySelector("p");
  let firstP;
  if (baseFirstP) {
    firstP = doc.importNode(baseFirstP, true);
    // Clear the text contents but keep secPr and ctrl
    const runs = firstP.querySelectorAll("run");
    runs.forEach(run => {
      const ts = run.querySelectorAll("t");
      ts.forEach(t => t.textContent = "");
    });
    firstP.setAttribute("id", genPid());
  } else {
    // Fallback if no base
    firstP = createEmptyParagraph(doc, "0", "0");
  }
  
  doc.documentElement.appendChild(firstP);

  // Append user blocks
  blocks.forEach(block => {
    if (block.type === "paragraph") {
      doc.documentElement.appendChild(createParagraph(doc, block.styleId, block.charStyleId, block.text));
    } else if (block.type === "blank") {
      doc.documentElement.appendChild(createEmptyParagraph(doc, "0", "0"));
    } else if (block.type === "table") {
      doc.documentElement.appendChild(createTable(doc, block.headers, block.rows, block.styleContext));
    }
  });

  const serializer = new XMLSerializer();
  return `<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n` + serializer.serializeToString(doc);
}

export function createParagraph(doc, paraPrId, charPrId, text) {
  const p = doc.createElementNS(NS.hp, "hp:p");
  p.setAttribute("id", genPid());
  p.setAttribute("paraPrIDRef", paraPrId || "0");
  p.setAttribute("styleIDRef", "0");
  p.setAttribute("pageBreak", "0");
  p.setAttribute("columnBreak", "0");
  p.setAttribute("merged", "0");

  const run = doc.createElementNS(NS.hp, "hp:run");
  run.setAttribute("charPrIDRef", charPrId || "0");

  const lines = (text || "").split('\n');
  lines.forEach((line, index) => {
    const t = doc.createElementNS(NS.hp, "hp:t");
    t.textContent = line;
    run.appendChild(t);
    if (index < lines.length - 1) {
      // For newlines inside a paragraph block, use empty <hp:t> space or another mechanism?
      // In HWPX, new line inside a paragraph is usually <hp:lineBreak/>
      const lb = doc.createElementNS(NS.hp, "hp:lineBreak");
      run.appendChild(lb);
    }
  });

  if (lines.length === 1 && lines[0] === "") {
    const t = doc.createElementNS(NS.hp, "hp:t");
    run.appendChild(t);
  }

  p.appendChild(run);
  return p;
}

export function createEmptyParagraph(doc, paraPrId, charPrId) {
  return createParagraph(doc, paraPrId, charPrId, "");
}

export function createTable(doc, headers, rows, styleContext = {}) {
  // Default values
  const tableParaPrId = styleContext.tableParaPrId || "1";
  const borderFillId = styleContext.borderFillId || "4"; // Usually normal border + background or not
  const headerParaPrId = styleContext.headerParaPrId || "21"; // CENTER
  const headerCharPrId = styleContext.headerCharPrId || "10"; // BOLD
  const cellParaPrId = styleContext.cellParaPrId || "22"; // JUSTIFY
  const cellCharPrId = styleContext.cellCharPrId || "0";  // Normal

  const p = doc.createElementNS(NS.hp, "hp:p");
  p.setAttribute("id", genPid());
  p.setAttribute("paraPrIDRef", tableParaPrId);
  p.setAttribute("styleIDRef", "0");
  p.setAttribute("pageBreak", "0");
  p.setAttribute("columnBreak", "0");
  p.setAttribute("merged", "0");

  const run = doc.createElementNS(NS.hp, "hp:run");
  run.setAttribute("charPrIDRef", "0");

  // total width is 42520 for A4
  const numCols = headers.length;
  // Calculate equal widths
  const colWidths = Array(numCols).fill(Math.floor(42520 / numCols));
  // adjust the last one
  colWidths[numCols - 1] += 42520 - colWidths.reduce((a, b) => a + b, 0);

  const numRows = rows.length + (headers.length > 0 ? 1 : 0);

  const tbl = doc.createElementNS(NS.hp, "hp:tbl");
  tbl.setAttribute("id", genPid());
  tbl.setAttribute("zOrder", "0");
  tbl.setAttribute("numberingType", "TABLE");
  tbl.setAttribute("textWrap", "TOP_AND_BOTTOM");
  tbl.setAttribute("textFlow", "BOTH_SIDES");
  tbl.setAttribute("lock", "0");
  tbl.setAttribute("pageBreak", "CELL");
  tbl.setAttribute("repeatHeader", "1");
  tbl.setAttribute("rowCnt", numRows.toString());
  tbl.setAttribute("colCnt", numCols.toString());
  tbl.setAttribute("cellSpacing", "0");
  tbl.setAttribute("borderFillIDRef", borderFillId);
  tbl.setAttribute("noAdjust", "0");

  const sz = doc.createElementNS(NS.hp, "hp:sz");
  sz.setAttribute("width", "42520");
  sz.setAttribute("widthRelTo", "ABSOLUTE");
  sz.setAttribute("height", "10000");
  sz.setAttribute("heightRelTo", "ABSOLUTE");
  sz.setAttribute("protect", "0");
  tbl.appendChild(sz);

  const pos = doc.createElementNS(NS.hp, "hp:pos");
  pos.setAttribute("treatAsChar", "1");
  pos.setAttribute("affectLSpacing", "0");
  pos.setAttribute("flowWithText", "1");
  pos.setAttribute("allowOverlap", "0");
  pos.setAttribute("holdAnchorAndSO", "0");
  pos.setAttribute("vertRelTo", "PARA");
  pos.setAttribute("horzRelTo", "COLUMN");
  pos.setAttribute("vertAlign", "TOP");
  pos.setAttribute("horzAlign", "LEFT");
  pos.setAttribute("vertOffset", "0");
  pos.setAttribute("horzOffset", "0");
  tbl.appendChild(pos);

  const outMargin = doc.createElementNS(NS.hp, "hp:outMargin");
  outMargin.setAttribute("left", "0"); outMargin.setAttribute("right", "0");
  outMargin.setAttribute("top", "0"); outMargin.setAttribute("bottom", "0");
  tbl.appendChild(outMargin);

  const inMargin = doc.createElementNS(NS.hp, "hp:inMargin");
  inMargin.setAttribute("left", "0"); inMargin.setAttribute("right", "0");
  inMargin.setAttribute("top", "0"); inMargin.setAttribute("bottom", "0");
  tbl.appendChild(inMargin);

  // Helper to create Cell
  const createTd = (text, rowIndex, colIndex, isHeader) => {
    const tc = doc.createElementNS(NS.hp, "hp:tc");
    tc.setAttribute("name", "");
    tc.setAttribute("header", isHeader ? "1" : "0");
    tc.setAttribute("hasMargin", "0");
    tc.setAttribute("protect", "0");
    tc.setAttribute("editable", "0");
    tc.setAttribute("dirty", "0");
    tc.setAttribute("borderFillIDRef", borderFillId);

    const subList = doc.createElementNS(NS.hp, "hp:subList");
    subList.setAttribute("id", "");
    subList.setAttribute("textDirection", "HORIZONTAL");
    subList.setAttribute("lineWrap", "BREAK");
    subList.setAttribute("vertAlign", "CENTER");
    subList.setAttribute("linkListIDRef", "0");
    subList.setAttribute("linkListNextIDRef", "0");
    subList.setAttribute("textWidth", "0");
    subList.setAttribute("textHeight", "0");
    subList.setAttribute("hasTextRef", "0");
    subList.setAttribute("hasNumRef", "0");
    
    // Split cell text by newline
    const lines = text.split('\n');
    lines.forEach(line => {
      const pCell = doc.createElementNS(NS.hp, "hp:p");
      pCell.setAttribute("id", genPid());
      pCell.setAttribute("paraPrIDRef", isHeader ? headerParaPrId : cellParaPrId);
      pCell.setAttribute("styleIDRef", "0");
      pCell.setAttribute("pageBreak", "0");
      pCell.setAttribute("columnBreak", "0");
      pCell.setAttribute("merged", "0");

      const rCell = doc.createElementNS(NS.hp, "hp:run");
      rCell.setAttribute("charPrIDRef", isHeader ? headerCharPrId : cellCharPrId);

      const tCell = doc.createElementNS(NS.hp, "hp:t");
      tCell.textContent = line;
      rCell.appendChild(tCell);
      pCell.appendChild(rCell);
      subList.appendChild(pCell);
    });

    if (lines.length === 0) {
      const pCell = doc.createElementNS(NS.hp, "hp:p");
      pCell.setAttribute("id", genPid());
      pCell.setAttribute("paraPrIDRef", isHeader ? headerParaPrId : cellParaPrId);
      const rCell = doc.createElementNS(NS.hp, "hp:run");
      rCell.setAttribute("charPrIDRef", isHeader ? headerCharPrId : cellCharPrId);
      rCell.appendChild(doc.createElementNS(NS.hp, "hp:t"));
      pCell.appendChild(rCell);
      subList.appendChild(pCell);
    }

    tc.appendChild(subList);

    const cellAddr = doc.createElementNS(NS.hp, "hp:cellAddr");
    cellAddr.setAttribute("colAddr", colIndex.toString());
    cellAddr.setAttribute("rowAddr", rowIndex.toString());
    tc.appendChild(cellAddr);

    const cellSpan = doc.createElementNS(NS.hp, "hp:cellSpan");
    cellSpan.setAttribute("colSpan", "1");
    cellSpan.setAttribute("rowSpan", "1");
    tc.appendChild(cellSpan);

    const cellSz = doc.createElementNS(NS.hp, "hp:cellSz");
    cellSz.setAttribute("width", colWidths[colIndex].toString());
    cellSz.setAttribute("height", "3000");
    tc.appendChild(cellSz);

    const cellMargin = doc.createElementNS(NS.hp, "hp:cellMargin");
    cellMargin.setAttribute("left", "141"); cellMargin.setAttribute("right", "141");
    cellMargin.setAttribute("top", "141"); cellMargin.setAttribute("bottom", "141");
    tc.appendChild(cellMargin);

    return tc;
  };

  let rowIndex = 0;
  if (headers && headers.length > 0) {
    const tr = doc.createElementNS(NS.hp, "hp:tr");
    headers.forEach((h, colIndex) => {
      tr.appendChild(createTd(h, rowIndex, colIndex, true));
    });
    tbl.appendChild(tr);
    rowIndex++;
  }

  if (rows) {
    rows.forEach(row => {
      const tr = doc.createElementNS(NS.hp, "hp:tr");
      row.forEach((text, colIndex) => {
         tr.appendChild(createTd(text, rowIndex, colIndex, false));
      });
      tbl.appendChild(tr);
      rowIndex++;
    });
  }

  run.appendChild(tbl);
  p.appendChild(run);

  return p;
}
