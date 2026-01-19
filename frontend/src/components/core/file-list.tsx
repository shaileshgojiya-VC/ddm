"use client";

import FileCard from "@/components/core/file-card";
import NoDataFound from "@/components/core/no-data-found";
import type { File } from "@/types/document-detail";

interface FileListProps {
  readonly files: File[];
  readonly emptyMessage?: string;
  readonly emptyDescription?: string;
}

/**
 * Reusable document list component with download functionality
 * @param files - Array of files to display
 * @param emptyMessage - Custom empty state message
 * @param emptyDescription - Custom empty state description
 */
export default function FileList({
  files,
  emptyMessage = "No files available",
  emptyDescription = "Files will appear here once uploaded",
}: FileListProps) {
  // Empty State
  if (files.length === 0) {
    return <NoDataFound title={emptyMessage} description={emptyDescription} />;
  }

  // Files List
  return (
    <div className="space-y-2">
      {files.map((file) => (
        <FileCard key={file.id} file={file} />
      ))}
    </div>
  );
}
