export interface FilterOption {
  label: string;
  value: string | number;
}

export interface FilterGroup {
  group_key: string;
  group_label: string;
  order_sequence: number;
  items: FilterOption[];
}

export interface FilterConfig {
  key: string;
  label: string;
  type?: "search" | "static" | "dynamic";
  placeholder?: string;
  options?: FilterOption[];
  grouped?: boolean;
  groups?: FilterGroup[];
  total_options?: number;
}

export interface FiltersData {
  module: string;
  filters: Record<string, FilterConfig>;
}

export interface FiltersResponse {
  module: string;
  filters: Record<string, FilterConfig>;
}

export interface SmartFilterDropdownProps {
  config: FilterConfig;
  currentValue: string;
  onFilterChange: (filterType: string, value: string) => void;
  disabled?: boolean;
  triggerClassName?: string;
  align?: "start" | "end" | "center";
}

export type FilterRow =
  | { type: "group"; label: string }
  | { type: "item"; label: string; value: string };
