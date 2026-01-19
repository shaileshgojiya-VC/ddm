"use client";

import { Loader2, User, Users, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

interface NewChatDialogProps {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
}

interface UserOption {
  id: string;
  name: string;
  email: string;
}

// Mock user list - in production, this would come from an API
const MOCK_USERS: UserOption[] = [
  { id: "1", name: "Mike Chen", email: "mike.chen@danadairy.com" },
  { id: "2", name: "Sarah Johnson", email: "sarah.johnson@danadairy.com" },
  { id: "3", name: "John Doe", email: "john.doe@danadairy.com" },
  { id: "4", name: "Emily Davis", email: "emily.davis@danadairy.com" },
  { id: "5", name: "Robert Wilson", email: "robert.wilson@danadairy.com" },
  { id: "6", name: "Lisa Anderson", email: "lisa.anderson@danadairy.com" },
];

const getInitials = (name: string): string => {
  return name
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase())
    .join("")
    .slice(0, 2);
};

export default function NewChatDialog({
  open,
  onOpenChange,
}: NewChatDialogProps) {
  const router = useRouter();
  const [chatType, setChatType] = useState<"team" | "individual">("individual");
  const [selectedUsers, setSelectedUsers] = useState<UserOption[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [chatTitle, setChatTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const filteredUsers = MOCK_USERS.filter(
    (user) =>
      user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleUserToggle = (user: UserOption) => {
    if (chatType === "individual") {
      // Single select for individual chat
      setSelectedUsers([user]);
    } else {
      // Multi-select for team chat
      setSelectedUsers((prev) => {
        const isSelected = prev.some((u) => u.id === user.id);
        if (isSelected) {
          return prev.filter((u) => u.id !== user.id);
        }
        return [...prev, user];
      });
    }
  };

  const handleRemoveUser = (userId: string) => {
    setSelectedUsers((prev) => prev.filter((u) => u.id !== userId));
  };

  const handleCreate = async () => {
    if (selectedUsers.length === 0) {
      toast.error("Please select at least one participant");
      return;
    }

    setIsCreating(true);

    try {
      // Generate unique chat ID
      const chatId = `chat-${Date.now()}`;

      // Reset form
      setSelectedUsers([]);
      setChatTitle("");
      setSearchQuery("");
      onOpenChange(false);

      // Navigate to the new chat
      router.push(`/messages/${chatId}`);
      toast.success("Chat created successfully");
    } catch (error) {
      toast.error("Failed to create chat");
      console.error("Error creating chat:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setSelectedUsers([]);
      setChatTitle("");
      setSearchQuery("");
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>New Chat</DialogTitle>
          <DialogDescription>
            Create a new team or individual conversation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Chat Type Selection */}
          <div className="space-y-2">
            <Label>Chat Type</Label>
            <Tabs
              value={chatType}
              onValueChange={(value) => {
                setChatType(value as "team" | "individual");
                // Reset selection when switching types
                if (value === "individual" && selectedUsers.length > 1) {
                  setSelectedUsers([selectedUsers[0]]);
                }
              }}
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="individual">
                  <User className="size-4 mr-2" />
                  Individual
                </TabsTrigger>
                <TabsTrigger value="team">
                  <Users className="size-4 mr-2" />
                  Team
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          {/* Chat Title (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="chat-title">
              Chat Title{" "}
              <span className="text-muted-foreground">(Optional)</span>
            </Label>
            <Input
              id="chat-title"
              placeholder={
                chatType === "individual"
                  ? "Leave empty to use participant name"
                  : "Leave empty to auto-generate"
              }
              value={chatTitle}
              onChange={(e) => setChatTitle(e.target.value)}
              disabled={isCreating}
            />
          </div>

          {/* Participant Selection */}
          <div className="space-y-2">
            <Label>
              Select{" "}
              {chatType === "individual" ? "Participant" : "Participants"}
            </Label>
            <Command className="rounded-lg border">
              <CommandInput
                placeholder={`Search ${
                  chatType === "individual" ? "user" : "users"
                }...`}
                value={searchQuery}
                onValueChange={setSearchQuery}
                disabled={isCreating}
              />
              <CommandList>
                <CommandEmpty>No users found.</CommandEmpty>
                <CommandGroup>
                  {filteredUsers.map((user) => {
                    const isSelected = selectedUsers.some(
                      (u) => u.id === user.id
                    );
                    return (
                      <CommandItem
                        key={user.id}
                        onSelect={() => handleUserToggle(user)}
                        className={cn(
                          "cursor-pointer",
                          isSelected && "bg-accent"
                        )}
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <Avatar className="size-8 bg-muted">
                            <AvatarFallback className="bg-muted text-foreground text-xs">
                              {getInitials(user.name)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{user.name}</p>
                            <p className="text-sm text-muted-foreground truncate">
                              {user.email}
                            </p>
                          </div>
                          {isSelected && (
                            <div className="size-4 rounded-full bg-primary flex items-center justify-center">
                              <div className="size-2 rounded-full bg-primary-foreground" />
                            </div>
                          )}
                        </div>
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              </CommandList>
            </Command>
          </div>

          {/* Selected Users Display */}
          {selectedUsers.length > 0 && (
            <div className="space-y-2">
              <Label>
                Selected{" "}
                {chatType === "individual" ? "Participant" : "Participants"}
              </Label>
              <div className="flex flex-wrap gap-2 p-3 rounded-lg border bg-muted/50">
                {selectedUsers.map((user) => (
                  <Badge
                    key={user.id}
                    variant="secondary"
                    className="flex items-center gap-2 pr-1"
                  >
                    <Avatar className="size-5 bg-background">
                      <AvatarFallback className="bg-background text-foreground text-xs">
                        {getInitials(user.name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-xs">{user.name}</span>
                    {chatType === "team" && (
                      <button
                        type="button"
                        onClick={() => handleRemoveUser(user.id)}
                        className="ml-1 rounded-full hover:bg-background/50 p-0.5"
                        disabled={isCreating}
                      >
                        <X className="size-3" />
                      </button>
                    )}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleCreate}
              disabled={isCreating || selectedUsers.length === 0}
            >
              {isCreating && <Loader2 className="size-4 mr-2 animate-spin" />}
              {isCreating ? "Creating..." : "Create Chat"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
