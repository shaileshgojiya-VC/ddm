import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Briefcase, ClipboardCheck, Mail } from "lucide-react";

interface PhaseBadgeProps {
  readonly phase: string;
  readonly className?: string;
}

export default function PhaseBadge({ phase, className }: PhaseBadgeProps) {
  const styles = {
    lead: "bg-blue-100 text-blue-700 hover:bg-blue-100",
    deal: "bg-green-100 text-green-700 hover:bg-green-100",
    registration: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  };

  const icons = {
    lead: <Mail className="size-3.5 shrink-0" />,
    deal: <Briefcase className="size-3.5 shrink-0" />,
    registration: <ClipboardCheck className="size-3.5 shrink-0" />,
  };

  return (
    <Badge
      className={cn(
        "font-normal gap-1.5 w-fit capitalize",
        styles[phase as keyof typeof styles] ||
          "bg-gray-100 text-gray-800 hover:bg-gray-100",
        className
      )}
    >
      {icons[phase as keyof typeof icons] || (
        <Mail className="size-3.5 shrink-0" />
      )}
      {phase || "-"}
    </Badge>
  );
}
