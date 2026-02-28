import { Outlet, NavLink, useLocation } from "react-router";
import {
  LayoutDashboard,
  PhoneCall,
  Users,
  UserCircle,
  Phone,
  ChevronRight,
} from "lucide-react";
import {
  Sidebar,
  SidebarProvider,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger,
} from "./ui/sidebar";
import { Separator } from "./ui/separator";
import logoImg from "../../../CanardTransparent.png";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { to: "/campaigns", icon: PhoneCall, label: "Campaigns" },
  { to: "/callers", icon: UserCircle, label: "Caller Profiles" },
  { to: "/employees", icon: Users, label: "Employees" },
  { to: "/calls", icon: Phone, label: "Call History" },
];

function getBreadcrumb(pathname: string) {
  if (pathname === "/") return ["Dashboard"];
  const parts = pathname.split("/").filter(Boolean);
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1));
}

export function DashboardLayout() {
  const { pathname } = useLocation();
  const breadcrumb = getBreadcrumb(pathname);

  return (
    <SidebarProvider>
      <Sidebar className="border-r-0" style={{ "--sidebar-width": "15rem" } as React.CSSProperties}>
        {/* Logo */}
        <SidebarHeader className="px-5 py-5">
          <img
            src={logoImg}
            alt="Canard Security"
            className="h-10 w-auto brightness-0 invert"
          />
        </SidebarHeader>

        <Separator className="opacity-10" />

        {/* Navigation */}
        <SidebarContent className="px-3 py-4">
          <SidebarMenu>
            {navItems.map((item) => {
              const isActive =
                item.exact
                  ? pathname === item.to
                  : pathname.startsWith(item.to);
              return (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive}
                    tooltip={item.label}
                    className={
                      isActive
                        ? "bg-[#fdfbe1] text-[#252a39] font-medium hover:bg-[#fdfbe1] hover:text-[#252a39]"
                        : "text-white/60 hover:text-white hover:bg-white/8"
                    }
                  >
                    <NavLink to={item.to} end={item.exact}>
                      <item.icon className="size-4" />
                      <span>{item.label}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarContent>

        {/* Footer */}
        <SidebarFooter className="px-5 py-4">
          <Separator className="opacity-10 mb-3" />
          <p className="text-xs text-white/30">Canard Security © 2026</p>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset>
        {/* Top Header Bar */}
        <header className="flex h-14 items-center gap-3 border-b px-6 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
          <SidebarTrigger className="-ml-2" />
          <Separator orientation="vertical" className="h-5" />
          <nav className="flex items-center gap-1 text-sm text-muted-foreground">
            {breadcrumb.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1">
                {i > 0 && <ChevronRight className="size-3" />}
                <span className={i === breadcrumb.length - 1 ? "text-foreground font-medium" : ""}>
                  {crumb}
                </span>
              </span>
            ))}
          </nav>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
