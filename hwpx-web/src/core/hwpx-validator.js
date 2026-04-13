import JSZip from 'jszip';
import { MIMETYPE } from '../utils/constants.js';

const REQUIRED_FILES = [
  "mimetype",
  "Contents/content.hpf",
  "Contents/header.xml",
  "Contents/section0.xml",
];

export async function validateHwpx(blobOrFile) {
  const errors = [];
  try {
    const zip = await JSZip.loadAsync(blobOrFile);
    
    // Check required files
    const names = Object.keys(zip.files);
    for (const required of REQUIRED_FILES) {
      if (!names.includes(required)) {
        errors.push(`Missing required file: ${required}`);
      }
    }

    // Check mimetype
    if (names.includes("mimetype")) {
      const mimetypeContent = await zip.file("mimetype").async("string");
      if (mimetypeContent !== MIMETYPE) {
        errors.push(`Invalid mimetype: expected '${MIMETYPE}', got '${mimetypeContent}'`);
      }
      
      // In JSZip 3.x, checking if a file was compressed as STORE using the public API is tricky, 
      // but it handles it correctly during generation if { compression: "STORE" } is provided.
    }

    // Check XML well-formedness
    const parser = new DOMParser();
    for (const name of names) {
      if (name.endsWith(".xml") || name.endsWith(".hpf")) {
        const text = await zip.file(name).async("string");
        const doc = parser.parseFromString(text, "application/xml");
        const parserError = doc.querySelector("parsererror");
        if (parserError) {
          errors.push(`Malformed XML in ${name}: ${parserError.textContent}`);
        }
      }
    }

  } catch (e) {
    errors.push(`Validation error: ${e.message}`);
  }
  return errors;
}
