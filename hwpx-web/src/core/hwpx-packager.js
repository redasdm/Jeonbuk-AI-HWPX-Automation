import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Templates } from '../templates/bundled.js';
import { MIMETYPE } from '../utils/constants.js';

function updateMetadata(hpfContent, title, creator) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(hpfContent, "application/xml");
  const ns = "http://www.idpf.org/2007/opf/";
  
  if (title) {
    const titleEls = doc.getElementsByTagNameNS(ns, "title");
    if (titleEls.length > 0) {
      titleEls[0].textContent = title;
    }
  }

  const now = new Date();
  const isoNow = now.toISOString().split('.')[0] + 'Z';
  const metas = doc.getElementsByTagNameNS(ns, "meta");

  for (let i = 0; i < metas.length; i++) {
    const meta = metas[i];
    const name = meta.getAttribute("name");
    if (creator && name === "creator") {
      meta.textContent = creator;
    } else if (creator && name === "lastsaveby") {
      meta.textContent = creator;
    } else if (name === "CreatedDate" || name === "ModifiedDate") {
      meta.textContent = isoNow;
    } else if (name === "date") {
      meta.textContent = `${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일`;
    }
  }

  const serializer = new XMLSerializer();
  return `<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n` + serializer.serializeToString(doc);
}

export async function buildHwpx(templateName, title, creator, generatedSectionXml) {
  const zip = new JSZip();

  // MUST add mimetype first as STORE (uncompressed)
  zip.file("mimetype", MIMETYPE, { compression: "STORE" });

  const templatesToApply = ['base'];
  if (templateName && templateName !== 'base') {
    templatesToApply.push(templateName);
  }

  let contentHpf = "";

  for (const tpl of templatesToApply) {
    const tplFiles = Templates[tpl];
    if (!tplFiles) continue;

    for (const [relPath, fileInfo] of Object.entries(tplFiles)) {
      if (relPath === "mimetype" || relPath === "Contents/section0.xml") continue;

      let content = fileInfo.content;
      if (relPath === "Contents/content.hpf") {
        // Keep string reference of content.hpf to update metadata later
        contentHpf = content;
      } else {
        if (fileInfo.type === 'base64') {
          zip.file(relPath, content, { base64: true });
        } else {
          zip.file(relPath, content);
        }
      }
    }
  }

  // Add updated content.hpf
  if (contentHpf) {
    contentHpf = updateMetadata(contentHpf, title, creator);
    zip.file("Contents/content.hpf", contentHpf);
  }

  // Add generated section0.xml
  zip.file("Contents/section0.xml", generatedSectionXml);

  const blob = await zip.generateAsync({ type: "blob" });
  return blob;
}

export function downloadHwpx(blob, filename) {
  saveAs(blob, filename || "document.hwpx");
}
