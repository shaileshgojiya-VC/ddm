"use client";

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { useCallback, useState, useTransition, useEffect } from "react";
import { Search, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useDebounce } from "@/hooks/use-debounce";
import { cn } from "@/lib/utils";

interface SearchInputProps {
  queryParam?: string;
  placeholder?: string;
  debounceDelay?: number;
  resetPagination?: boolean;
  paginationParam?: string;
  className?: string;
  inputClassName?: string;
  showClearButton?: boolean;
  onSearch?: (value: string) => void;
}

export function SearchInput({
  queryParam = "search",
  placeholder = "Search...",
  debounceDelay = 1000,
  resetPagination = true,
  paginationParam = "page",
  className,
  inputClassName,
  showClearButton = true,
  onSearch,
}: Readonly<SearchInputProps>) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const currentSearch = searchParams.get(queryParam) ?? "";
  const [searchValue, setSearchValue] = useState(currentSearch);
  const debouncedSearchValue = useDebounce(searchValue, debounceDelay);

  const createQueryString = useCallback(
    (value: string) => {
      const newSearchParams = new URLSearchParams(searchParams.toString());

      if (value) {
        newSearchParams.set(queryParam, value);
      } else {
        newSearchParams.delete(queryParam);
      }

      if (resetPagination) {
        newSearchParams.set(paginationParam, "1");
      }

      return newSearchParams.toString();
    },
    [searchParams, queryParam, resetPagination, paginationParam]
  );

  useEffect(() => {
    if (debouncedSearchValue === currentSearch) {
      return;
    }

    startTransition(() => {
      const queryString = createQueryString(debouncedSearchValue);
      router.push(`${pathname}?${queryString}`);
      onSearch?.(debouncedSearchValue);
    });
  }, [
    debouncedSearchValue,
    currentSearch,
    createQueryString,
    router,
    pathname,
    onSearch,
  ]);

  useEffect(() => {
    setSearchValue(currentSearch);
  }, [currentSearch]);

  const handleClear = () => {
    setSearchValue("");
  };

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="text"
        placeholder={placeholder}
        className={cn(
          "pl-10",
          showClearButton && searchValue && "pr-10",
          inputClassName
        )}
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        disabled={isPending}
      />
      {showClearButton && searchValue && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1/2 size-7 -translate-y-1/2"
          onClick={handleClear}
          disabled={isPending}
        >
          <X className="size-4" />
          <span className="sr-only">Clear search</span>
        </Button>
      )}
    </div>
  );
}
