"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Check, ChevronDown, Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  inviteUserSchema,
  type InviteUserFormValues,
} from "@/lib/validation-schemas/invite-user-schema";

import { createUserAction } from "@/actions/user/create-user-actions";

interface InviteUserDialogProps {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
}

export default function InviteUserDialog({
  open,
  onOpenChange,
}: InviteUserDialogProps) {
  const [isPending, startTransition] = useTransition();
  const { data: session } = useSession();
  const router = useRouter();

  const form = useForm<InviteUserFormValues>({
    resolver: zodResolver(inviteUserSchema),
    defaultValues: {
      fullName: "",
      email: "",
      roleUuid: "",
    },
  });

  const submitHandler = (formData: FormData) => {
    startTransition(async () => {
      const result = await createUserAction(formData);
      if (result.success) {
        toast.success(result.message || "User created successfully");
        form.reset();
        onOpenChange(false);
        router.refresh();
      } else {
        toast.error(result.message || "Failed to create user");
      }
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[430px]">
        <DialogHeader>
          <DialogTitle>Create User</DialogTitle>
          <DialogDescription>Add a new user to the system</DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form action={submitHandler} className="space-y-4">
            {/* Full Name */}
            <FormField
              control={form.control}
              name="fullName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input {...field} name="fullName" placeholder="Full Name" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Email */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      name="email"
                      type="email"
                      placeholder="user@example.com"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Role */}
            <FormField
              control={form.control}
              name="roleUuid"
              render={({ field }) => {
                const selectedRole = session?.roles?.find(
                  (role) => role.id === field.value
                );

                const selectedLabel = selectedRole
                  ? selectedRole.name
                  : "Select role";

                return (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className="w-full justify-between"
                          >
                            {selectedLabel}
                            <ChevronDown className="size-4" />
                          </Button>
                        </FormControl>
                      </DropdownMenuTrigger>

                      <DropdownMenuContent align="start" className="w-full">
                        {session?.roles?.map((role) => (
                          <DropdownMenuItem
                            key={role.id}
                            onClick={() => field.onChange(role.id)}
                          >
                            {role.name}
                            {field.value === role.id && (
                              <Check className="size-4" />
                            )}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                    <input type="hidden" name="roleUuid" value={field.value} />
                    <FormMessage />
                  </FormItem>
                );
              }}
            />

            {/* Buttons */}
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                disabled={isPending}
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>

              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="animate-spin" />}
                {isPending ? "Creating..." : "Create User"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
