import { MessageSquare, Users } from "lucide-react";
import Link from "next/link";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import NoDataFound from "@/components/core/no-data-found";

interface Message {
  id: string;
  name: string;
  preview: string;
  unreadCount?: number;
  date: string;
  type: "team" | "individual";
}

interface MessageListProps {
  readonly messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  if (!messages || messages?.length === 0) {
    return <NoDataFound title="No conversations found" />;
  }

  return (
    <Card className="py-0">
      <CardContent className="divide-y p-0">
        {messages?.map((message) => {
          const isTeamChat = message.type === "team";
          const initial = message.name.charAt(0).toUpperCase();

          return (
            <Link
              href={`/messages/${message.id}`}
              key={message.id}
              className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors cursor-pointer gap-4"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="relative">
                  <Avatar className={`size-12 bg-primary/10`}>
                    <AvatarFallback className="bg-primary/10 text-primary">
                      {isTeamChat ? <Users className="size-5" /> : initial}
                    </AvatarFallback>
                  </Avatar>
                  {message.unreadCount && message.unreadCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 size-5 flex items-center justify-center p-0 rounded-full bg-primary hover:bg-primary text-white text-xs">
                      {message.unreadCount}
                    </Badge>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium truncate">{message.name}</span>
                    {isTeamChat &&
                      message.unreadCount &&
                      message.unreadCount > 0 && (
                        <Badge variant="secondary" className="shrink-0 text-xs">
                          {message.unreadCount}
                        </Badge>
                      )}
                  </div>
                  <p className="text-sm text-muted-foreground truncate">
                    {message.preview}
                  </p>
                </div>
              </div>
              <div className="text-xs text-muted-foreground shrink-0">
                {message.date}
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
