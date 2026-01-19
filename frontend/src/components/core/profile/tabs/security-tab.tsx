"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChangePasswordDialog } from "../change-password-dialog";
import { UpdateEmailDialog } from "../update-email-dialog";
import { useSession } from "next-auth/react";

export default function SecurityTab() {
  const { data: session } = useSession();

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
      <CardContent className="space-y-6">
        {/* Password Section */}
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border">
          <div className="space-y-1">
            <p className="font-medium">Password</p>
            <p className="text-sm text-muted-foreground">
              Last changed {securityData.passwordLastChanged}
            </p>
          </div>
          <ChangePasswordDialog />
        </div>

        {/* Email Section */}
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg border">
          <div className="space-y-1">
            <p className="font-medium">Email Address</p>
            <p className="text-sm text-muted-foreground">
              Current: {session?.user?.email}
            </p>
          </div>
          <UpdateEmailDialog currentEmail={session?.user?.email || ""} />
        </div>

        {/* Security Tips */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="font-medium text-blue-900 mb-2">Security Tips:</p>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Use a strong password with mixed case, numbers, and special characters</li>
            <li>Never share your password with anyone</li>
            <li>Change your password regularly (every 3-6 months)</li>
            <li>Keep your email address up to date for account recovery</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
