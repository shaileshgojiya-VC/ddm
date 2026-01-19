import Image from "next/image";

export default function Loading() {
  return (
    <div className="flex flex-col gap-4 h-screen items-center justify-center">
      <div className="relative aspect-[1.74/1] h-16 mx-auto">
        <Image
          src="/images/dana-dairy-logo.png"
          alt="Dana Dairy Logo"
          fill
          sizes="132px"
          loading="eager"
        />
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-foreground">
        Welcome to Dana Dairy
      </h1>
      <p className="text-sm text-muted-foreground">
        We are loading the page for you. Please wait a moment.
      </p>
    </div>
  );
}
