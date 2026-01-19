"use client";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { navItems } from "@/components/core/layout/nav-items";
import { useIsMobile } from "@/hooks/use-mobile";

export default function NavLinks() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const { toggleSidebar } = useSidebar();
  const isMobile = useIsMobile();
  const userRole = session?.roles?.find(
    (role) => role?.name === session?.role?.name
  );
  const userModules = userRole?.module_list ?? [];

  const accessibleItems = navItems?.filter((item) =>
    userModules?.includes(item?.module)
  );

  const isItemActive = (itemUrl: string) => {
    if (pathname === itemUrl) return true;
    return pathname.startsWith(`${itemUrl}/`);
  };

  return (
    <SidebarMenu className="gap-2">
      {accessibleItems?.length > 0 &&
        accessibleItems?.map((item) => (
          <SidebarMenuItem key={item?.title}>
            <SidebarMenuButton
              tooltip={item?.title}
              asChild
              isActive={isItemActive(item?.url)}
              className="[&>svg]:size-5 h-10 group-data-[collapsible=icon]:w-10! group-data-[collapsible=icon]:h-10! group-data-[collapsible=icon]:justify-center"
            >
              <Link
                href={item?.url}
                onClick={() => {
                  if (isMobile) {
                    toggleSidebar();
                  }
                }}
              >
                <item.icon />
                <span className="text-sm font-medium group-data-[collapsible=icon]:hidden ">
                  {item?.title}
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
    </SidebarMenu>
  );
}
