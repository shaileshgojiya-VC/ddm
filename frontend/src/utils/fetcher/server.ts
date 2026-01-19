import "server-only";
import { auth, signOut } from "@/utils/auth";
import type { FetcherProps, IResponse, Service } from "./types";

interface ServerFetcherProps extends FetcherProps {
  token?: boolean;
}

export default async function serverFetcher<T>({
  request,
  method = "GET",
  payload = null,
  token = false,
  headerOptions = {},
  type = "default",
  options = {},
}: ServerFetcherProps): Promise<IResponse<T>> {
  const services: Service = {
    default: process.env.NEXT_PUBLIC_API_URL!,
  };

  let authorization = {};

  if (token) {
    const session = await auth();
    authorization = {
      authorization: `Bearer ${session?.accessToken}`,
    };
  }

  const url = `${services[type]}/${request}`;

  let response: Response;

  try {
    response = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authorization,
        ...headerOptions,
      },
      body: payload ? JSON.stringify(payload) : null,
      ...options,
    });
  } catch {
    throw new Error("Service is temporarily unavailable");
  }

  let result: IResponse<T>;
  try {
    result = await response.json();
  } catch {
    throw new Error("Invalid server response");
  }

  if (!response.ok) {
    if (response.status === 401) {
      signOut({ redirect: true, redirectTo: "/login" });
      throw new Error("Session expired. Please login again.");
    }

    throw new Error(result?.message || "Server error");
  }

  return result;
}
