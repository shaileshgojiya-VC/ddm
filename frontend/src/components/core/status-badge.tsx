import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  readonly status: string;
  readonly className?: string;
}
export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const styles = {
    "Pending Response": "bg-amber-700/10 text-amber-700 hover:bg-amber-700/10",
    "On Track": "bg-green-700/10 text-green-700 hover:bg-green-700/10",
    Delayed: "bg-red-700/10 text-red-700 hover:bg-red-700/10",
    "Awaiting Client": "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
    "Follow-up Required":
      "bg-orange-700/10 text-orange-700 hover:bg-orange-700/10",
  };

  return (
    <Badge
      className={cn(
        "font-normal capitalize",
        styles[status as keyof typeof styles] ||
          "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
        className
      )}
    >
      {status || "-"}
    </Badge>
  );
}
