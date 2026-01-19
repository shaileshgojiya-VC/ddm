import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { getRoleBadgeStyle } from "@/utils/role-styles";
import type { ActiveCounts } from "@/types/user";

interface RoleStatsProps {
  readonly activeCounts: ActiveCounts;
}

// Define role display order
const ROLE_ORDER = ["admin", "management", "sales"];

export default function RoleStats({ activeCounts }: RoleStatsProps) {
  // If no data, return null
  if (Object.keys(activeCounts).length === 0) {
    return null;
  }

  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      {ROLE_ORDER.map((roleKey) => {
        const count = activeCounts[roleKey] ?? 0;
        // Capitalize first letter for label
        const label = roleKey;

        return (
          <Card key={roleKey}>
            <CardContent className="flex items-center justify-between pt-0">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground capitalize">
                  {label} Users
                </p>
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-muted-foreground">{count} active</p>
              </div>
              <Badge className={getRoleBadgeStyle(label)}>{label}</Badge>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
