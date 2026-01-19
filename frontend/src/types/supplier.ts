/**
 * Supplier-related types for the suppliers management module
 */

import { DocumentDetail } from "@/types/document-detail";
import { MailCommunication } from "@/types/mail-communication";

// Re-export Pagination from fetcher types for convenience
export type { Pagination } from "@/utils/fetcher/types";

/**
 * Product details within a supplier
 */
export interface SupplierProductDetail {
  id: string;
  name: string;
  description: string;
  category: string;
  sub_category: string;
  image_url: string;
  price: number;
  currency: string | null;
  primary_supplier_name: string;
  created_at: string;
  updated_at: string;
  status: string;
  sku_id: string;
}

/**
 * Price history details for supplier products
 */
export interface SupplierPriceHistory {
  id: string;
  product_name: string;
  price: number;
  currency: string;
  effective_from: string;
  effective_to: string;
}

/**
 * Main supplier interface matching the API response
 */
export interface Supplier {
  // Primary identifier
  id: string;

  // Company information
  company_name: string;
  company_type: string | null;
  supplier_name: string;

  // Contact information
  email: string;
  phone_number: string;
  website: string;
  messanger_type: string;
  messanger_number: string | null;
  created_by: string;
  created_on: string;
  modified_by: string;
  generated_by: string;
  buyer_type: string;
  products_manufactured: string;
  assigned_by: string;

  // Business information
  rating: number;
  address: string;
  country: string;
  responsible_person_name: string;
  industry: string;
  type_of_buyer: string | null;
  prefix: string | null;
  vat_number: string | null;
  registraction_number: string | null;

  // Timestamps
  created_at: string;
  updated_at: string;
  updated_by: string;
  last_contact: string | null;

  // Categories
  category: string[];
  sub_category: string[];
  child_category: string[];

  // Related data
  product_details: SupplierProductDetail[];
  price_history_details: SupplierPriceHistory[];
  mail_communication: MailCommunication[];
  document_details: DocumentDetail[];
}

// The response structure (items at root level, not nested in data)
export interface SuppliersResponse {
  items: Supplier[];
  pagination?: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface SuppliersSearchParams {
  search?: string;
  country?: string;
  company_type?: string;
  category?: string;
  view?: "grid" | "list";
  page?: string;
  limit?: string;
}

/**
 * Form data type for supplier editing
 * Contains all Supplier fields except system-generated/read-only fields
 */
export type SupplierFormData = {
  company_name?: string;
  prefix?: string | null;
  company_type?: string | null;
  industry?: string;
  address?: string;
  country?: string;
  email?: string;
  phone_number?: string;
  website?: string;
  messanger_number?: string | null;
  vat_number?: string | null;
  registraction_number?: string | null;
  supplier_name?: string;
  buyer_type?: string;
  products_manufactured?: string;
  sub_category?: string[];
  child_category?: string[];
};
