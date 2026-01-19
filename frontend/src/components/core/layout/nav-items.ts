import {
  Building2,
  FileText,
  LayoutDashboard,
  LucideIcon,
  MessageSquare,
  Package,
  Settings,
  Sparkles,
  UserCircle,
} from "lucide-react";

interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  module: string;
}

export const navItems: NavItem[] = [
  {
    title: "Dashboard",
    url: "/dashboard",
    icon: LayoutDashboard,
    module: "dashboard",
  },
  {
    title: "Inquiry Management",
    url: "/inquiry-management",
    icon: FileText,
    module: "inquiry-management",
  },
  {
    title: "Users",
    url: "/users",
    icon: UserCircle,
    module: "users",
  },
  {
    title: "Messages",
    url: "/messages",
    icon: MessageSquare,
    module: "messages",
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
    module: "settings",
  },
  {
    title: "Products",
    url: "/products",
    icon: Package,
    module: "products",
  },
  {
    title: "Suppliers",
    url: "/suppliers",
    icon: Building2,
    module: "suppliers",
  },
  {
    title: "AI Assistant",
    url: "/ai-assistant",
    icon: Sparkles,
    module: "ai-assistant",
  },
];
