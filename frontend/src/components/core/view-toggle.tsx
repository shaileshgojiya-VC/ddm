"use client";

import { Button } from "@/components/ui/button";
import { LayoutDashboard, List } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useTransition } from "react";

export default function ViewToggle() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const currentView = (searchParams.get("view") as "grid" | "list") || "grid";

  const createQueryString = useCallback(
    (view: "grid" | "list") => {
      const newSearchParams = new URLSearchParams(searchParams.toString());
      newSearchParams.set("view", view);
      return newSearchParams.toString();
    },
    [searchParams]
  );

  const handleViewChange = (view: "grid" | "list") => {
    startTransition(() => {
      const queryString = createQueryString(view);
      router.push(`${pathname}?${queryString}`);
    });
  };

  return (
    <div className="flex items-center gap-2 bg-slate-200 rounded-md p-1">
      <Button
        variant={currentView === "grid" ? "default" : "ghost"}
        onClick={() => handleViewChange("grid")}
        disabled={isPending}
        className="gap-2"
        size="sm"
      >
        <LayoutDashboard />
        Grid
      </Button>
      <Button
        variant={currentView === "list" ? "default" : "ghost"}
        onClick={() => handleViewChange("list")}
        disabled={isPending}
        className="gap-2"
        size="sm"
      >
        <List />
        List
      </Button>
    </div>
  );
}
