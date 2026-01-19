import MessageHeader from "@/components/core/messages-details/message-header";
import MessageConversation from "@/components/core/messages-details/message-conversation";
import MessageInput from "@/components/core/messages-details/message-input";
import { Card } from "@/components/ui/card";

interface MessageDetailsPageProps {
  readonly params: Promise<{ id: string }>;
}

interface Member {
  id: string;
  name: string;
  email?: string;
}

interface ConversationData {
  title: string;
  memberCount?: number;
  members?: string;
  type: "team" | "individual";
  date: string;
  membersList?: Member[];
  messages: Array<{
    id: string;
    sender: string;
    content: string;
    timestamp: string;
    isCurrentUser: boolean;
    attachment?: {
      name: string;
      url: string;
    };
  }>;
}

// Mock data - Replace with actual API call
async function getMessageDetails(id: string) {
  // Mock conversation data
  const conversations: Record<string, ConversationData> = {
    "1": {
      title: "Sales Team",
      memberCount: 3,
      members: "Mike Chen, Sarah Johnson, John Doe",
      type: "team",
      date: "15 Jan 2024",
      membersList: [
        {
          id: "1",
          name: "Mike Chen",
          email: "mike.chen@danadairy.com",
        },
        {
          id: "2",
          name: "Sarah Johnson",
          email: "sarah.johnson@danadairy.com",
        },
        {
          id: "3",
          name: "John Doe",
          email: "john.doe@danadairy.com",
        },
      ],
      messages: [
        {
          id: "1",
          sender: "Sarah Johnson",
          content:
            "Good morning team! We have a new inquiry from Al-Rashid Trading.",
          timestamp: "09:00",
          isCurrentUser: false,
        },
        {
          id: "2",
          sender: "Mike Chen",
          content:
            "Great. I'll take a look at it. What product are they interested in?",
          timestamp: "09:05",
          isCurrentUser: false,
        },
        {
          id: "3",
          sender: "Sarah Johnson",
          content:
            "They're looking for olive oil - about 500 tons for the Dubai market.",
          timestamp: "09:10",
          isCurrentUser: false,
        },
        {
          id: "4",
          sender: "You",
          content:
            "I can prepare a quotation for this. Let me check our current inventory and pricing.",
          timestamp: "09:15",
          isCurrentUser: true,
        },
        {
          id: "5",
          sender: "Mike Chen",
          content: "Thanks! I've attached the latest price list for reference.",
          timestamp: "09:20",
          isCurrentUser: false,
          attachment: {
            name: "Price_List_Jan2024.pdf",
            url: "#",
          },
        },
        {
          id: "6",
          sender: "You",
          content: "Perfect. I'll have the quotation ready by end of day.",
          timestamp: "10:30",
          isCurrentUser: true,
        },
      ],
    },
    "2": {
      title: "Mike Chen",
      type: "individual",
      date: "15 Jan 2024",
      messages: [
        {
          id: "1",
          sender: "Mike Chen",
          content: "Hi! I've updated the quotation for the olive oil inquiry.",
          timestamp: "14:30",
          isCurrentUser: false,
        },
        {
          id: "2",
          sender: "You",
          content: "Thanks Mike! Let me review it.",
          timestamp: "14:35",
          isCurrentUser: true,
        },
      ],
    },
  };

  return conversations[id] || conversations["1"];
}

export default async function MessageDetailsPage({
  params,
}: MessageDetailsPageProps) {
  const { id } = await params;
  const conversation = await getMessageDetails(id);

  return (
    <Card className="flex flex-col h-[calc(100vh-7rem)] gap-0 py-0">
      <MessageHeader
        title={conversation.title}
        memberCount={conversation.memberCount}
        members={conversation.members}
        type={conversation.type}
        membersList={conversation.membersList}
      />
      <MessageConversation
        messages={conversation.messages}
        date={conversation.date}
      />
      <MessageInput />
    </Card>
  );
}
