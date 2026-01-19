import type { RoleData } from "@/types/role";

/* -------------------- NEXT-AUTH MODULE AUGMENTATION -------------------- */

declare module "next-auth" {
  /**
   * Role object structure from the API
   */
  interface Role {
    id: string;
    name: string;
    description: string;
  }

  /**
   * User object returned from Credentials `authorize`
   * ⚠️ This exists ONLY during login
   */
  interface User {
    access_token: string;
    refresh_token: string;
    expires_in: number;

    user: {
      id: string;
      name: string;
      email: string;
      role: Role;
    };

    requires_password_change?: boolean;
    rememberMe?: boolean;
  }

  /**
   * Session object exposed to frontend
   */
  interface Session {
    id?: string;
    name?: string;
    email?: string;
    role?: Role;
    accessToken?: string;
    roles?: RoleData[];
    requiresPasswordChange?: boolean;

    /** Used for auto logout */
    error?: "RefreshAccessTokenError";
  }
}

/* -------------------- NEXT-AUTH JWT MODULE AUGMENTATION -------------------- */

declare module "next-auth/jwt" {
  interface JWT {
    // Identity
    id?: string;
    name?: string;
    email?: string;
    role?: import("next-auth").Role;

    // Tokens
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;

    // State
    rememberMe?: boolean;
    requiresPasswordChange?: boolean;

    // Authorization
    roles?: RoleData[];

    // Error handling
    error?: "RefreshAccessTokenError";
  }
}
