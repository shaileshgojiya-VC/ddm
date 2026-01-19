import { create } from "zustand";
import clientFetcher from "@/utils/fetcher/client";
import type { FilterConfig, FiltersResponse } from "@/types/filters";

type ModuleFiltersData = {
  module: string;
  filters: Record<string, FilterConfig>;
};

type FilterState = {
  filters: Record<string, ModuleFiltersData>; // module -> { module, filters }
  isLoading: boolean;
  error: string | null;
  fetchFilters: (token: string, module: string) => Promise<void>;
  getModuleFilters: (module: string) => Record<string, FilterConfig>;
};

export const useFilterStore = create<FilterState>((set, get) => ({
  filters: {},
  isLoading: false,
  error: null,

  fetchFilters: async (token, module) => {
    set({ isLoading: true, error: null });

    try {
      const response = await clientFetcher<FiltersResponse>({
        request: `filters?module=${module}`,
        method: "GET",
        token,
      });

      // Get module name from API response
      const moduleName = response?.data?.module ?? module;

      set((state) => ({
        filters: {
          ...state.filters,
          [moduleName]: {
            module: moduleName,
            filters: response?.data?.filters ?? {},
          },
        },
        isLoading: false,
      }));
    } catch (err: unknown) {
      const error = err as Error;
      set({
        error: error?.message || "Failed to fetch filters",
        isLoading: false,
      });
    }
  },

  getModuleFilters: (module: string) => {
    const state = get();
    return state?.filters?.[module]?.filters || {};
  },
}));
