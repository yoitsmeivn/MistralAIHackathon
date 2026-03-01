import { Outlet, NavLink, useLocation, useNavigate, Link } from "react-router";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  BarChart3,
  PhoneCall,
  Users,
  UserCircle,
  FileText,
  Activity,
  ChevronRight,
  X,
  LogOut,
  Settings,
  Trash2,
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
import { useAuth } from "../contexts/AuthContext";
import { deleteAccount, getCampaign } from "../services/api";
import logoImg from "../../../CanardSecurityTransparent.png";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  exact?: boolean;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", exact: true },
  { to: "/analytics", icon: BarChart3, label: "Analytics" },
  { to: "/campaigns", icon: PhoneCall, label: "Campaigns" },
  { to: "/callers", icon: UserCircle, label: "Caller Profiles" },
  { to: "/scripts", icon: FileText, label: "Scripts" },
  { to: "/employees", icon: Users, label: "Employees" },
  { to: "/monitoring", icon: Activity, label: "Call Monitoring" },
  { to: "/settings/users", icon: Settings, label: "Team", adminOnly: true },
];

const labelMap: Record<string, string> = {
  analytics: "Analytics",
  campaigns: "Campaigns",
  callers: "Caller Profiles",
  scripts: "Scripts",
  employees: "Employees",
  calls: "Calls",
  monitoring: "Call Monitoring",
  settings: "Settings",
  users: "Team",
};

function useBreadcrumbs(pathname: string) {
  const [resolvedNames, setResolvedNames] = useState<Record<string, string>>({});

  useEffect(() => {
    const parts = pathname.split("/").filter(Boolean);
    // Detect /campaigns/:id pattern
    if (parts[0] === "campaigns" && parts[1] && !labelMap[parts[1]]) {
      const id = parts[1];
      if (!resolvedNames[id]) {
        getCampaign(id).then((c) => {
          if (c?.name) {
            setResolvedNames((prev) => ({ ...prev, [id]: c.name }));
          }
        });
      }
    }
  }, [pathname]);

  if (pathname === "/") return [{ label: "Dashboard" }];

  const parts = pathname.split("/").filter(Boolean);
  return parts.map((p, i) => {
    const href = "/" + parts.slice(0, i + 1).join("/");
    const label = resolvedNames[p] || labelMap[p] || p.charAt(0).toUpperCase() + p.slice(1);
    return { label, href };
  });
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
  const { appUser } = useAuth();
  const isAdmin = appUser?.role === "admin";
  const visibleItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  return (
    <SidebarContent className="px-3 py-4">
      <SidebarMenu>
        <AnimatePresence>
          {state === "expanded" &&
            visibleItems.map((item, i) => {
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
  const breadcrumbs = useBreadcrumbs(pathname);
  const { appUser, signOut } = useAuth();
  const navigate = useNavigate();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);

  async function handleSignOut() {
    await signOut();
    navigate("/login", { replace: true });
  }

  async function handleDeleteAccount() {
    setDeleting(true);
    setDeleteError("");
    try {
      await deleteAccount();
      await signOut();
      navigate("/login", { replace: true });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete account");
    } finally {
      setDeleting(false);
    }
  }

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
            {breadcrumbs.map((crumb, i) => {
              const isLast = i === breadcrumbs.length - 1;
              return (
                <span key={i} className="flex items-center gap-1">
                  {i > 0 && <ChevronRight className="size-3" />}
                  {isLast || !crumb.href ? (
                    <span className={isLast ? "text-foreground font-medium" : ""}>
                      {crumb.label}
                    </span>
                  ) : (
                    <Link
                      to={crumb.href}
                      className="hover:text-foreground transition-colors"
                    >
                      {crumb.label}
                    </Link>
                  )}
                </span>
              );
            })}
          </nav>

          {/* User info + sign out */}
          <div className="ml-auto flex items-center gap-3">
            {appUser && (
              <span className="text-sm text-muted-foreground">
                {appUser.full_name}
                {appUser.org_name && (
                  <span className="text-xs ml-1 opacity-60">({appUser.org_name})</span>
                )}
              </span>
            )}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Delete account"
            >
              <Trash2 className="size-4" />
            </button>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Sign out"
            >
              <LogOut className="size-4" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>

      {/* Delete account confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl border p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-semibold mb-2">Delete Account</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Are you sure you want to delete your account? This action cannot be undone.
            </p>
            {deleteError && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {deleteError}
              </div>
            )}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false);
                  setDeleteError("");
                }}
                className="rounded-md px-4 py-2 text-sm border hover:bg-muted transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="rounded-md px-4 py-2 text-sm bg-red-600 text-white hover:bg-red-700 transition-colors disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete Account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </SidebarProvider>
  );
}
