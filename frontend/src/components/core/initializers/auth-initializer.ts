"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useUserStore } from "@/stores/use-user-store";

export default function AuthInitializer() {
  const { data: session, status } = useSession();
  const setUser = useUserStore((state) => state.setUser);
  const clearUser = useUserStore((state) => state.clearUser);

  useEffect(() => {
    if (status === "authenticated" && session) {
      setUser({
        name: session?.user?.name ?? session?.name ?? "",
        email: session?.user?.email ?? session?.email ?? "",
        id: session?.id ?? "",
        role: session?.role ?? { id: "", name: "", description: "" },
      });
    }

    if (status === "unauthenticated") {
      clearUser();
    }
  }, [session, status, setUser, clearUser]);

  return null;
}
