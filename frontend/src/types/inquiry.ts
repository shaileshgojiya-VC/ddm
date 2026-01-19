import { MailCommunication } from "@/types/mail-communication";
import { DocumentDetail } from "@/types/document-detail";

export interface UserDetail {
  id: string;
  name: string;
  email: string;
  role: string;
  role_type: string;
}

export interface ProductDetail {
  id: string;
  name: string;
  description: string | null;
  quantity: number | null;
  package_size: string | null;
  target_price: number | null;
  currency_id: string | null;
  certificate: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface StageTimeline {
  id: string;
  stage_name: string;
  stage_description: string;
  stage_number: number;
  stage_status: string;
  created_at: string;
  updated_at: string;
}

export interface Inquiry {
  id: number;
  name: string;
  phase: string;
  request_id: string;
  customer_company_name: string;
  customer_email: string;
  customer_country: string | null;
  customer_full_name: string | null;
  priority: string | null;
  bitrix_url: string | null;
  bitrix_id: number;
  company_name: string | null;
  group_name: string | null;
  prodcut_category: string;
  status: string;
  created_at: string;
  updated_at: string;
  stage_name: string;
  assigned_to: string | null;
  last_contact: string | null;
  etd: string | null;
  destination_country: string | null;
  user_details?: UserDetail[];
  product_details?: ProductDetail[];
  mail_communication?: MailCommunication[];
  document_details?: DocumentDetail[];
  stage_timeline?: StageTimeline[];
}

export interface InquiriesResponse {
  items: Inquiry[];
  pagination?: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
  data_count: {
    all: number;
    deal: number;
    lead: number;
    registration: number;
  };
}

export interface InquiriesSearchParams {
  search?: string;
  priority?: string;
  phase?: string;
  request_status?: string;
  stage_id?: string;
  country?: string;
  customer_id?: string;
  product_id?: string;
  start_date?: string;
  end_date?: string;
  user_id?: string;
  page?: string;
  limit?: string;
}
