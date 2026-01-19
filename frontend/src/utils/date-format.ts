/**
 * Format a date string to DD/MM/YYYY format
 *
 * @param date - The date to format (string, Date, or timestamp)
 * @returns Formatted date string (e.g., "11/09/2024")
 */
export function formatDate(date: string | Date | number): string {
  const dateObj =
    typeof date === "string" || typeof date === "number"
      ? new Date(date)
      : date;

  if (Number.isNaN(dateObj.getTime())) {
    return "Invalid date";
  }

  return dateObj.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}
