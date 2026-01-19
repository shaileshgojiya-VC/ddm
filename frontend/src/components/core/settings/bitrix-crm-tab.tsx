"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle } from "lucide-react";
import { useForm } from "react-hook-form";
import * as z from "zod";

const bitrixFormSchema = z.object({
  domain: z.string().min(1, "Domain is required"),
  webhookUrl: z.string().url("Invalid webhook URL"),
  userId: z.string().min(1, "User ID is required"),
});

type BitrixFormValues = z.infer<typeof bitrixFormSchema>;

export default function BitrixCRMTab() {
  const form = useForm<BitrixFormValues>({
    resolver: zodResolver(bitrixFormSchema),
    defaultValues: {
      domain: "danadairy.bitrix24.com",
      webhookUrl: "",
      userId: "1",
    },
  });

  const onSubmit = (data: BitrixFormValues) => {
    console.log("Save Configuration:", data);
    // TODO: Call API to save configuration
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
              <h3 className="text-lg font-semibold">
                Bitrix24 CRM Integration
              </h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Configure API connection to Bitrix24 for deal synchronization
            </p>
          </div>
          <Badge className="bg-green-600 hover:bg-green-600">
            <CheckCircle className="size-4" />
            Connected
          </Badge>
        </div>

        {/* Form */}
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Form Fields */}
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="domain"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bitrix24 Domain</FormLabel>
                    <FormControl>
                      <Input placeholder="yourdomain.bitrix24.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="webhookUrl"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Webhook URL</FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder="••••••••••••••••••••••••••••••••••"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="userId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>User ID</FormLabel>
                    <FormControl>
                      <Input placeholder="1" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Sync Settings */}
            <div className="space-y-4 pt-2">
              <h4 className="font-semibold">Sync Settings</h4>

              <div className="flex items-center justify-between py-3 px-4 border rounded-lg">
                <div>
                  <p className="font-medium">Auto-sync Deals</p>
                  <p className="text-sm text-muted-foreground">
                    Automatically sync inquiries to Bitrix24 deals
                  </p>
                </div>
                <Badge className="bg-green-600 hover:bg-green-600">
                  Enabled
                </Badge>
              </div>

              <div className="flex items-center justify-between py-3 px-4 border rounded-lg">
                <div>
                  <p className="font-medium">Sync Interval</p>
                  <p className="text-sm text-muted-foreground">
                    How often to sync data
                  </p>
                </div>
                <p className="text-sm font-medium text-primary">
                  Every 5 minutes
                </p>
              </div>

              <div className="flex items-center justify-between py-3 px-4 border rounded-lg">
                <div>
                  <p className="font-medium">Last Sync</p>
                  <p className="text-sm text-muted-foreground">
                    Most recent synchronization
                  </p>
                </div>
                <p className="text-sm text-muted-foreground">2 minutes ago</p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <Button type="submit">Save Configuration</Button>
              <Button
                type="button"
                variant="outline"
                onClick={handleTestConnection}
              >
                Test Connection
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={handleDisconnect}
              >
                Disconnect
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
