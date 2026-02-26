const MAX_UPLOAD_MB = 10;
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".doc",
  ".docx",
  ".txt",
  ".rtf",
  ".png",
  ".jpg",
  ".jpeg",
  ".csv",
  ".xls",
  ".xlsx",
];
const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "application/rtf",
  "text/rtf",
  "image/png",
  "image/jpeg",
  "text/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

function extname(filename = "") {
  const idx = String(filename).lastIndexOf(".");
  if (idx < 0) return "";
  return String(filename).slice(idx).toLowerCase();
}

export function validateSelectedFiles(files = []) {
  const valid = [];
  const errors = [];

  for (const file of files) {
    const ext = extname(file?.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      errors.push(`${file?.name || "arquivo"}: tipo não permitido (${ext || "sem extensão"})`);
      continue;
    }
    if ((file?.size || 0) > MAX_UPLOAD_BYTES) {
      errors.push(`${file?.name || "arquivo"}: excede ${MAX_UPLOAD_MB}MB`);
      continue;
    }
    const mime = String(file?.type || "").toLowerCase();
    if (mime && !ALLOWED_MIME_TYPES.includes(mime)) {
      errors.push(`${file?.name || "arquivo"}: MIME não permitido (${mime})`);
      continue;
    }
    valid.push(file);
  }

  return {
    valid,
    errors,
    maxMb: MAX_UPLOAD_MB,
    allowedExtensions: ALLOWED_EXTENSIONS,
    allowedMimes: ALLOWED_MIME_TYPES,
  };
}
