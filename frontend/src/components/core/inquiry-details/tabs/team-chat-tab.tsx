"use client";

import { useState } from "react";
import { Send } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import NoDataFound from "@/components/core/no-data-found";

interface ChatMessage {
  id: string;
  author: string;
  authorInitials: string;
  message: string;
  timestamp: string;
}

// Mock data - replace with actual API data
const initialMessages: ChatMessage[] = [
  {
    id: "1",
    author: "Mike Chen",
    authorInitials: "MC",
    message:
      "Customer is asking for better payment terms. Suggesting LC 60 days instead of LC at sight.",
    timestamp: "2 hours ago",
  },
  {
    id: "2",
    author: "Sarah Johnson",
    authorInitials: "SJ",
    message:
      "Approved. Let's proceed with the updated terms. Please prepare the revised quote.",
    timestamp: "1 hour ago",
  },
];

export default function TeamChatTab() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [newMessage, setNewMessage] = useState("");

  const handleSendMessage = () => {
    if (!newMessage.trim()) return;

    // TODO: Replace with actual API call
    const message: ChatMessage = {
      id: Date.now().toString(),
      author: "Current User", // Replace with actual user from session
      authorInitials: "CU",
      message: newMessage,
      timestamp: "Just now",
    };

    setMessages([...messages, message]);
    setNewMessage("");
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="flex flex-col h-full">
      <CardHeader>
        <CardTitle>Team Discussion</CardTitle>
        <p className="text-sm text-muted-foreground">
          Internal communication about this inquiry
        </p>
      </CardHeader>
      <CardContent className="flex flex-col flex-1 min-h-0 space-y-4">
        <NoDataFound
          title="No team discussion found"
          description="Team discussion will appear here once available"
        />
        {/* <div className="flex-1 space-y-4 overflow-y-auto">
          {messages.map((message) => (
            <div
              key={message.id}
              className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
            >
              <Avatar className="size-8 bg-primary">
                <AvatarFallback className="bg-primary text-white text-sm font-medium">
                  {message.authorInitials}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold">
                    {message.author}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {message.timestamp}
                  </span>
                </div>
                <p className="text-sm text-foreground">{message.message}</p>
              </div>
            </div>
          ))}
        </div> */}

        {/* <div className="flex items-start gap-2 pt-2 border-t">
          <Textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Add a message..."
            className="flex-1"
          />
          <Button
            onClick={handleSendMessage}
            disabled={!newMessage.trim()}
            size="icon"
            className="shrink-0 size-10"
          >
            <Send className="size-4" />
          </Button>
        </div> */}
      </CardContent>
    </Card>
  );
}
