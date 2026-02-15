import { useState } from "react";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import type { DateRange } from "@/types/trading";

interface DateRangePickerProps {
  dateRange?: DateRange;
  onDateRangeChange: (range: DateRange | undefined) => void;
}

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false);

  // react-day-picker v8 uses { from, to } for range selection
  const selected = dateRange
    ? { from: dateRange.from, to: dateRange.to }
    : undefined;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-[260px] justify-start text-left font-normal",
            !dateRange && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {dateRange ? (
            <>
              {format(dateRange.from, "MMM d, yyyy")} –{" "}
              {format(dateRange.to, "MMM d, yyyy")}
            </>
          ) : (
            <span>Pick a date range</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="end">
        <Calendar
          mode="range"
          defaultMonth={dateRange?.from}
          selected={selected}
          onSelect={(range: any) => {
            if (range?.from && range?.to) {
              // Set "to" date to end of day for inclusive filtering
              const toEnd = new Date(range.to);
              toEnd.setHours(23, 59, 59, 999);
              onDateRangeChange({ from: range.from, to: toEnd });
            } else if (range?.from) {
              // User has only picked the start date so far
              onDateRangeChange({ from: range.from, to: range.from });
            }
          }}
          numberOfMonths={2}
          disabled={{ after: new Date() }}
        />
        <div className="flex items-center justify-between p-3 border-t">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              onDateRangeChange(undefined);
              setOpen(false);
            }}
          >
            Clear
          </Button>
          <Button
            size="sm"
            onClick={() => setOpen(false)}
            disabled={!dateRange}
          >
            Apply
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
