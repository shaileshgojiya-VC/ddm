"use client";

import { useEffect } from "react";
import { useSession, signOut } from "next-auth/react";

export default function AutoLogout() {
  const { data: session, status } = useSession();

  useEffect(() => {
    if (
      status === "authenticated" &&
      session?.error === "RefreshAccessTokenError"
    ) {
      console.warn("🚪 AUTO LOGOUT TRIGGERED");
      signOut({ redirect: true, redirectTo: "/login" });
    }
  }, [session, status]);

  return null;
}
