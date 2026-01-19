"use server";

import { redirect } from "next/navigation";
import { auth } from "@/utils/auth";
import serverFetcher from "@/utils/fetcher/server";
import { SupplierFormData } from "@/types/supplier";

interface UpdateSupplierActionProps {
  id: string | undefined | null;
  data: SupplierFormData | undefined | null;
}
export async function updateSupplierAction({
  id,
  data,
}: UpdateSupplierActionProps) {
  const session = await auth();

  if (!session?.accessToken) {
    throw new Error("Unauthorized");
  }

  redirect(`/suppliers/${id}/view`);
  return;
  // try {
  //   const response = await serverFetcher({
  //     request: `supplier/${id}`,
  //     method: "PUT",
  //     payload: data,
  //     token: true,
  //   });

  //   if (response?.status === "success") {
  //     redirect(`/suppliers/${id}/view`);
  //   }
  // } catch (error) {
  //   throw new Error(
  //     error instanceof Error ? error.message : "Failed to update supplier"
  //   );
  // }
}
