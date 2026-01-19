"use client";
import AutoLogout from "@/components/core/auto-logout";
import ErrorCard from "@/components/core/error-card";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  readonly error: Error;
  readonly reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error:", error);
  }, [error]);
  const handleReset = () => {
    reset();
  };
  console.log(error);
  return (
    <div className="flex items-center justify-center h-screen">
      <AutoLogout />
      <ErrorCard handleReset={handleReset} />
    </div>
  );
}
