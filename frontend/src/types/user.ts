/**
 * User-related types for the users management module
 */

export interface InquiryData {
  id: string;
  phase: string;
  stage: string | null;
  customer_name: string;
  company_name: string | null;
}

export interface UserRole {
  id: string;
  name: string;
  description: string;
  module_list: string[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole | null;
  status: "active" | "inactive" | "pending" | "deleted";
  joined_at: string;
  created_at: string;
  updated_at: string;
  // Optional fields that may be present in user detail endpoint
  total_inquiry?: number;
  active_deals?: number;
  deals_won?: number;
  inquiries: InquiryData[];
}

// Active counts by role name
export interface ActiveCounts {
  [roleName: string]: number;
}

// The data object inside the response (what's inside response.data)
export interface UsersResponse {
  items: User[];
  active_counts: ActiveCounts;
}

export interface UsersSearchParams {
  search?: string;
  role?: string;
  role_id?: string;
  status?: string;
  page?: string;
  limit?: string;
}
