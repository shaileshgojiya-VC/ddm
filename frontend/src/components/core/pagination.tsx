"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useTransition } from "react";
import { ChevronLeft, ChevronRight, ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Pagination as PaginationType } from "@/utils/fetcher/types";

interface PaginationProps {
  readonly pagination?: PaginationType;
  readonly limitOptions?: number[];
}

export default function Pagination({
  pagination,
  limitOptions = [5, 10, 15, 20, 25, 50],
}: PaginationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const createQueryString = useCallback(
    (newPage: number, newLimit?: number) => {
      const newSearchParams = new URLSearchParams(searchParams.toString());
      newSearchParams.set("page", newPage.toString());
      if (newLimit) {
        newSearchParams.set("limit", newLimit.toString());
      }
      return newSearchParams.toString();
    },
    [searchParams]
  );

  if (!pagination) {
    return null;
  }

  const { page, pages, total, limit } = pagination;

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > pages) return;

    startTransition(() => {
      const queryString = createQueryString(newPage);
      router.push(`${pathname}?${queryString}`);
    });
  };

  const handleLimitChange = (newLimit: number) => {
    startTransition(() => {
      const queryString = createQueryString(1, newLimit);
      router.push(`${pathname}?${queryString}`);
    });
  };

  const startItem = (page - 1) * limit + 1;
  const endItem = Math.min(page * limit, total);

  if (total === 0) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Rows per page</span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 gap-1"
              disabled={isPending}
            >
              {limit}
              <ChevronDown className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            {limitOptions?.map((option) => (
              <DropdownMenuItem
                key={option}
                onClick={() => handleLimitChange(option)}
              >
                {option}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-sm text-muted-foreground">
          {startItem}-{endItem} of {total}
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => handlePageChange(page - 1)}
            disabled={page === 1 || isPending}
          >
            <ChevronLeft className="size-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={() => handlePageChange(page + 1)}
            disabled={page === pages || isPending}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
