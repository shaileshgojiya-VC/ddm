"use client";
import { SmartFilterDropdownProps } from "@/types/filters";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
export default function SimpleSelectFilter({
  config,
  currentValue,
  onFilterChange,
  disabled,
  triggerClassName,
  align = "start",
}: Readonly<SmartFilterDropdownProps>) {
  const handleChange = (value: string) => {
    const filterValue = value === "all" ? "" : value;
    onFilterChange(config.key, filterValue);
  };
  return (
    <Select
      value={currentValue}
      onValueChange={handleChange}
      disabled={disabled}
    >
      <SelectTrigger
        className={cn("w-full sm:w-auto truncate", triggerClassName)}
      >
        <SelectValue placeholder={config.label} />
      </SelectTrigger>

      <SelectContent align={align} className="max-w-80">
        {!config.grouped &&
          config.options?.map((opt) => (
            <SelectItem
              key={opt.value}
              value={String(opt.value) || "all"}
              className="w-full max-w-80 whitespace-normal "
            >
              {opt.label}
            </SelectItem>
          ))}

        {config.grouped &&
          config.groups
            ?.slice()
            .sort((a, b) => a.order_sequence - b.order_sequence)
            .map((group) => (
              <SelectGroup
                key={group.group_key}
                className="border-b border-border pb-2 pt-2 last:border-b-0 last:pt-0"
              >
                <SelectLabel className="font-medium text-black text-base">
                  {group.group_label}
                </SelectLabel>
                {group.items.map((item) => (
                  <SelectItem
                    key={item.value}
                    value={String(item.value) || "all"}
                    className="w-full max-w-80 whitespace-normal pl-6!"
                  >
                    {item.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
      </SelectContent>
    </Select>
  );
}
