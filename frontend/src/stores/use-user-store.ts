import { create } from "zustand";
import type { Role } from "next-auth";

interface UserData {
  name: string;
  email: string;
  role: Role;
  id: string;
}

interface UserState {
  user: UserData | null;
  setUser: (user: UserData) => void;
  clearUser: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clearUser: () => set({ user: null }),
}));
