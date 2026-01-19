"use client";

import { SessionProvider } from "next-auth/react";
import { Session } from "next-auth";
import AutoLogout from "./auto-logout";

export default function Providers({
  children,
  session,
}: Readonly<{
  children: React.ReactNode;
  session?: Session | null;
}>) {
  return (
    <SessionProvider session={session}>
      <AutoLogout />
      {children}
    </SessionProvider>
  );
}
