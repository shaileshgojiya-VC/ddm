"use client";

import DocumentList from "@/components/core/document-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { Inquiry } from "@/types/inquiry";

interface DocumentsTabProps {
  readonly inquiryDetails: Inquiry;
}

export default function DocumentsTab({ inquiryDetails }: DocumentsTabProps) {
  const { document_details } = inquiryDetails || {};

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
        <p className="text-sm text-muted-foreground">
          All files and attachments related to this inquiry
        </p>
      </CardHeader>
      <CardContent>
        <DocumentList
          documents={document_details || []}
          emptyMessage="No documents available"
          emptyDescription="Documents will appear here once uploaded"
        />
      </CardContent>
    </Card>
  );
}
