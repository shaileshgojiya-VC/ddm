"use client";

import { Bell } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";

interface Notification {
  id: string;
  title: string;
  description: string;
  isRead: boolean;
  createdAt: string;
}

// Mock notifications data
const mockNotifications: Notification[] = [
  {
    id: "1",
    title: "New Inquiry Received",
    description: "Al Majd Group - Full Cream Milk Powder",
    isRead: false,
    createdAt: "2024-01-06T10:30:00Z",
  },
  {
    id: "2",
    title: "Quote Approved",
    description: "Qatar Food Co approved your quotation",
    isRead: false,
    createdAt: "2024-01-06T09:15:00Z",
  },
  {
    id: "3",
    title: "Team Message",
    description: "Admin: Priority inquiry assigned to you",
    isRead: false,
    createdAt: "2024-01-06T08:45:00Z",
  },
];

export function Notifications() {
  const [notifications] = useState<Notification[]>(mockNotifications);
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white">
              {unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <div className="flex items-center justify-between px-4 py-3">
          <h3 className="font-semibold text-base">Notifications</h3>
        </div>
        <Separator />
        <div className="max-h-[300px] overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Bell className="h-12 w-12 text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">
                No notifications yet
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notification) => (
                <button
                  key={notification.id}
                  className="w-full text-left px-4 py-3 hover:bg-accent transition-colors"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-semibold leading-none">
                      {notification.title}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {notification.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
