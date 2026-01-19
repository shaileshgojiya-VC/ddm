import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface PriorityBadgeProps {
  readonly priority: string;
  readonly className?: string;
}
export default function PriorityBadge({
  priority,
  className,
}: PriorityBadgeProps) {
  const styles = {
    urgent: "bg-red-700/10 text-red-700 hover:bg-red-700/10",
    high: "bg-amber-700/10 text-amber-700 hover:bg-amber-700/10",
    medium: "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
    low: "bg-green-700/10 text-green-700 hover:bg-green-700/10",
  };

  return (
    <Badge
      className={cn(
        "font-normal capitalize",
        styles[priority as keyof typeof styles] || styles.medium,
        className
      )}
    >
      {priority || "-"}
    </Badge>
  );
}
