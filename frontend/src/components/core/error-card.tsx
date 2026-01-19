import { ShieldX } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface ErrorCardProps {
  readonly handleReset: () => void;
}

export default function ErrorCard({ handleReset }: ErrorCardProps) {
  return (
    <div className="flex items-center justify-center p-4 min-h-full">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 text-center">
          <div className="rounded-full bg-red-100 p-4">
            <ShieldX className="size-12 text-red-600" />
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              Something went wrong
            </h1>
            <p className="text-muted-foreground">
              We couldn’t load this page. Please try again.
            </p>
          </div>
          <div className="flex gap-3">
            <Button asChild variant="outline">
              <Link href="/">Go to Home</Link>
            </Button>
            <Button onClick={handleReset}>Try again</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
