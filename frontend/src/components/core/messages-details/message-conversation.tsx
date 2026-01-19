import { FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
  isCurrentUser: boolean;
  attachment?: {
    name: string;
    url: string;
  };
}

interface MessageConversationProps {
  messages: Message[];
  date?: string;
}

export default function MessageConversation({
  messages,
  date,
}: MessageConversationProps) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* Date Separator */}
      {date && (
        <div className="flex items-center justify-center sticky top-0 z-10">
          <div className="bg-muted px-3 py-1 rounded-full text-xs text-muted-foreground">
            {date}
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((message) => (
        <div key={message.id} className="space-y-1">
          {!message.isCurrentUser && (
            <p className="text-xs text-muted-foreground px-1">
              {message.sender}
            </p>
          )}
          <div
            className={cn(
              "flex",
              message.isCurrentUser ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[70%] space-y-1",
                message.isCurrentUser ? "items-end" : "items-start"
              )}
            >
              <div
                className={cn(
                  "rounded-2xl px-4 py-2",
                  message.isCurrentUser
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                )}
              >
                <p className="text-sm whitespace-pre-wrap break-words">
                  {message.content}
                </p>
                {message.attachment && (
                  <div
                    className={cn(
                      "mt-2 flex items-center gap-2 p-2 rounded-lg",
                      message.isCurrentUser
                        ? "bg-primary-foreground/10"
                        : "bg-background"
                    )}
                  >
                    <FileText className="size-4 shrink-0" />
                    <span className="text-xs truncate">
                      {message.attachment.name}
                    </span>
                  </div>
                )}
              </div>
              <p
                className={cn(
                  "text-xs text-muted-foreground px-1",
                  message.isCurrentUser ? "text-right" : "text-left"
                )}
              >
                {message.timestamp}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
