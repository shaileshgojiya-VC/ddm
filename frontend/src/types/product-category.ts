/**
 * Product category-related types for the products management module
 */

/**
 * Recursive product category structure matching the API response
 */
export interface ProductCategory {
  id: string;
  name: string;
  description: string | null;
  status: "active" | "inactive";
  product_count: number;
  parent_id: string | null;
  subcategory_id: string | null;
  child_categories: ProductCategory[];
  created_at: string;
  updated_at: string;
}

/**
 * Full API response structure for product categories
 * This matches what's inside response.data from serverFetcher
 */
export interface ProductCategoriesResponse {
  items: ProductCategory[];
  total_product_count: number;
}
