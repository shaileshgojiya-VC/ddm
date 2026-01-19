import { Card, CardContent, CardHeader } from "@/components/ui/card";
import Image from "next/image";

export default function AuthCardWrapper({
  title,
  description,
  children,
}: Readonly<{
  title?: string;
  description?: string;
  children?: React.ReactNode;
}>) {
  return (
    <Card className="w-full max-w-md border-none shadow-xs">
      <CardHeader className="text-center space-y-4">
        <div className="relative aspect-[1.74/1] h-16 mx-auto">
          <Image
            src="/images/dana-dairy-logo.png"
            alt="Dana Dairy Logo"
            fill
            sizes="132px"
            loading="eager"
          />
        </div>
        {(title || description) && (
          <div className="space-y-1">
            {title && (
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                {title}
              </h1>
            )}
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
        )}
      </CardHeader>
      {children && <CardContent className="space-y-6">{children}</CardContent>}
    </Card>
  );
}
