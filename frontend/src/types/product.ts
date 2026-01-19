/**
 * Product-related types for the products management module
 */

import { DocumentDetail } from "@/types/document-detail";

/**
 * Supplier details for a product
 */
export interface SupplierDetail {
  id: string;
  supplier_name?: string;
  price?: number;
  currency?: string;
  moq?: number;
  lead_times?: string;
  country_of_origin?: string;
  [key: string]: unknown;
}

/**
 * Logistics details for a product
 */
export interface LogisticsDetails {
  id: string;
  cartons_per_pallet: string | null;
  loading_quantities: string | null;
  transport_temperature?: string | null;
  storage_temperature: string | null;
  carton_dimensions: string | null;
  pallet_dimensions: string | null;
  term_of_delivery?: string | null;
}

/**
 * Main product interface matching the new API structure
 */
export interface Product {
  id: string;
  sku_id: string | null;
  barcode: string | null;
  hs_code: string | null;
  carton_barcode: string | null;
  art_number: string | null;
  unit_pack_size: string | null;
  units_per_carton: string | null;
  name: string;
  preview_text: string;
  short_name: string | null;
  bitrix_url: string | null;
  bitrix_id: string;
  description: string;
  category: string;
  sub_category: string;
  child_category: string;
  image_url: string;
  image_urls: string[];
  price: number;
  primary_supplier_name: string;
  net_content: string | null;
  net_content_unit: string;
  shelf_life: string | null;
  shelf_life_unit: string;
  carton_dimensions: string;
  cartons_per_pallet: string | null;
  pallet_dimensions: string | null;
  storage_conditions: string;
  sku_package: string;
  package_material: string;
  specification: string;
  brand_name: string | null;
  factory_name: string;
  country_of_origin: string;
  origin: string | null;
  loading_address: string;
  active_from: string;
  active_to: string;
  active_until: string;
  external_id: string;
  created_by: string;
  created_at: string;
  updated_by: string;
  updated_at: string;
  artwork_id: string | null;
  is_fda_approved: boolean;
  artwork_documents: string[];
  supplier_details: SupplierDetail[];
  logistics_details: LogisticsDetails | null;
  document_details: DocumentDetail[];
  currency_id: string;
  moq: string | null;
  moq_production: string | null;
  moq_packaging_matereal: string | null;
  lead_time_to_production: string | null;
  lead_time_to_print_packing_material: string | null;
  lead_time_to_reorder_packing_material: string | null;
}

export interface ProductsResponse {
  items: Product[];
  pagination?: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface ProductsSearchParams {
  search?: string;
  category?: string;
  sub_category?: string;
  child_category?: string;
  view?: "grid" | "list";
  page?: string;
  limit?: string;
}

export interface ProductCategory {
  id: string;
  name: string;
  count: number;
  subcategories?: ProductSubcategory[];
}

export interface ProductSubcategory {
  id: string;
  name: string;
  count: number;
}

export interface PriceHistory {
  id: string;
  productName: string;
  date: string;
  price: string;
  changePercentage: number;
  trend: "up" | "down" | "neutral";
}

/**
 * Form data type for product editing
 * Contains all Product fields except system-generated/read-only fields
 */
export type ProductFormData = {
  preview_text?: string;
  short_name?: string;
  description?: string;
  category?: string;
  sub_category?: string | null;
  child_category?: string | null;
  net_content?: string;
  sku_package?: string;
  package_material?: string;
  specification?: string;
  shelf_life?: string;
  sku_id?: string;
  barcode?: string;
  carton_barcode?: string;
  hs_code?: string;
  art_number?: string;
  unit_pack_size?: string;
  units_per_carton?: string;
  brand_name?: string;
  factory_name?: string;
  country_of_origin?: string;
  origin?: string | null;
  loading_address?: string | null;
  cartons_per_pallet?: string;
  loading_quantities?: string;
  transport_temperature?: string;
  storage_temperature?: string;
  carton_dimensions?: string;
  pallet_dimensions?: string;
  term_of_delivery?: string;
  is_fda_approved?: boolean;
};
