"use client";

import { useUserStore } from "@/stores/use-user-store";

export default function LoginUser() {
  const user = useUserStore((state) => state.user);

  if (!user) {
    return null;
  }

  return (
    <div>
      <span>{user.name}</span>
    </div>
  );
}
