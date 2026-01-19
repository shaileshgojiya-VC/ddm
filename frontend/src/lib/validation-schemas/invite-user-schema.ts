import { z } from "zod";

export const inviteUserSchema = z.object({
  fullName: z.string().min(2, "Name must be at least 2 characters"),
  email: z.email({ message: "Invalid email address" }),
  roleUuid: z.string().min(1, "Please select a role"),
});

export type InviteUserFormValues = z.infer<typeof inviteUserSchema>;
