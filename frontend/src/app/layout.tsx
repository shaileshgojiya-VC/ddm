import Providers from "@/components/core/providers";
import { Toaster } from "@/components/ui/sonner";
import { auth } from "@/utils/auth";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Dana Dairy - Inquiry Management Portal",
  description:
    "AI-powered inquiry management system for Dana Dairy sales and administration",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await auth();
  return (
    <html lang="en">
      <body className={`font-sans antialiased ${inter.className}`}>
        <Providers session={session}>
          {children}
          <Toaster
            richColors
            position="bottom-right"
            expand={true}
            closeButton
          />
        </Providers>
      </body>
    </html>
  );
}
