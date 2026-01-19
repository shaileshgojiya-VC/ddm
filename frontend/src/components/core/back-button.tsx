"use client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

interface BackButtonProps {
  readonly className?: string;
}

export default function BackButton({ className }: BackButtonProps) {
  const router = useRouter();
  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn("", className)}
      onClick={() => router.back()}
    >
      <ArrowLeft className="size-5" />
    </Button>
  );
}
