export interface File {
  id: string;
  name: string;
  url: string;
}
export interface URLType {
  downloadUrl: string;
  showUrl: string;
}
export interface DocumentDetail {
  id: string;
  name: string;
  url: URLType;
  path: string;
  file_name: string;
  file_type: string;
  file_size: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}
