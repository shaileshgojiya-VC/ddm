"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CheckCircle } from "lucide-react";
import { Separator } from "@/components/ui/separator";

export default function InquiryConnectorTab() {
  const handleConfigureRules = () => {
    console.log("Configure rules...");
    // TODO: Navigate to rules configuration
  };

  const handleTestConnection = () => {
    console.log("Testing connection...");
    // TODO: Call API to test connection
  };

  const handleDisconnect = () => {
    console.log("Disconnecting...");
    // TODO: Call API to disconnect
  };

  return (
    <Card>
      <CardContent className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">Inquiry Email Connector</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Connect Microsoft email account for inquiry processing
            </p>
          </div>
          <Button>Connect Account</Button>
        </div>

        {/* Connected Email Account */}
        <div className="rounded-lg p-4 border">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center size-10 rounded-lg bg-sky-500">
                <svg
                  viewBox="0 0 23 23"
                  className="size-5 text-white fill-current"
                >
                  <path d="M0 0h11v11H0zM12 0h11v11H12zM0 12h11v11H0zM12 12h11v11H12z" />
                </svg>
              </div>
              <div>
                <p className="font-medium">inquiry-ai@danadairy.com</p>
                <p className="text-sm text-muted-foreground">
                  Inquiry processing inbox
                </p>
              </div>
            </div>
            <Badge className="bg-green-600 hover:bg-green-600">
              <CheckCircle className="size-4" />
              Connected
            </Badge>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="p-2 rounded bg-muted">
              <p className="text-xs text-muted-foreground mb-1">
                Inquiries Processed
              </p>
              <p className="text-sm font-semibold">89 today</p>
            </div>
            <div className="p-2 rounded bg-muted">
              <p className="text-xs text-muted-foreground mb-1">
                Auto-classified
              </p>
              <p className="text-sm font-semibold">76 classified</p>
            </div>
            <div className="p-2 rounded bg-muted">
              <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
              <p className="text-sm font-semibold text-green-600">96.8%</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <Button onClick={handleConfigureRules}>Configure Rules</Button>
            <Button variant="outline" onClick={handleTestConnection}>
              Test Connection
            </Button>
            <Button variant="destructive" onClick={handleDisconnect}>
              Disconnect
            </Button>
          </div>
        </div>

        <Separator />

        {/* Processing Settings */}
        <div className="space-y-4">
          <h4 className="font-semibold">Processing Settings</h4>

          <div className="flex items-center justify-between py-3 px-4 border rounded-lg">
            <div>
              <p className="font-medium">Auto-classification</p>
              <p className="text-sm text-muted-foreground">
                Automatically classify incoming inquiries
              </p>
            </div>
            <Badge className="bg-green-600 hover:bg-green-600">Enabled</Badge>
          </div>

          <div className="flex items-center justify-between py-3 px-4 border rounded-lg">
            <div>
              <p className="font-medium">Auto-response</p>
              <p className="text-sm text-muted-foreground">
                Send automated acknowledgment emails
              </p>
            </div>
            <Badge className="bg-green-600 hover:bg-green-600">Enabled</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
