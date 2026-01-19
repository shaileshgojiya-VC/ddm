import AuthInitializer from "@/components/core/initializers/auth-initializer";
import { AppHeader } from "@/components/core/layout/app-header";
import AppSidebar from "@/components/core/layout/app-sidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export default function ProtectedRouteLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <AuthInitializer />
      <SidebarProvider
        className="h-screen"
        style={
          {
            "--sidebar-width-icon": "4.5rem",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset className="min-h-screen w-[calc(100%-var(--sidebar-width))] group-data-[collapsible=icon]:w-[calc(100%-var(--sidebar-width-icon))]">
          <AppHeader />
          <div className="p-4 flex-1 overflow-y-auto">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </>
  );
}
