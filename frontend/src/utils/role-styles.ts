const roleColors: Record<string, string> = {
  admin: "bg-red-500 text-white hover:bg-red-500 rounded-md capitalize",
  management: "bg-primary text-white hover:bg-primary rounded-md capitalize",
  sales:
    "bg-slate-200 text-foreground hover:bg-slate-200 rounded-md capitalize",
};

export function getRoleBadgeStyle(roleName: string): string {
  const normalizedRole = roleName?.toLowerCase() || "";
  return (
    roleColors[normalizedRole] ??
    "bg-muted text-muted-foreground hover:bg-muted rounded-md capitalize"
  );
}
