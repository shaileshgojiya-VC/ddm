/**
 * Role-related types for the roles API
 */

/**
 * Role data structure from the API
 */
export interface RoleData {
  id: string;
  name: string;
  description: string;
  module_list: string[];
  status: "active" | "inactive";
  created_at: string;
  updated_at: string;
}

/**
 * The data object inside the roles response (what's inside response.data)
 */
export interface RolesResponse {
  items: RoleData[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}
