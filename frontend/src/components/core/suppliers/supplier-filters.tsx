"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

import { SearchInput } from "@/components/core/search-input";
import SmartFilterDropdown from "@/components/core/smart-filter-dropdown";
import SuspenseLoader from "@/components/core/suspense-loader";
import { Card, CardContent } from "@/components/ui/card";
import { useModuleFilters } from "@/hooks/use-module-filters";
import { createFilterQueryString } from "@/utils/create-filter-query-string";

export default function SupplierFilters() {
  const { filters, isLoading } = useModuleFilters("supplier-management");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const showFilters = new Set([
    "search",
    "country",
    "company_type",
    "category",
  ]);

  // Extract search filter and dropdown filters
  const searchFilter = filters?.search;
  const dropdownFilters = Object.entries(filters || {}).filter(
    ([filterKey, filter]) =>
      showFilters.has(filterKey) && filter?.type !== "search"
  );

  const handleFilterChange = (filterType: string, value: string) => {
    startTransition(() => {
      const queryString = createFilterQueryString(searchParams, {
        [filterType]: value,
      });
      router.push(`/suppliers?${queryString}`);
    });
  };

  if (isLoading) {
    return <SuspenseLoader title="Loading filters..." />;
  }

  if (Object.keys(filters || {}).length === 0 || !filters) {
    return null;
  }

  return (
    <Card>
      <CardContent className="flex flex-col lg:flex-row items-center gap-4 pt-0">
        {/* Search Input */}
        {searchFilter && (
          <SearchInput
            placeholder={
              searchFilter?.placeholder || "Search by name, country, email..."
            }
            className="flex-1 w-full lg:w-auto"
          />
        )}

        {/* Dynamic Filter Dropdowns */}
        {dropdownFilters?.length > 0 && (
          <div className="flex flex-wrap flex-col sm:flex-row items-center gap-4 w-full lg:w-auto">
            {dropdownFilters?.map(([filterKey, filter]) => {
              const currentValue = searchParams.get(filter?.key) ?? "";
              return (
                <SmartFilterDropdown
                  key={filterKey}
                  config={filter}
                  currentValue={currentValue}
                  onFilterChange={handleFilterChange}
                  disabled={isPending}
                  triggerClassName="min-w-[100px]"
                  align="end"
                />
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
