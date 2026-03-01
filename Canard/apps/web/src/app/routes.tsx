import { createBrowserRouter, Navigate, Outlet } from "react-router";
import { DashboardLayout } from "./components/DashboardLayout";
import { Dashboard } from "./components/Dashboard";
import { Campaigns } from "./components/Campaigns";
import { CampaignDetail } from "./components/CampaignDetail";
import { Callers } from "./components/Callers";
import { Employees } from "./components/Employees";
import { Calls } from "./components/Calls";
import { NotFound } from "./components/NotFound";
import { LoginPage } from "./components/LoginPage";
import { CompanySignUp } from "./components/CompanySignUp";
import { CallMonitoring } from "./components/CallMonitoring";
import { UserManagement } from "./components/UserManagement";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

/** Root layout that wraps everything in AuthProvider */
function RootLayout() {
  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}

/** Redirects to /login if not authenticated */
function ProtectedRoute() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-svh flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#252a39]" />
      </div>
    );
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    children: [
      /* Auth pages — full-viewport, no dashboard shell */
      { path: "/login", Component: LoginPage },
      { path: "/signup", Component: CompanySignUp },
      { path: "/create-account", element: <Navigate to="/login" replace /> },

      /* Protected dashboard routes */
      {
        Component: ProtectedRoute,
        children: [
          {
            path: "/",
            Component: DashboardLayout,
            children: [
              { index: true, Component: Dashboard },
              { path: "campaigns", Component: Campaigns },
              { path: "campaigns/:id", Component: CampaignDetail },
              { path: "callers", Component: Callers },
              { path: "employees", Component: Employees },
              { path: "calls", Component: Calls },
              { path: "monitoring", Component: CallMonitoring },
              { path: "settings/users", Component: UserManagement },
              { path: "*", Component: NotFound },
            ],
          },
        ],
      },
    ],
  },
]);
