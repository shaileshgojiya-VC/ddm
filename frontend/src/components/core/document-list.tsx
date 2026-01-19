"use client";

import { useState } from "react";
import { toast } from "sonner";

import DocumentCard from "@/components/core/document-card";
import { downloadFile } from "@/utils/download";

import NoDataFound from "@/components/core/no-data-found";
import { DocumentDetail } from "@/types/document-detail";

interface DocumentListProps {
  readonly documents: DocumentDetail[];
  readonly emptyMessage?: string;
  readonly emptyDescription?: string;
}

export default function DocumentList({
  documents,
  emptyMessage = "No documents available",
  emptyDescription = "Documents will appear here once uploaded",
}: DocumentListProps) {
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownload = async (document: DocumentDetail) => {
    const downloadUrl = document?.path;
    const fileName = document?.file_name || document?.name;
    try {
      setDownloadingId(document?.id);

      // Use the downloadUrl from the url object

      // Use the reusable download utility
      await downloadFile(downloadUrl, fileName);
      toast.success("Document downloaded successfully", {
        description: `"${
          fileName || "-"
        }" document has been downloaded successfully.`,
      });
    } catch (error) {
      console.error("Failed to download document:", error);
      toast.error("Download failed", {
        description: `"${
          fileName || "-"
        }" document download failed. Please try again.`,
      });
    } finally {
      setDownloadingId(null);
    }
  };

  if (!documents || documents?.length === 0) {
    return <NoDataFound title={emptyMessage} description={emptyDescription} />;
  }

  return (
    <div className="space-y-2">
      {documents?.map((document) => (
        <DocumentCard
          key={document?.id}
          document={document}
          onDownload={handleDownload}
          isDownloading={downloadingId === document?.id}
        />
      ))}
    </div>
  );
}
