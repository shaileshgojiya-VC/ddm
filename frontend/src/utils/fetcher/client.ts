"use client";

import { signOut } from "next-auth/react";
import type { FetcherProps, IResponse, Service } from "./types";

interface ClientFetcherProps extends FetcherProps {
  token?: string;
}

export default async function clientFetcher<IReturn>({
  request,
  method = "GET",
  payload = null,
  token = "",
  headerOptions = {},
  type = "default",
  options = {},
}: ClientFetcherProps): Promise<IResponse<IReturn>> {
  const services: Service = {
    default: `${process.env["NEXT_PUBLIC_API_URL"]}`,
  };

  const authorization = token && {
    authorization: `Bearer ${token}`,
  };

  const url = `${services[type]}/${request}`;
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...authorization,
      ...headerOptions,
    },
    ...options,
    body: payload ? JSON.stringify(payload) : null,
  });
  const result: IResponse<IReturn> = await response.json();
  if (!response.ok) {
    if (response.status === 401) {
      signOut({ redirect: false });
    }
    throw new Error(result.message);
  }

  return result;
}
