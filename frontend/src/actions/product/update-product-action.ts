"use server";

import { redirect } from "next/navigation";
import { auth } from "@/utils/auth";
import serverFetcher from "@/utils/fetcher/server";
import { ProductFormData } from "@/types/product";

interface UpdateProductActionProps {
  id: string | undefined | null;
  data: ProductFormData | undefined | null;
}
export async function updateProductAction({
  id,
  data,
}: UpdateProductActionProps) {
  const session = await auth();

  if (!session?.accessToken) {
    throw new Error("Unauthorized");
  }
  redirect(`/products/${id}/view`);
  return;
  // try {
  //   const response = await serverFetcher({
  //     request: `product/${id}`,
  //     method: "PUT",
  //     payload: data,
  //     token: true,
  //   });

  //   if (response?.status === "success") {
  //     redirect(`/products/${id}/view`);
  //   }
  // } catch (error) {
  //   throw new Error(
  //     error instanceof Error ? error.message : "Failed to update product"
  //   );
  // }
}
