import PageHeading from "@/components/core/page-heading";
import Pagination from "@/components/core/pagination";
import NewChatButton from "@/components/core/messages/new-chat-button";
import MessageFilters from "@/components/core/messages/message-filters";
import MessageList from "@/components/core/messages/message-list";

interface MessagesPageProps {
  readonly searchParams: Promise<{
    search?: string;
    page?: string;
    limit?: string;
  }>;
}

// Mock data - Replace with actual API call
async function getMessages(searchParams: {
  search?: string;
  page?: string;
  limit?: string;
}) {
  const { search, page = "1", limit = "10" } = searchParams;

  // Mock messages data
  const allMessages = [
    {
      id: "1",
      name: "Sales Team",
      preview: "Let's discuss the new lead from Al-Rashid Trading",
      unreadCount: 3,
      date: "15 Jan",
      type: "team" as const,
    },
    {
      id: "2",
      name: "Mike Chen",
      preview: "I've updated the quotation for the olive oil inquiry",
      unreadCount: 1,
      date: "15 Jan",
      type: "individual" as const,
    },
    {
      id: "3",
      name: "Product Updates",
      preview: "New pricing sheet has been uploaded",
      unreadCount: 3,
      date: "14 Jan",
      type: "team" as const,
    },
    {
      id: "4",
      name: "Sarah Johnson",
      preview: "Can you check the deal status for Dubai Foods?",
      date: "14 Jan",
      type: "individual" as const,
    },
    {
      id: "5",
      name: "Management Updates",
      preview: "Monthly report is ready for review",
      unreadCount: 2,
      date: "14 Jan",
      type: "team" as const,
    },
  ];

  // Filter by search if provided
  const filteredMessages = search
    ? allMessages.filter(
        (msg) =>
          msg.name.toLowerCase().includes(search.toLowerCase()) ||
          msg.preview.toLowerCase().includes(search.toLowerCase())
      )
    : allMessages;

  const currentPage = Number.parseInt(page);
  const itemsPerPage = Number.parseInt(limit);
  const totalMessages = filteredMessages.length;
  const totalPages = Math.ceil(totalMessages / itemsPerPage);

  // Paginate results
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedMessages = filteredMessages.slice(startIndex, endIndex);

  return {
    messages: paginatedMessages,
    pagination: {
      page: currentPage,
      pages: totalPages,
      limit: itemsPerPage,
      total: totalMessages,
    },
  };
}

export default async function MessagesPage({
  searchParams,
}: MessagesPageProps) {
  const resolvedSearchParams = await searchParams;
  const { messages, pagination } = await getMessages(resolvedSearchParams);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeading title="Messages" description="Team conversations" />
        <NewChatButton />
      </div>

      <MessageFilters />
      <MessageList messages={messages} />
      <Pagination pagination={pagination} />
    </div>
  );
}
