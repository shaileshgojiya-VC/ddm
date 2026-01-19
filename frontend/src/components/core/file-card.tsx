import { ExternalLink, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { File } from "@/types/document-detail";
import Link from "next/link";

interface FileCardProps {
  readonly file: File;
}

/**
 * Reusable document card component with download functionality
 * @param file - File data to display
 */
export default function FileCard({ file }: FileCardProps) {
  return (
    <div className="flex items-center gap-4 justify-between rounded-lg bg-muted/50 p-4 transition-colors hover:bg-muted/70">
      {/* Document Info */}
      <h4 className="truncate text-sm font-medium text-foreground flex items-center gap-2">
        <FileText className="size-5" />
        {file.name}
      </h4>
      {/* View Details Button */}
      <Button
        variant="outline"
        className="hover:bg-primary hover:text-primary-foreground"
        asChild
        size="sm"
      >
        <Link href={`/files/${file.id}/view`}>
          <ExternalLink className="size-4 mr-2" />
          Open
        </Link>
      </Button>
    </div>
  );
}
