"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import NewChatDialog from "@/components/core/messages/new-chat-dialog";

export default function NewChatButton() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsDialogOpen(true)}>
        <Plus className="size-4" />
        New Chat
      </Button>
      <NewChatDialog open={isDialogOpen} onOpenChange={setIsDialogOpen} />
    </>
  );
}
