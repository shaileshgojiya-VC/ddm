"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useFilterStore } from "@/stores/use-filter-store";

/**
 * Hook to fetch and manage filters for a specific module
 * @param module - The module name (e.g., "inquiry-management", "supplier-management")
 */
export function useModuleFilters(module: string) {
  const { data: session } = useSession();
  const { isLoading, fetchFilters, filters: allFilters } = useFilterStore();
  const moduleData = allFilters[module];
  const moduleFilters = moduleData?.filters || {};

  useEffect(() => {
    // Only fetch if:
    // 1. User is authenticated
    // 2. Module data doesn't exist yet
    if (session?.accessToken && !moduleData) {
      fetchFilters(session.accessToken, module);
    }
  }, [session, fetchFilters, moduleData, module]);

  return {
    filters: moduleFilters,
    isLoading,
  };
}
