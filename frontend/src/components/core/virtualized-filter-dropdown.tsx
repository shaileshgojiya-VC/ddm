"use client";
import {
  FilterConfig,
  FilterRow,
  SmartFilterDropdownProps,
} from "@/types/filters";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

function buildRows(config: FilterConfig): FilterRow[] {
  if (!config.grouped) {
    return (
      config.options?.map((opt) => ({
        type: "item" as const,
        label: opt.label,
        value: String(opt.value),
      })) ?? []
    );
  }

  return (
    config.groups
      ?.slice()
      .sort((a, b) => a.order_sequence - b.order_sequence)
      .flatMap((group) => [
        { type: "group" as const, label: group.group_label },
        ...group.items.map((item) => ({
          type: "item" as const,
          label: item.label,
          value: String(item.value),
        })),
      ]) ?? []
  );
}

export default function VirtualizedFilterDropdown({
  config,
  currentValue,
  onFilterChange,
  disabled,
  triggerClassName,
  align = "start",
}: Readonly<SmartFilterDropdownProps>) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const parentRef = useRef<HTMLDivElement>(null);

  const rows = useMemo(() => buildRows(config), [config]);

  /* 🔥 FIX: show all options initially */
  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;

    const lower = search.toLowerCase();
    const result: FilterRow[] = [];
    let activeGroup: FilterRow | null = null;
    let groupMatched = false;

    for (const row of rows) {
      if (row.type === "group") {
        activeGroup = row;
        groupMatched = false;
      } else if (row.label.toLowerCase().includes(lower)) {
        if (activeGroup && !groupMatched) {
          result.push(activeGroup);
          groupMatched = true;
        }
        result.push(row);
      }
    }

    return result;
  }, [rows, search]);

  const selectedLabel = useMemo(() => {
    const found = rows.find(
      (r) => r.type === "item" && r.value === currentValue
    );
    return found?.label ?? config.label;
  }, [rows, currentValue, config.label]);

  const virtualizer = useVirtualizer({
    count: filteredRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: (i) => (filteredRows[i]?.type === "group" ? 40 : 36),
    overscan: 6,
    enabled: open,
  });

  useEffect(() => {
    if (open) {
      requestAnimationFrame(() => {
        virtualizer.measure();
        virtualizer.scrollToIndex(0);
      });
    }
  }, [open, virtualizer]);

  const handleSelect = (value: string) => {
    const filterValue = value === "all" ? "" : value;
    onFilterChange(config.key, filterValue);
    setOpen(false);
    setSearch("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn("w-full sm:w-auto justify-between", triggerClassName)}
        >
          <span className="truncate"> {selectedLabel}</span>

          <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent className="p-0 w-80 max-w-[80vw]" align={align}>
        <Command shouldFilter={false}>
          <CommandInput
            placeholder={`Search ${config.label.toLowerCase()}...`}
            value={search}
            onValueChange={setSearch}
            autoFocus
          />

          {filteredRows.length === 0 && (
            <CommandEmpty>No results found.</CommandEmpty>
          )}

          <CommandList ref={parentRef} className="h-64 overflow-auto">
            <div
              style={{
                height: virtualizer.getTotalSize(),
                position: "relative",
              }}
            >
              {virtualizer.getVirtualItems().map((v) => {
                const row = filteredRows[v.index];

                if (row.type === "group") {
                  return (
                    <div
                      key={`group-${v.index}`}
                      className="px-3 py-2 text-sm font-semibold text-muted-foreground"
                      style={{
                        position: "absolute",
                        top: 0,
                        transform: `translateY(${v.start}px)`,
                        width: "100%",
                      }}
                    >
                      {row.label}
                    </div>
                  );
                }

                return (
                  <CommandItem
                    key={row.value}
                    value={row.value}
                    onSelect={() => handleSelect(row.value)}
                    style={{
                      position: "absolute",
                      top: 0,
                      transform: `translateY(${v.start}px)`,
                      width: "100%",
                    }}
                  >
                    <Check
                      className={cn(
                        "h-4 w-4",
                        row.value === currentValue ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span className="truncate">{row.label}</span>
                  </CommandItem>
                );
              })}
            </div>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
