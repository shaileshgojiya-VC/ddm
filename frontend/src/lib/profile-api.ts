"use client";

import { signOut } from "next-auth/react";
import clientFetcher from "@/utils/fetcher/client";
import type { Profile, UpdateProfileRequest } from "@/types/user";
import type { IResponse } from "@/utils/fetcher/types";

/**
 * Uploads profile image for current user
 * @param file - Image file to upload
 * @param accessToken - User's access token
 * @returns Updated profile data
 */
export async function uploadProfileImage(
  file: File,
  accessToken: string
): Promise<Profile | null> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    throw new Error("API URL is not configured");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiUrl}/auth/profile/image`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${accessToken}`,
    },
    body: formData,
  });

  const result: IResponse<Profile> = await response.json();

  if (!response.ok) {
    if (response.status === 401) {
      signOut({ redirect: false });
      throw new Error("Session expired. Please login again.");
    }
    throw new Error(result.message || "Failed to upload profile image");
  }

  return result.data ?? null;
}

/**
 * Fetches current user's profile (client-side)
 * @param accessToken - User's access token
 * @returns Profile data or null if not found
 */
export async function getProfile(accessToken: string): Promise<Profile | null> {
  const response = await clientFetcher<Profile>({
    request: "auth/profile",
    method: "GET",
    token: accessToken,
  });

  return response.data ?? null;
}

/**
 * Updates current user's profile (client-side)
 * @param data - Profile update data (name, phone_number, location)
 * @param accessToken - User's access token
 * @returns Updated profile data
 */
export async function updateProfile(
  data: UpdateProfileRequest,
  accessToken: string
): Promise<Profile | null> {
  const response = await clientFetcher<Profile>({
    request: "auth/profile",
    method: "PUT",
    payload: data as Record<string, unknown>,
    token: accessToken,
  });

  return response.data ?? null;
}

