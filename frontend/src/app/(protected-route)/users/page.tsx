import PageHeading from "@/components/core/page-heading";
import Pagination from "@/components/core/pagination";
import SuspenseLoader from "@/components/core/suspense-loader";
import InviteUserButton from "@/components/core/users/invite-user-button";
import RoleStats from "@/components/core/users/role-stats";
import UserFilters from "@/components/core/users/user-filters";
import UserList from "@/components/core/users/user-list";
import type { UsersSearchParams } from "@/types/user";
import { auth } from "@/utils/auth";
import { getUsers } from "@/lib/data";
import { Suspense } from "react";

interface UsersPageProps {
  readonly searchParams: Promise<UsersSearchParams>;
}

export default async function UsersPage({ searchParams }: UsersPageProps) {
  const session = await auth();
  const userRole = session?.role?.name;
  const resolvedSearchParams = await searchParams;
  const { users, pagination, activeCounts } = await getUsers(
    resolvedSearchParams
  );
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeading title="Team Members" description="All system users" />
        {userRole === "Admin" && <InviteUserButton />}
      </div>

      <Suspense fallback={<SuspenseLoader title="Loading users filters..." />}>
        <UserFilters />
      </Suspense>
      <RoleStats activeCounts={activeCounts} />
      <UserList users={users} />
      <Pagination pagination={pagination} />
    </div>
  );
}
