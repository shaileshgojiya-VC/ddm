"use client";

import { useSession } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useTransition } from "react";

import { SearchInput } from "@/components/core/search-input";
import SmartFilterDropdown from "@/components/core/smart-filter-dropdown";
import { Card, CardContent } from "@/components/ui/card";
import { createFilterQueryString } from "@/utils/create-filter-query-string";

export default function UserFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const { data: session } = useSession();

  const currentRole = searchParams.get("role_id") ?? "";

  // Generate role filter config dynamically from session roles
  const roleFilterConfig = useMemo(() => {
    const options = [{ label: "All Roles", value: "" }];
    const isAdmin = session?.role?.name === "Admin";

    if (session?.roles) {
      session.roles.forEach((role) => {
        // Skip Admin role if current user is NOT Admin
        if (!isAdmin && role.name === "Admin") {
          return;
        }
        options.push({
          label: role.name,
          value: role.id,
        });
      });
    }
    return {
      key: "role_id",
      label: "All Roles",
      options,
      minWidth: "min-w-[140px]",
      menuWidth: "w-[140px]",
    };
  }, [session]);

  const handleFilterChange = (filterType: string, value: string) => {
    startTransition(() => {
      const queryString = createFilterQueryString(searchParams, {
        [filterType]: value,
      });
      router.push(`/users?${queryString}`);
    });
  };

  return (
    <Card>
      <CardContent className="flex flex-col sm:flex-row  items-center gap-4 pt-0">
        <SearchInput
          placeholder="Search by name or email..."
          className="flex-1 w-full sm:w-auto"
        />
        <SmartFilterDropdown
          config={roleFilterConfig}
          currentValue={currentRole}
          onFilterChange={handleFilterChange}
          disabled={isPending}
        />
      </CardContent>
    </Card>
  );
}
