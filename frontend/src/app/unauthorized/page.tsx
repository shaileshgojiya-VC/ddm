import { ShieldX } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="flex flex-col items-center space-y-4 text-center">
          <div className="rounded-full bg-red-100 p-4">
            <ShieldX className="size-12 text-red-600" />
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              Access Denied
            </h1>
            <p className="text-muted-foreground">
              You don&apos;t have permission to access this page. Please contact
              your administrator if you believe this is an error.
            </p>
          </div>

          <div className="flex gap-3">
            <Button asChild variant="outline">
              <Link href="/">Go to Home</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
