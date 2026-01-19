import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface NoDataFoundProps {
  readonly title: string;
  readonly description?: string;
  readonly icon?: LucideIcon;
}

export default function NoDataFound({
  title,
  description = "",
  icon: Icon,
}: NoDataFoundProps) {
  return (
    <Card className="flex flex-col items-center justify-center py-6">
      {Icon && <Icon className="size-10 text-muted-foreground" />}
      <CardTitle className="text-center text-2xl">{title}</CardTitle>
      {description && (
        <CardDescription className="text-center">{description}</CardDescription>
      )}
    </Card>
  );
}
