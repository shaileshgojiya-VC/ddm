import NavLinks from "@/components/core/layout/nav-links";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
} from "@/components/ui/sidebar";
import Image from "next/image";

export default function AppSidebar({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader className="h-[68] group-data-[collapsible=icon]:h-14 overflow-hidden border-b border-b-primary/70">
        <div className="flex gap-3 px-2 group-data-[collapsible=icon]:px-1 py-1 h-full group-data-[collapsible=icon]:items-center group-data-[collapsible=icon]:justify-center">
          <div className="relative aspect-[1.74/1] h-10 group-data-[collapsible=icon]:h-6">
            <Image
              src="/images/dana-dairy-logo.png"
              alt="Dana Dairy Logo"
              fill
              sizes="132px"
              loading="eager"
            />
          </div>
          <div className="flex flex-col group-data-[collapsible=icon]:hidden ">
            <h1 className="text-lg font-bold">Dana Dairy</h1>
            <p className="text-xs text-muted/70">Inquiry Management</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="p-4">
          <SidebarGroupContent>
            <NavLinks />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
  );
}
