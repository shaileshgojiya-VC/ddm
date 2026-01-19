import {
  Product,
  ProductsResponse,
  ProductsSearchParams,
} from "@/types/product";
import {
  Supplier,
  SuppliersResponse,
  SuppliersSearchParams,
} from "@/types/supplier";
import type {
  Inquiry,
  InquiriesResponse,
  InquiriesSearchParams,
} from "@/types/inquiry";
import type { ProductCategoriesResponse } from "@/types/product-category";
import type {
  Profile,
  UpdateProfileRequest,
  User,
  UsersResponse,
  UsersSearchParams,
} from "@/types/user";
import serverFetcher from "@/utils/fetcher/server";

/**
 * Helper function to build URLSearchParams from an object with optional key mapping
 * @param params - Object containing the parameters
 * @param keyMap - Optional mapping of param keys to query param names
 * @param defaults - Optional default values to always include
 * @returns URLSearchParams instance
 */
function buildQueryParams(
  params: Record<string, string | undefined>,
  keyMap?: Record<string, string>,
  defaults?: Record<string, string>
): URLSearchParams {
  const queryParams = new URLSearchParams();

  // Add default values first
  if (defaults) {
    Object.entries(defaults).forEach(([key, value]) => {
      queryParams.set(key, value);
    });
  }

  // Add params with optional key mapping
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      const queryKey = keyMap?.[key] ?? key;
      queryParams.set(queryKey, value);
    }
  });

  return queryParams;
}

/**
 * Fetches product details by ID from the server
 * @param id - The product ID
 * @returns Product details or empty object if not found
 */
export async function getProductDetails(id: string): Promise<Product> {
  const response = await serverFetcher<Product>({
    request: `product/${id}`,
    token: true,
  });
  return response?.data;
}

/**
 * Fetches supplier details by ID from the server
 * @param id - The supplier ID
 * @returns Supplier details or empty object if not found
 */
export async function getSupplierDetails(id: string): Promise<Supplier> {
  const response = await serverFetcher<Supplier>({
    request: `supplier/${id}`,
    token: true,
  });
  return response?.data ?? {};
}

/**
 * Fetches suppliers list from the server with search params
 * @param searchParams - The search parameters for filtering suppliers
 * @returns Object containing suppliers and pagination
 */
export async function getSuppliers(searchParams: SuppliersSearchParams) {
  const {
    search,
    country,
    company_type,
    category,
    page = "1",
    limit = "10",
  } = searchParams;

  const queryParams = buildQueryParams(
    { search, country, company_type, category },
    undefined,
    { page, limit }
  );

  const response = await serverFetcher<SuppliersResponse>({
    request: `suppliers?${queryParams.toString()}`,
    token: true,
  });

  return {
    suppliers: response?.data?.items,
    pagination: response?.pagination,
  };
}

/**
 * Fetches inquiry details by ID from the server
 * @param id - The inquiry ID
 * @returns Inquiry details or empty object if not found
 */
export async function getInquiryDetails(id: string): Promise<Inquiry> {
  const response = await serverFetcher<Inquiry>({
    request: `request/${id}`,
    token: true,
  });
  return response?.data ?? {};
}

/**
 * Fetches product categories from the server
 * @returns Product categories response or empty object if not found
 */
export async function getCategories(): Promise<ProductCategoriesResponse> {
  const response = await serverFetcher<ProductCategoriesResponse>({
    request: "product/category/list",
    token: true,
  });
  return response?.data ?? {};
}

/**
 * Fetches products list from the server with search params
 * @param searchParams - The search parameters for filtering products
 * @returns Object containing products and pagination
 */
export async function getProducts(searchParams: ProductsSearchParams) {
  const {
    search,
    category,
    sub_category,
    child_category,
    page = "1",
    limit = "10",
  } = searchParams;

  const queryParams = buildQueryParams(
    { search, category, sub_category, child_category },
    {
      category: "category_id",
      sub_category: "sub_category_id",
      child_category: "child_category_id",
    },
    { page, limit }
  );

  const response = await serverFetcher<ProductsResponse>({
    request: `product/list?${queryParams.toString()}`,
    token: true,
  });
  return {
    products: response?.data?.items,
    pagination: response?.pagination,
  };
}

/**
 * Fetches user details by ID from the server
 * @param id - The user ID
 * @returns User details or null if not found
 */
export async function getUserDetails(id: string): Promise<User | null> {
  const response = await serverFetcher<User>({
    request: `auth/user/${id}`,
    method: "GET",
    token: true,
  });

  return response.data ?? null;
}

/**
 * Fetches users list from the server with search params
 * @param searchParams - The search parameters for filtering users
 * @returns Object containing users, pagination, and active counts
 */
export async function getUsers(searchParams: UsersSearchParams) {
  const { search, role_id, page = "1", limit = "10" } = searchParams;

  const queryParams = buildQueryParams({ search, role_id }, undefined, {
    page,
    limit,
  });

  const response = await serverFetcher<UsersResponse>({
    request: `auth/users?${queryParams.toString()}`,
    token: true,
  });
  return {
    users: response.data?.items ?? [],
    pagination: response?.pagination ?? undefined,
    activeCounts: response.data?.active_counts ?? {},
  };
}

/**
 * Fetches inquiries list from the server with search params
 * @param searchParams - The search parameters for filtering inquiries
 * @returns Object containing inquiries, pagination, and data count
 */
export async function getInquiries(searchParams: InquiriesSearchParams) {
  const {
    search,
    priority,
    phase,
    request_status,
    stage_id,
    country,
    customer_id,
    product_id,
    start_date,
    end_date,
    user_id,
    page = "1",
    limit = "10",
  } = searchParams;

  const queryParams = buildQueryParams(
    {
      search,
      priority,
      phase,
      request_status,
      stage_id,
      country,
      customer_id,
      product_id,
      start_date,
      end_date,
      user_id,
    },
    undefined,
    { page, limit }
  );

  const response = await serverFetcher<InquiriesResponse>({
    request: `request/list?${queryParams.toString()}`,
    token: true,
  });
  return {
    inquiries: response?.data?.items,
    pagination: response?.pagination,
    dataCount: response?.data?.data_count,
  };
}

/**
 * Fetches current user's profile from the server
 * @returns Profile data or null if not found
 */
export async function getProfile(): Promise<Profile | null> {
  const response = await serverFetcher<Profile>({
    request: "auth/profile",
    method: "GET",
    token: true,
  });

  return response.data ?? null;
}

/**
 * Updates current user's profile
 * @param data - Profile update data (name, phone_number, location)
 * @returns Updated profile data
 */
export async function updateProfile(
  data: UpdateProfileRequest
): Promise<Profile | null> {
  const response = await serverFetcher<Profile>({
    request: "auth/profile",
    method: "PUT",
    payload: data as Record<string, unknown>,
    token: true,
  });

  return response.data ?? null;
}
