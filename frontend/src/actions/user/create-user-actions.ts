"use server";

import serverFetcher from "@/utils/fetcher/server";

export async function createUserAction(formData: FormData) {
  try {
    const payload = {
      name: (formData.get("fullName") as string) || "",
      email: (formData.get("email") as string) || "",
      role_id: (formData.get("roleUuid") as string) || "",
    };

    const response = await serverFetcher({
      request: "admin/create/user",
      method: "POST",
      payload,
      token: true,
    });

    return {
      success: true,
      message: response?.message || "User created successfully",
    };
  } catch (error: unknown) {
    return {
      success: false,
      message:
        error instanceof Error
          ? error.message
          : "Failed to create user using action",
    };
  }
}
