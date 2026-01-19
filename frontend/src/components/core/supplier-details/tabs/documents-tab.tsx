import DocumentList from "@/components/core/document-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { Supplier } from "@/types/supplier";

interface SupplierDocumentsTabProps {
  readonly supplierDetails: Supplier;
}

export default function SupplierDocumentsTab({
  supplierDetails,
}: SupplierDocumentsTabProps) {
  const { document_details } = supplierDetails || {};

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <p className="text-sm text-muted-foreground">
            All documents from Fonterra Co-operative Group
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
    </div>
  );
}
