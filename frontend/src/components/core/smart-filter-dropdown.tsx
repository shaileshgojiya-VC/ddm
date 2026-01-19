"use client";

import { useMemo } from "react";
import type { FilterConfig, SmartFilterDropdownProps } from "@/types/filters";

import SimpleSelectFilter from "./simple-select-filter";
import VirtualizedFilterDropdown from "./virtualized-filter-dropdown";

function getTotalOptionCount(config: FilterConfig): number {
  if (config.grouped) {
    return (
      config.groups?.reduce((sum, group) => sum + group.items.length, 0) ?? 0
    );
  }
  return config.options?.length ?? 0;
}

export default function SmartFilterDropdown(
  props: Readonly<SmartFilterDropdownProps>
) {
  const totalOptions = useMemo(
    () => getTotalOptionCount(props.config),
    [props.config]
  );

  if (totalOptions <= 15) {
    return <SimpleSelectFilter {...props} />;
  }

  return <VirtualizedFilterDropdown {...props} />;
}
