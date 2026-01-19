import { Bot } from "lucide-react";

import PageHeading from "@/components/core/page-heading";
import { Card, CardContent } from "@/components/ui/card";

export default function AIAssistantPage() {
  return (
    <div className="space-y-6">
      <PageHeading
        title="AI Assistant"
        description="Get intelligent assistance for your tasks"
      />

      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <div className="rounded-full bg-primary/10 p-4 mb-4">
            <Bot className="size-12 text-primary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">AI Assistant</h2>
          <p className="text-muted-foreground text-center max-w-md">
            Your intelligent assistant is ready to help. Start a conversation to
            get insights and recommendations.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
