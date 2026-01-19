/**
 * Download utility for handling file downloads
 */

/**
 * Downloads a file from a URL
 * @param url - The URL of the file to download
 * @param filename - The name to save the file as
 */
export async function downloadFile(
  url: string,
  filename: string
): Promise<void> {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to download file: ${response.statusText}`);
    }

    const blob = await response.blob();
    downloadBlob(blob, filename);
  } catch (error) {
    console.error("Error downloading file:", error);
    throw error;
  }
}

/**
 * Downloads a blob as a file
 * @param blob - The blob to download
 * @param filename - The name to save the file as
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Downloads a file from base64 data
 * @param base64Data - The base64 encoded data
 * @param filename - The name to save the file as
 * @param mimeType - The MIME type of the file (default: application/pdf)
 */
export function downloadBase64File(
  base64Data: string,
  filename: string,
  mimeType: string = "application/pdf"
): void {
  try {
    // Remove data URL prefix if present
    const base64String = base64Data.replace(/^data:[^;]+;base64,/, "");

    // Convert base64 to blob
    const byteCharacters = atob(base64String);
    const byteNumbers = new Array(byteCharacters.length);

    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mimeType });

    downloadBlob(blob, filename);
  } catch (error) {
    console.error("Error downloading base64 file:", error);
    throw error;
  }
}
