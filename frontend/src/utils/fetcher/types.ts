export interface Pagination {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface IResponse<T> {
  data: T;
  message: string;
  status: "success" | "Error";
  status_code: number;
  success: boolean;
  pagination?: Pagination; // Pagination at root level for list endpoints
}

type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type Payload = Record<string, unknown> | null;

export interface FetcherProps {
  request: string;
  method?: RequestMethod;
  payload?: Payload;
  headerOptions?: { [key: string]: string };
  type?: "default" | "report" | "log";
  options?: Record<string, unknown>;
}

export interface Service {
  [key: string]: string;
}
