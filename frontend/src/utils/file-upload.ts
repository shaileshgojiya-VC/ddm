export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB in bytes

export interface FileValidationResult {
  isValid: boolean;
  error?: string;
}

export function validateFileSize(file: File): FileValidationResult {
  if (file.size > MAX_FILE_SIZE) {
    return {
      isValid: false,
      error: `File size exceeds 100 MB. Please select a smaller file.`,
    };
  }
  return { isValid: true };
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

export function getFileIcon(fileName: string): string {
  const extension = fileName.split(".").pop()?.toLowerCase();

  const iconMap: Record<string, string> = {
    // Documents
    pdf: "📄",
    doc: "📝",
    docx: "📝",
    txt: "📝",
    // Spreadsheets
    xls: "📊",
    xlsx: "📊",
    csv: "📊",
    // Presentations
    ppt: "📊",
    pptx: "📊",
    // Images
    jpg: "🖼️",
    jpeg: "🖼️",
    png: "🖼️",
    gif: "🖼️",
    // Archives
    zip: "🗜️",
    rar: "🗜️",
    "7z": "🗜️",
    // Default
    default: "📎",
  };

  return iconMap[extension || ""] || iconMap.default;
}
