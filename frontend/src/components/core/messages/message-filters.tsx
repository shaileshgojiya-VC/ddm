"use client";

import { SearchInput } from "@/components/core/search-input";
import { Card, CardContent } from "@/components/ui/card";

export default function MessageFilters() {
  return (
    <Card>
      <CardContent className="pt-0">
        <SearchInput placeholder="Search conversations..." className="w-full" />
      </CardContent>
    </Card>
  );
}
