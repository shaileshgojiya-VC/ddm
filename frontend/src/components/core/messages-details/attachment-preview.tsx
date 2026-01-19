"use client";

import { X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatFileSize } from "@/utils/file-upload";

interface AttachmentPreviewProps {
  readonly file: File;
  readonly onRemove: () => void;
}

export default function AttachmentPreview({
  file,
  onRemove,
}: AttachmentPreviewProps) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-muted rounded-lg">
      <FileText className="size-5 shrink-0 text-muted-foreground" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{file.name}</p>
        <p className="text-xs text-muted-foreground">
          {formatFileSize(file.size)}
        </p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={onRemove}
        className="size-6 shrink-0"
      >
        <X className="size-4" />
      </Button>
    </div>
  );
}
