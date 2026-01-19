/**
 * Creates a query string for filter changes
 * - Updates/removes filter parameters based on value
 * - Resets to page 1 when filters change
 * - Preserves other existing query parameters
 */
export function createFilterQueryString(
  currentSearchParams: URLSearchParams,
  params: Record<string, string>
): string {
  const newSearchParams = new URLSearchParams(currentSearchParams.toString());

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      newSearchParams.set(key, value);
    } else {
      newSearchParams.delete(key);
    }
  });

  // Reset to page 1 when filters change
  newSearchParams.set("page", "1");

  return newSearchParams.toString();
}
