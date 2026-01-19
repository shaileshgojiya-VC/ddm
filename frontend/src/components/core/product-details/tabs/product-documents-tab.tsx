import DocumentList from "@/components/core/document-list";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { Product } from "@/types/product";

interface ProductDocumentsTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function ProductDocumentsTab({
  productDetails,
  mode,
}: ProductDocumentsTabProps) {
  const { document_details } = productDetails || {};
  return (
    <Card>
      <CardHeader>
        <CardTitle>All Documents</CardTitle>
      </CardHeader>
      <CardContent>
        <DocumentList
          documents={document_details || []}
          emptyMessage="No documents available"
          emptyDescription="Product documents will appear here once uploaded"
        />
      </CardContent>
    </Card>
  );
}
