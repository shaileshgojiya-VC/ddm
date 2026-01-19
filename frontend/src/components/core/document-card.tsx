"use client";
import type { DocumentDetail } from "@/types/document-detail";
import { formatDate } from "@/utils/date-format";
import { Download, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DocumentCardProps {
  readonly document: DocumentDetail;
  readonly onDownload: (document: DocumentDetail) => void;
  readonly isDownloading?: boolean;
}

export default function DocumentCard({
  document,
  onDownload,
  isDownloading = false,
}: DocumentCardProps) {
  return (
    <div className="flex items-center gap-4 rounded-lg bg-muted/50 p-4 transition-colors hover:bg-muted/70">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border bg-background">
        <FileText className="size-5 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <h4 className="truncate text-sm font-medium text-foreground">
          {document?.file_name || "-"}
        </h4>
        <p className="text-xs text-muted-foreground flex flex-wrap items-center gap-1">
          <span className="truncate">{document?.name || "-"}</span>
          <span className="size-1 bg-muted-foreground inline-block rounded-full"></span>
          <span>
            Uploaded{" "}
            {document?.updated_at ? formatDate(document?.updated_at) : "-"}
          </span>
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onDownload(document)}
        disabled={isDownloading}
        className="shrink-0"
        aria-label={`Download ${document?.file_name || document?.name || "-"}`}
      >
        <Download className="size-4" />
      </Button>
    </div>
  );
}
