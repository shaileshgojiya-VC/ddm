"use client";

import { useState, useEffect } from "react";
import { Calendar as CalendarIcon } from "lucide-react";
import { type DateRange } from "react-day-picker";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";

interface DateRangePickerProps {
  placeholder?: string;
  className?: string;
  onDateChange?: (dateRange: DateRange | undefined) => void;
  startDateParam?: string;
  endDateParam?: string;
}

export default function DateRangePicker({
  placeholder = "Date Range",
  className,
  onDateChange,
  startDateParam = "start_date",
  endDateParam = "end_date",
}: Readonly<DateRangePickerProps>) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [date, setDate] = useState<DateRange | undefined>(() => {
    const startDate = searchParams.get(startDateParam);
    const endDate = searchParams.get(endDateParam);

    if (startDate && endDate) {
      return {
        from: new Date(startDate),
        to: new Date(endDate),
      };
    }
    return undefined;
  });

  // Derive date from URL params - this will update when params change
  const startDateParamValue = searchParams.get(startDateParam);
  const endDateParamValue = searchParams.get(endDateParam);

  // Update date state when URL params change
  useEffect(() => {
    if (startDateParamValue && endDateParamValue) {
      const newDate = {
        from: new Date(startDateParamValue),
        to: new Date(endDateParamValue),
      };

      // Only update if the date actually changed
      const currentFrom = date?.from?.toISOString().split("T")[0];
      const currentTo = date?.to?.toISOString().split("T")[0];
      const newFrom = newDate.from.toISOString().split("T")[0];
      const newTo = newDate.to.toISOString().split("T")[0];

      if (currentFrom !== newFrom || currentTo !== newTo) {
        setDate(newDate);
      }
    } else {
      // Clear date when params are removed
      setDate(undefined);
    }
    // We intentionally exclude 'date' from dependencies to avoid infinite loops
    // The effect should only run when URL params change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startDateParamValue, endDateParamValue]);

  const handleDateSelect = (selectedDate: DateRange | undefined) => {
    setDate(selectedDate);

    if (onDateChange) {
      onDateChange(selectedDate);
      return;
    }

    if (selectedDate?.from && selectedDate?.to) {
      const newSearchParams = new URLSearchParams(searchParams.toString());
      newSearchParams.set(
        startDateParam,
        selectedDate.from.toISOString().split("T")[0]
      );
      newSearchParams.set(
        endDateParam,
        selectedDate.to.toISOString().split("T")[0]
      );
      newSearchParams.set("page", "1");

      router.push(`${pathname}?${newSearchParams.toString()}`);
    }
  };

  const formatDateDisplay = (date: Date) => {
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getDateRangeDisplay = () => {
    if (!date?.from) {
      return <span>{placeholder}</span>;
    }

    if (date.to) {
      const fromFormatted = date.from.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
      const toFormatted = formatDateDisplay(date.to);
      return (
        <>
          {fromFormatted} - {toFormatted}
        </>
      );
    }

    return formatDateDisplay(date.from);
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "min-w-[140px] justify-start text-left font-normal w-full sm:w-auto",
            !date && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {getDateRangeDisplay()}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="range"
          defaultMonth={date?.from}
          selected={date}
          onSelect={handleDateSelect}
          numberOfMonths={2}
        />
      </PopoverContent>
    </Popover>
  );
}
