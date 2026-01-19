"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InquiriesResponse } from "@/types/inquiry";

interface TabItem {
  label: string;
  value: string;
  count?: number;
}

// Helper function to get badge color based on tab value
function getCountBadgeColor(tabValue: string): string {
  const colorMap: Record<string, string> = {
    all: "bg-muted",
    lead: "bg-blue-100 text-blue-700",
    registration: "bg-amber-100 text-amber-700",
    deal: "bg-green-100 text-green-700",
  };
  return colorMap[tabValue] || "bg-gray-100 text-gray-700";
}

interface InquiryTabsProps {
  readonly dataCount: InquiriesResponse["data_count"];
}

export default function InquiryTabs({ dataCount }: InquiryTabsProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentPhase = searchParams.get("phase") ?? "all";

  const TABS: TabItem[] = [
    { label: "All", value: "all", count: dataCount?.all ?? 0 },
    { label: "Leads", value: "lead", count: dataCount?.lead ?? 0 },
    {
      label: "Registration",
      value: "registration",
      count: dataCount?.registration ?? 0,
    },
    { label: "Deals", value: "deal", count: dataCount?.deal ?? 0 },
  ];

  const createQueryString = useCallback(
    (phase: string) => {
      const newSearchParams = new URLSearchParams(searchParams.toString());

      if (phase && phase !== "all") {
        newSearchParams.set("phase", phase);
      } else {
        newSearchParams.delete("phase");
      }

      // Reset to page 1 when tab changes
      newSearchParams.set("page", "1");

      return newSearchParams.toString();
    },
    [searchParams]
  );

  const handleTabChange = (value: string) => {
    const queryString = createQueryString(value);
    router.push(`${pathname}?${queryString}`);
  };

  return (
    <Tabs
      value={currentPhase}
      onValueChange={handleTabChange}
      className="w-full gap-4"
    >
      <TabsList className="h-auto p-1 flex-wrap justify-start">
        {TABS?.map((tab) => (
          <TabsTrigger
            key={tab?.value}
            value={tab?.value}
            className="data-[state=active]:shadow-none text-inherit data-[state=active]:text-foreground flex-0 cursor-pointer"
          >
            <span className="font-medium">{tab?.label}</span>
            {tab?.count !== undefined && (
              <span
                className={`rounded px-1.5 py-0.5 text-xs font-medium ${getCountBadgeColor(
                  tab?.value
                )}`}
              >
                {tab?.count}
              </span>
            )}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
