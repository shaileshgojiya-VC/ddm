import { LucideIcon, Plug, Users } from "lucide-react";

import PageHeading from "@/components/core/page-heading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface StatCard {
  title: string;
  value: string | number;
  subtitle: string;
  icon: LucideIcon;
}

export default function DashboardPage() {
  // Mock data - replace with actual data from API
  const statsCards: StatCard[] = [
    {
      title: "Total Users",
      value: 6,
      subtitle: "6 active",
      icon: Users,
    },
    {
      title: "Connected Integrations",
      value: "3/3",
      subtitle: "All healthy",
      icon: Plug,
    },
  ];

  const usersByRole = [
    { role: "Admin", activeUsers: 1, count: 1 },
    { role: "Management", activeUsers: 2, count: 2 },
    { role: "Sales", activeUsers: 3, count: 3 },
  ];

  return (
    <div className="space-y-6">
      <PageHeading
        title="Admin Dashboard"
        description="System overview and configuration status"
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        {statsCards.map((card) => (
          <Card key={card.title}>
            <CardContent className="flex items-start justify-between pt-0">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">{card.title}</p>
                <p className="text-2xl font-bold">{card.value}</p>
                <p className="text-sm text-green-600">{card.subtitle}</p>
              </div>
              <div className="rounded-lg bg-primary/10 p-3">
                <card.icon className="size-5 text-primary" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* User Overview Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <CardTitle className="text-2xl">User Overview</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">System users by role</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {usersByRole.map((item) => (
            <div
              key={item.role}
              className="flex items-center justify-between rounded-lg bg-slate-100 p-4"
            >
              <div>
                <p className="font-medium">{item.role}</p>
                <p className="text-sm text-muted-foreground">
                  {item.activeUsers} active users
                </p>
              </div>
              <p className="text-2xl font-bold">{item.count}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
