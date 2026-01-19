"use client";

import { Users } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface Member {
  id: string;
  name: string;
  email?: string;
}

interface MembersDialogProps {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
  readonly members: Member[];
}

export default function MembersDialog({
  open,
  onOpenChange,
  members,
}: MembersDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="size-5" />
            Members
          </DialogTitle>
        </DialogHeader>
        <div className="max-h-[400px] overflow-y-auto pr-2">
          <div className="space-y-2">
            {members.map((member) => {
              const initials = member.name
                .split(" ")
                .map((n) => n.charAt(0))
                .join("")
                .toUpperCase()
                .slice(0, 2);

              return (
                <div
                  key={member.id}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <Avatar className="size-10 bg-muted">
                    <AvatarFallback className="bg-muted text-foreground font-medium">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{member.name}</p>
                    {member.email && (
                      <p className="text-sm text-muted-foreground truncate">
                        {member.email}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

