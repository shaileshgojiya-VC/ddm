import { Card, CardContent } from "@/components/ui/card";

interface SuspenseLoaderProps {
  readonly title: string;
}

export default function SuspenseLoader({
  title = "Loading...",
}: SuspenseLoaderProps) {
  return (
    <Card>
      <CardContent className="flex items-center justify-center py-4">
        {title}
      </CardContent>
    </Card>
  );
}
