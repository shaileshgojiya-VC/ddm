import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import Link from "next/link";

export default function SecurityTab() {
  // Static data - will be replaced with API data later
  const securityData = {
    passwordLastChanged: "30 days ago",
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle className="text-2xl font-semibold">Security</CardTitle>
        </div>
        <CardDescription>Manage your account security settings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
          <div className="space-y-1">
            <p className="font-medium">Password</p>
            <p className="text-sm text-muted-foreground">
              Last changed {securityData.passwordLastChanged}
            </p>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/change-password">Change Password</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
