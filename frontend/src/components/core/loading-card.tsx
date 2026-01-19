import { Skeleton } from "@/components/ui/skeleton";

export default function LoadingCard() {
  return (
    <div className="w-full h-full overflow-hidden bg-white p-4 rounded-lg space-y-3">
      {Array.from({ length: 23 }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
