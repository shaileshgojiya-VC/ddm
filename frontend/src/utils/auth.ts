import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import serverFetcher from "./fetcher/server";
import type { RolesResponse } from "@/types/role";
import type { JWT } from "next-auth/jwt";
import type { User } from "next-auth";

/* -------------------- CONSTANTS -------------------- */

const SESSION_MAX_AGE = 30 * 24 * 60 * 60; // 30 days (upper bound)
const ACCESS_TOKEN_BUFFER = 60 * 1000; // 60s in ms

/* -------------------- HELPERS -------------------- */

async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const response = await serverFetcher<{
      access_token: string;
      expires_in: number;
    }>({
      request: "auth/refresh",
      method: "POST",
      payload: {
        refresh_token: token.refreshToken,
      },
    });

    if (!response?.data) throw new Error("Refresh failed");

    return {
      ...token,
      accessToken: response.data.access_token,
      accessTokenExpires: Date.now() + response.data.expires_in * 1000,
      error: undefined,
    };
  } catch (error) {
    console.error("Refresh token failed:", error);

    return {
      ...token,
      accessToken: undefined,
      refreshToken: undefined,
      accessTokenExpires: undefined,
      error: "RefreshAccessTokenError",
    };
  }
}

/* -------------------- NEXTAUTH -------------------- */

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Credentials({
      async authorize(credentials) {
        if (!credentials) return null;

        const { request, payload } = credentials as {
          request: string;
          payload: string;
        };

        const parsed = JSON.parse(payload);
        const rememberMe = !!parsed.rememberMe;

        const response = await serverFetcher({
          request,
          method: "POST",
          payload: parsed,
        });

        if (!response?.data) return null;

        return {
          ...response.data,
          rememberMe,
        } as User;
      },
    }),
  ],

  session: {
    strategy: "jwt",
    maxAge: SESSION_MAX_AGE,
  },

  callbacks: {
    async jwt({ token, user }) {
      /* ---------- LOGIN ---------- */
      if (user) {
        token.accessToken = user.access_token;
        token.refreshToken = user.refresh_token;
        token.accessTokenExpires = Date.now() + user.expires_in * 1000;

        token.id = user.user.id;
        token.name = user.user.name;
        token.email = user.user.email;
        token.role = user.user.role;

        token.rememberMe = user.rememberMe;
        token.requiresPasswordChange = user.requires_password_change;

        // Fetch roles once
        try {
          const rolesRes = await serverFetcher<RolesResponse>({
            request: "auth/roles",
            method: "GET",
            token: true,
            headerOptions: {
              authorization: `Bearer ${user.access_token}`,
            },
          });
          token.roles = rolesRes?.data?.items ?? [];
        } catch {
          token.roles = [];
        }

        return token;
      }

      /* ---------- TOKEN STILL VALID ---------- */
      if (
        token.accessTokenExpires &&
        Date.now() < token.accessTokenExpires - ACCESS_TOKEN_BUFFER
      ) {
        return token;
      }

      /* ---------- TOKEN EXPIRED ---------- */
      return refreshAccessToken(token);
    },

    async session({ session, token }) {
      session.id = token.id;
      session.name = token.name;
      session.email = token.email;
      session.role = token.role;
      session.accessToken = token.accessToken;
      session.roles = token.roles;
      session.requiresPasswordChange = token.requiresPasswordChange;
      session.error = token.error;

      return session;
    },
  },
});
