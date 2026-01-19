"use client";

import DOMPurify from "isomorphic-dompurify";

interface HtmlViewerProps {
  readonly html: string;
}

export default function HtmlViewer({ html }: HtmlViewerProps) {
  const cleanHtml = DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
  });

  return (
    <div
      className="prose max-w-none"
      dangerouslySetInnerHTML={{ __html: cleanHtml }}
    />
  );
}
