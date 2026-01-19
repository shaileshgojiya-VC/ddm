export function normalizeWebsite(website?: string) {
  if (!website) return "";

  const trimmed = website.trim();

  // already absolute with proper format
  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed;
  }

  // handle malformed URLs like "http:www.example.com" or "https:www.example.com"
  if (/^https?:/i.test(trimmed) && !/^https?:\/\//i.test(trimmed)) {
    // Replace "http:" or "https:" with "https://"
    return trimmed.replace(/^https?:/i, "https://");
  }

  // starts with www.
  if (/^www\./i.test(trimmed)) {
    return `https://${trimmed}`;
  }

  // fallback
  return `https://${trimmed}`;
}
