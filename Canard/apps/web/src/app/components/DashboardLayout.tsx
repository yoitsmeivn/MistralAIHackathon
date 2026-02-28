import { Outlet, NavLink, useLocation } from "react-router";
import {
  LayoutDashboard,
  PhoneCall,
  Users,
  UserCircle,
  Phone,
  Activity,
  ChevronRight,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import {
  Sidebar,
  SidebarProvider,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  useSidebar,
} from "./ui/sidebar";
import { Separator } from "./ui/separator";
import logoImg from "../../../CanardSecurityTransparent.png";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { to: "/campaigns", icon: PhoneCall, label: "Campaigns" },
  { to: "/callers", icon: UserCircle, label: "Caller Profiles" },
  { to: "/employees", icon: Users, label: "Employees" },
  { to: "/monitoring", icon: Activity, label: "Call Monitoring" },
];

function getBreadcrumb(pathname: string) {
  if (pathname === "/") return ["Dashboard"];
  const parts = pathname.split("/").filter(Boolean);
  return parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1));
}

/** Backdrop overlay that appears when the sidebar is open */
function SidebarBackdrop() {
  const { state, toggleSidebar } = useSidebar();
  if (state !== "expanded") return null;
  return (
    <div
      className="fixed inset-0 z-30 bg-black/40 transition-opacity"
      onClick={toggleSidebar}
      aria-label="Close sidebar"
    />
  );
}

/** Close button inside the sidebar header */
function SidebarCloseButton() {
  const { toggleSidebar } = useSidebar();
  return (
    <button
      onClick={toggleSidebar}
      className="absolute right-3 top-3 rounded-md p-1 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
      aria-label="Close menu"
    >
      <X className="size-4" />
    </button>
  );
}

/** Sidebar navigation with staggered entrance animation */
function SidebarNav() {
  const { pathname } = useLocation();
  const { state } = useSidebar();

  return (
    <SidebarContent className="px-3 py-4">
      <SidebarMenu>
        <AnimatePresence>
          {state === "expanded" &&
            navItems.map((item, i) => {
              const isActive = item.exact
                ? pathname === item.to
                : pathname.startsWith(item.to);
              return (
                <motion.div
                  key={item.to}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{
                    duration: 0.2,
                    delay: i * 0.04,
                    ease: [0.32, 0.72, 0, 1],
                  }}
                >
                  <SidebarMenuItem>
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
                </motion.div>
              );
            })}
        </AnimatePresence>
      </SidebarMenu>
    </SidebarContent>
  );
}

export function DashboardLayout() {
  const { pathname } = useLocation();
  const breadcrumb = getBreadcrumb(pathname);

  return (
    <SidebarProvider defaultOpen={false}>
      {/* Backdrop overlay */}
      <SidebarBackdrop />

      <Sidebar className="border-r-0" style={{ "--sidebar-width": "15rem" } as React.CSSProperties}>
        {/* Logo + Close Button */}
        <SidebarHeader className="px-5 py-3 relative">
          <img
            src={logoImg}
            alt="Canard Security"
            className="w-full max-h-10 object-contain brightness-0 invert"
          />
          <SidebarCloseButton />
        </SidebarHeader>

        <Separator className="opacity-10" />

        {/* Navigation with stagger animation */}
        <SidebarNav />

        {/* Footer */}
        <SidebarFooter className="px-5 py-4">
          <Separator className="opacity-10 mb-3" />
          <p className="text-xs text-white/30">Canard Security © 2026</p>
        </SidebarFooter>
      </Sidebar>

      {/* Main content — always full-width, never shifts */}
      <div className="flex flex-1 flex-col w-full">
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
      </div>
    </SidebarProvider>
  );
}
