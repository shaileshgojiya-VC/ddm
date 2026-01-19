"use client";

import { useState } from "react";
import { UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import InviteUserDialog from "./invite-user-dialog";

export default function InviteUserButton() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsDialogOpen(true)}>
        <UserPlus className="size-4" />
        Invite User
      </Button>
      <InviteUserDialog open={isDialogOpen} onOpenChange={setIsDialogOpen} />
    </>
  );
}
