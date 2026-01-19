"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  forgotPasswordSchema,
  type ForgotPasswordFormValues,
} from "@/lib/validation-schemas/auth-schema";
import { toast } from "sonner";
import { useState } from "react";
import clientFetcher from "@/utils/fetcher/client";
import AuthCardWrapper from "./auth-card-wrapper";
import { ArrowLeft, Loader2 } from "lucide-react";

export default function ForgotPasswordForm() {
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (data: ForgotPasswordFormValues) => {
    setIsLoading(true);

    try {
      const response = await clientFetcher({
        request: "auth/password/forget",
        method: "POST",
        payload: {
          email: data.email,
        },
      });

      if (response?.status === "success") {
        toast.success("Reset link sent", {
          description:
            response.message ||
            "Please check your email for the password reset link.",
        });
        form.reset();
        // Don't redirect - let user stay or navigate manually
      }
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthCardWrapper
      title="Forgot Password"
      description="Enter your email to receive reset instructions"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="your@email.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading && <Loader2 className="animate-spin" />}
            {isLoading ? "Sending..." : "Send Reset Link"}
          </Button>
        </form>
      </Form>

      <div className="flex justify-center">
        <Link href="/login" className="flex items-center gap-3 font-medium">
          <ArrowLeft className="size-4" />
          Back to Login
        </Link>
      </div>
    </AuthCardWrapper>
  );
}
