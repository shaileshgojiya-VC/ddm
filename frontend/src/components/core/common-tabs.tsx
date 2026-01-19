"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export interface TabItem {
  value: string;
  label: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
}

interface CommonTabsProps {
  readonly tabs: TabItem[];
  readonly defaultValue?: string;
  readonly className?: string;
}

export default function CommonTabs({
  tabs,
  defaultValue,
  className,
}: CommonTabsProps) {
  return (
    <Tabs
      defaultValue={defaultValue || tabs?.[0]?.value}
      className={cn("gap-4", className)}
    >
      <TabsList className="h-auto p-1 flex-wrap justify-start">
        {tabs?.map((tab) => (
          <TabsTrigger
            key={tab?.value}
            value={tab?.value}
            className="data-[state=active]:shadow-none text-inherit data-[state=active]:text-foreground flex-0 cursor-pointer"
          >
            {tab?.icon}
            {tab?.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs?.map((tab) => (
        <TabsContent key={tab?.value} value={tab?.value}>
          {tab?.content}
        </TabsContent>
      ))}
    </Tabs>
  );
}
