"use client";

import { useState } from "react";
import { MoreVertical, Users } from "lucide-react";
import { useRouter } from "next/navigation";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import BackButton from "@/components/core/back-button";
import MembersDialog from "./members-dialog";

interface Member {
  id: string;
  name: string;
  email?: string;
}

interface MessageHeaderProps {
  readonly title: string;
  readonly memberCount?: number;
  readonly members?: string;
  readonly type?: "team" | "individual";
  readonly membersList?: Member[];
}

export default function MessageHeader({
  title,
  memberCount,
  members,
  type = "individual",
  membersList = [],
}: MessageHeaderProps) {
  const router = useRouter();
  const [isMembersDialogOpen, setIsMembersDialogOpen] = useState(false);

  const handleViewMembers = () => {
    setIsMembersDialogOpen(true);
  };

  const handleMuteNotifications = () => {
    // Future: Implement mute notifications API call
    console.log("Mute notifications");
  };

  const handleLeaveChat = () => {
    router.back();
  };

  return (
    <div className="flex items-center justify-between p-4 sticky top-0 z-10">
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <BackButton />
        <Avatar className="size-10 bg-primary/10 shrink-0">
          <AvatarFallback className="bg-primary/10 text-primary">
            {type === "team" ? (
              <Users className="size-5" />
            ) : (
              title.charAt(0).toUpperCase()
            )}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h1 className="font-semibold text-base truncate">{title}</h1>
            {memberCount && (
              <Badge variant="secondary" className="shrink-0">
                {memberCount} members
              </Badge>
            )}
          </div>
          {members && (
            <p className="text-sm text-muted-foreground truncate">{members}</p>
          )}
        </div>
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="shrink-0">
            <MoreVertical className="size-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          {type === "team" && membersList.length > 0 && (
            <DropdownMenuItem onClick={handleViewMembers}>
              View Members
            </DropdownMenuItem>
          )}
          <DropdownMenuItem onClick={handleMuteNotifications}>
            Mute Notifications
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={handleLeaveChat}
            className="text-destructive focus:text-destructive"
          >
            Leave Chat
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <MembersDialog
        open={isMembersDialogOpen}
        onOpenChange={setIsMembersDialogOpen}
        members={membersList}
      />
    </div>
  );
}
