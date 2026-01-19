"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { signOut } from "next-auth/react";
import { LogOut } from "lucide-react";

export default function LogoutCard({
  title = "You are already logged in",
  description = "If you are already logged in, please log out or open this link in Incognito.",
}: {
  readonly title?: string;
  readonly description?: string;
}) {
  const handleLogout = async () => {
    await signOut({ redirect: true, redirectTo: "/login" });
  };
  return (
    <div className="flex items-center justify-center p-4 min-h-full">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 text-center">
          <div className="rounded-full bg-green-100 p-4">
            <LogOut className="size-12 text-green-600" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">{title}</h1>
            <p className="text-muted-foreground">{description}</p>
          </div>
          <div className="flex gap-3">
            <Button onClick={handleLogout} variant="destructive">
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
