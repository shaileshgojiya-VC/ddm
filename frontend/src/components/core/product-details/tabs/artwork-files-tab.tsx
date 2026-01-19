import FileList from "@/components/core/file-list";
import { InfoItem } from "@/components/core/info-item";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { File } from "@/types/document-detail";
import { Product } from "@/types/product";

interface ArtworkFilesTabProps {
  readonly productDetails?: Product | null;
  readonly mode: "view" | "edit";
}

export default function ArtworkFilesTab({
  productDetails,
  mode,
}: ArtworkFilesTabProps) {
  const { is_fda_approved, art_number, artwork_documents } =
    productDetails || {};
  // Static data - replace with API call in future
  const STATIC_FILES: File[] = [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Artwork Information</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoItem
            label="FDA Approved"
            value={is_fda_approved ? "Yes" : "No"}
          />
          <InfoItem label="Artwork Number" value={art_number || "-"} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Artwork Files</CardTitle>
        </CardHeader>
        <CardContent>
          <FileList
            files={STATIC_FILES}
            emptyMessage="No documents available"
            emptyDescription="Documents will appear here once uploaded"
          />
        </CardContent>
      </Card>
    </div>
  );
}
