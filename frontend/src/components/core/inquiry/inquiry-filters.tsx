"use client";

import { Filter, X } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useTransition } from "react";

import DateRangePicker from "@/components/core/date-range-picker";
import { SearchInput } from "@/components/core/search-input";
import SmartFilterDropdown from "@/components/core/smart-filter-dropdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useModuleFilters } from "@/hooks/use-module-filters";
import { createFilterQueryString } from "@/utils/create-filter-query-string";
import SuspenseLoader from "@/components/core/suspense-loader";

export default function InquiryFilters() {
  const { filters, isLoading } = useModuleFilters("inquiry-management");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [isExpanded, setIsExpanded] = useState(false);
  const showFilters = new Set([
    "search",
    "priority",
    "stage_id",
    "request_status",
    "user_id",
    "country",
    "customer_id",
    "product_id",
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
      router.push(`/inquiry-management?${queryString}`);
    });
  };

  // Count active filters (excluding search and page)
  const activeFiltersCount = Array.from(searchParams.entries()).filter(
    ([key]) =>
      key !== "search" && key !== "page" && key !== "limit" && key !== "phase"
  ).length;

  // Clear all filters
  const handleClearFilters = () => {
    startTransition(() => {
      const newSearchParams = new URLSearchParams();
      const search = searchParams.get("search");
      if (search) {
        newSearchParams.set("search", search);
      }
      const phase = searchParams.get("phase");
      if (phase) {
        newSearchParams.set("phase", phase);
      }
      const limit = searchParams.get("limit");
      if (limit) {
        newSearchParams.set("limit", limit);
      }
      newSearchParams.set("page", "1");
      router.push(`/inquiry-management?${newSearchParams.toString()}`);
    });
  };

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-4 pt-0">
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full">
          <SearchInput
            placeholder={
              searchFilter?.placeholder ||
              "Search by ID, customer, email, product, region..."
            }
            className="flex-1 w-full sm:w-auto"
          />

          <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
            <Button
              variant={isExpanded ? "default" : "outline"}
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex-1"
            >
              <Filter className="size-4 mr-2" />
              Filters
              {activeFiltersCount > 0 && (
                <Badge
                  variant="secondary"
                  className="ml-2 rounded-full px-1.5 py-0 text-xs min-w-5 h-5"
                >
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
            {activeFiltersCount > 0 && (
              <Button
                variant="outline"
                onClick={handleClearFilters}
                disabled={isPending}
                className="flex-1"
              >
                <X className="size-4" />
                Clear
              </Button>
            )}
          </div>
        </div>
        {isExpanded && (
          <>
            <Separator />
            <div className="space-y-3 w-full">
              {isLoading && <SuspenseLoader title="Loading filters..." />}
              {dropdownFilters?.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {dropdownFilters?.length > 0 &&
                    dropdownFilters?.map(([filterKey, filter]) => {
                      const currentValue = searchParams.get(filter?.key) ?? "";
                      return (
                        <SmartFilterDropdown
                          key={filterKey}
                          config={filter}
                          currentValue={currentValue}
                          onFilterChange={handleFilterChange}
                          disabled={isPending}
                        />
                      );
                    })}
                  <DateRangePicker />
                </div>
              )}
              {dropdownFilters?.length === 0 && !isLoading && (
                <SuspenseLoader title="No filters found..." />
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
