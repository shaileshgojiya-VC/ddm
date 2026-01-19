"use client";
import { Button } from "@/components/ui/button";
import { SquarePen } from "lucide-react";
import Link from "next/link";

export default function EditProductButton() {
  return (
    <Button variant="outline" className="shrink-0" asChild>
      <Link href="">
        <SquarePen />
        Edit Product
      </Link>
    </Button>
  );
}
