"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle, Plus, X } from "lucide-react";
import { useFieldArray, useForm } from "react-hook-form";
import * as z from "zod";

const oneDriveFormSchema = z.object({
  email: z.string().email("Invalid email address"),
  folderPaths: z
    .array(
      z.object({
        path: z.string().min(1, "Folder path is required"),
      })
    )
    .min(1, "At least one folder path is required"),
  accessType: z.string().min(1, "Access type is required"),
  syncFrequency: z.string().min(1, "Sync frequency is required"),
});

type OneDriveFormValues = z.infer<typeof oneDriveFormSchema>;

const connectedFolders = [
  { path: "/Shared/Dana Dairy/Inquiries", status: "active" },
  { path: "/Shared/Dana Dairy/Documents", status: "active" },
];

export default function OneDriveTab() {
  const form = useForm<OneDriveFormValues>({
    resolver: zodResolver(oneDriveFormSchema),
    defaultValues: {
      email: "documents@danadairy.com",
      folderPaths: [{ path: "/Shared/Dana Dairy/Inquiries" }],
      accessType: "read-write",
      syncFrequency: "every-hour",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "folderPaths",
  });

  const onSubmit = (data: OneDriveFormValues) => {
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

  const handleAddFolder = () => {
    append({ path: "" });
  };

  return (
    <Card>
      <CardContent className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">OneDrive Folder Access</h3>
            </div>
            <p className="text-sm text-muted-foreground">
              Connect to specific OneDrive folders for document management
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
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>OneDrive Account Email</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="your-email@company.com"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Folder Paths with Add More */}
              <div className="space-y-3">
                <FormLabel>Folder Path</FormLabel>
                {fields.map((field, index) => (
                  <div key={field.id} className="flex items-start gap-2">
                    <FormField
                      control={form.control}
                      name={`folderPaths.${index}.path`}
                      render={({ field }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Input
                              placeholder="/Shared/Folder/Path"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    {fields.length > 1 && (
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => remove(index)}
                        className="shrink-0"
                      >
                        <X className="size-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleAddFolder}
                  className="gap-2"
                >
                  <Plus className="size-4" />
                  Add More Folder
                </Button>
                <p className="text-sm text-muted-foreground">
                  Specify the exact folder path you want to access
                </p>
              </div>

              <FormField
                control={form.control}
                name="accessType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Access Type</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select access type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="read-only">Read Only</SelectItem>
                        <SelectItem value="read-write">Read & Write</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="syncFrequency"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Sync Frequency</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select sync frequency" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="every-15min">
                          Every 15 minutes
                        </SelectItem>
                        <SelectItem value="every-30min">
                          Every 30 minutes
                        </SelectItem>
                        <SelectItem value="every-hour">Every Hour</SelectItem>
                        <SelectItem value="every-6hours">
                          Every 6 hours
                        </SelectItem>
                        <SelectItem value="daily">Daily</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3">
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

        {/* Connected Folders */}
        <Card className="p-4 bg-muted border-none">
          <CardHeader className="px-0 gap-0">
            <CardTitle>Connected Folders:</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {connectedFolders?.map((folder) => (
              <div
                key={folder?.path}
                className="flex items-center justify-between py-2 px-4 bg-background rounded"
              >
                <p className="text-sm font-medium">{folder.path}</p>
                <Badge className="bg-green-600 hover:bg-green-600">
                  Active
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </CardContent>
    </Card>
  );
}
