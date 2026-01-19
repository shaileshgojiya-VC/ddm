"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Eye, EyeOff, ArrowLeft, Loader2 } from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";

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
  resetPasswordSchema,
  type ResetPasswordFormValues,
} from "@/lib/validation-schemas/auth-schema";
import { toast } from "sonner";
import clientFetcher from "@/utils/fetcher/client";
import AuthCardWrapper from "./auth-card-wrapper";

export default function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const router = useRouter();

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      reset_token: token || "",
      password: "",
      confirmPassword: "",
    },
  });

  useEffect(() => {
    if (token) {
      form.setValue("reset_token", token);
    } else {
      toast.error("Invalid reset link", {
        description:
          "The reset link is missing or invalid. Please request a new one.",
      });
    }
  }, [token, form]);

  if (!token) {
    return (
      <AuthCardWrapper
        title="Invalid Reset Link"
        description="The reset link is missing or invalid"
      >
        <div className="text-center space-y-4">
          <p className="text-muted-foreground">
            Please request a new password reset link from the login page.
          </p>
          <Link
            href="/login"
            className="flex items-center justify-center gap-3 font-medium"
          >
            <ArrowLeft className="size-4" />
            Back to Login
          </Link>
        </div>
      </AuthCardWrapper>
    );
  }

  const onSubmit = async (data: ResetPasswordFormValues) => {
    setIsLoading(true);

    try {
      const response = await clientFetcher({
        request: "auth/password/reset",
        method: "POST",
        payload: {
          reset_token: data.reset_token,
          new_password: data.password,
          confirm_password: data.confirmPassword,
        },
      });

      if (response?.status === "success") {
        toast.success("Password reset successful", {
          description:
            response.message || "Your password has been reset successfully.",
        });
        form.reset();

        // Small delay to let user see the success message
        setTimeout(() => {
          router.push("/login");
        }, 1500);
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
      title="Reset Password"
      description="Enter your new password below"
    >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>New Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter new password"
                      className="pr-10"
                      {...field}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Confirm Password</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Input
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm new password"
                      className="pr-10"
                      {...field}
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="size-4" />
                      ) : (
                        <Eye className="size-4" />
                      )}
                    </button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading && <Loader2 className="animate-spin" />}
            {isLoading ? "Resetting..." : "Reset Password"}
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
