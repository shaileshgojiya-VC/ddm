import { Building2, ChevronRight, Mail } from "lucide-react";
import Link from "next/link";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatDate } from "@/utils/date-format";
import { getRoleBadgeStyle } from "@/utils/role-styles";
import type { User } from "@/types/user";
import NoDataFound from "@/components/core/no-data-found";

interface UserListProps {
  readonly users: User[];
}

export default function UserList({ users }: UserListProps) {
  if (!users || users?.length === 0) {
    return <NoDataFound title="No users found" />;
  }

  return (
    <Card className="py-0">
      <CardContent className="divide-y p-0">
        {users?.map((user) => {
          const roleBadgeStyle = getRoleBadgeStyle(user?.role?.name || "");

          return (
            <Link
              href={`/users/${user?.id}`}
              key={user?.id}
              className="flex flex-col md:flex-row md:items-center justify-between p-4 hover:bg-muted/50 transition-colors cursor-pointer md:gap-4 gap-3"
            >
              <div className="flex items-center md:gap-4 gap-3">
                <Avatar className="md:size-10 size-8 bg-primary">
                  <AvatarFallback className="bg-primary text-white font-medium">
                    {user?.name?.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{user?.name}</span>
                    {user?.role && (
                      <Badge className={roleBadgeStyle}>{user.role.name}</Badge>
                    )}
                  </div>
                  <div className="flex flex-col xl:flex-row xl:items-center xl:gap-4 gap-1 text-sm text-muted-foreground">
                    <div className="flex items-center gap-2 ">
                      <Mail className="size-3 shrink-0" />
                      {user?.email}
                    </div>
                    {user?.role && (
                      <div className="flex items-center gap-2">
                        <Building2 className="size-3 shrink-0" />
                        {user.role.description}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 text-sm md:pl-0 pl-11">
                <div className="md:text-right">
                  <p className="text-muted-foreground">Last active</p>
                  <p className="font-medium">{formatDate(user?.joined_at)}</p>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
