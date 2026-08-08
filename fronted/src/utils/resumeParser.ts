export interface ResumeParseResult {
  text: string;
  fileName: string;
  format: 'text' | 'pdf' | 'docx';
}

const MAX_RESUME_CHARS = 2000;

export async function extractResumeText(file: File): Promise<ResumeParseResult> {
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('File too large. Please upload a resume smaller than 5MB.');
  }

  const name = file.name.toLowerCase();

  if (name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.text')) {
    const text = await file.text();
    return { text: text.trim().slice(0, MAX_RESUME_CHARS), fileName: file.name, format: 'text' };
  }

  if (name.endsWith('.pdf')) {
    const text = await parsePdf(file);
    return { text: text.trim().slice(0, MAX_RESUME_CHARS), fileName: file.name, format: 'pdf' };
  }

  if (name.endsWith('.docx')) {
    const text = await parseDocx(file);
    return { text: text.trim().slice(0, MAX_RESUME_CHARS), fileName: file.name, format: 'docx' };
  }

  throw new Error('Unsupported file type. Please upload a .txt, .pdf, or .docx file.');
}

async function parsePdf(file: File): Promise<string> {
  const pdfjsLib = await import('pdfjs-dist');
  const workerUrl = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default;
  pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) }).promise;

  let output = '';
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const pageText = content.items
      .map((item) => ('str' in item ? (item as { str: string }).str : ''))
      .join(' ');
    output += pageText + '\n';
  }
  return output;
}

async function parseDocx(file: File): Promise<string> {
  const mammoth = await import('mammoth');
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  return result.value;
}
