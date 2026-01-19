import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface InfoItemCardProps {
  readonly icon: LucideIcon;
  readonly label: string;
  readonly value: string | number;
  readonly className?: string;
}

export default function InfoItemCard({
  icon: Icon,
  label,
  value,
  className,
}: InfoItemCardProps) {
  return (
    <Card className={cn("py-0", className)}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <Icon className="size-5 text-muted-foreground shrink-0" />
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-sm font-medium text-foreground wrap-break-word">
              {value}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
