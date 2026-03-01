import { createBrowserRouter, Navigate, Outlet, useNavigate, useParams } from "react-router";
import { useEffect } from "react";
import { DashboardLayout } from "./components/DashboardLayout";
import { Dashboard } from "./components/Dashboard";
import { Campaigns } from "./components/Campaigns";
import { CampaignDetail } from "./components/CampaignDetail";
import { Callers } from "./components/Callers";
import { Scripts } from "./components/Scripts";
import { Employees } from "./components/Employees";
import { Calls } from "./components/Calls";
import { NotFound } from "./components/NotFound";
import { LoginPage } from "./components/LoginPage";
import { CompanySignUp } from "./components/CompanySignUp";
import { CallMonitoring } from "./components/CallMonitoring";
import { UserManagement } from "./components/UserManagement";
import { AcceptInvite } from "./components/AcceptInvite";
import { Analytics } from "./components/Analytics";
import { EmployeeDetail } from "./components/EmployeeDetail";
import { LandingPage } from "./components/LandingPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

/** Root layout that wraps everything in AuthProvider */
function RootLayout() {
  const navigate = useNavigate();

  useEffect(() => {
    // Supabase invite links redirect to site_url with hash fragments.
    // Detect type=invite in the hash and redirect to /invite/accept.
    const hash = window.location.hash;
    if (hash && hash.includes("type=invite")) {
      navigate("/invite/accept" + hash, { replace: true });
    }
  }, [navigate]);

  return (
    <AuthProvider>
      <Outlet />
    </AuthProvider>
  );
}

/** Redirect /campaigns/:id → /dashboard/campaigns/:id */
function CampaignDetailRedirect() {
  const { id } = useParams<{ id: string }>();
  return <Navigate to={`/dashboard/campaigns/${id}`} replace />;
}

/** Shows landing page if not authenticated, redirects to /dashboard if logged in */
function LandingOrRedirect() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-svh flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#252a39]" />
      </div>
    );
  }

  if (session) {
    return <Navigate to="/dashboard" replace />;
  }

  return <LandingPage />;
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
      /* Public landing page — redirects to /dashboard if authenticated */
      { path: "/", Component: LandingOrRedirect },

      /* Auth pages — full-viewport, no dashboard shell */
      { path: "/login", Component: LoginPage },
      { path: "/signup", Component: CompanySignUp },
      { path: "/invite/accept", Component: AcceptInvite },
      { path: "/create-account", element: <Navigate to="/login" replace /> },

      /* Short-URL redirects for links that omit /dashboard prefix */
      { path: "/campaigns", element: <Navigate to="/dashboard/campaigns" replace /> },
      { path: "/campaigns/:id", Component: CampaignDetailRedirect },

      /* Protected dashboard routes */
      {
        Component: ProtectedRoute,
        children: [
          {
            path: "/dashboard",
            Component: DashboardLayout,
            children: [
              { index: true, Component: Dashboard },
              { path: "analytics", Component: Analytics },
              { path: "campaigns", Component: Campaigns },
              { path: "campaigns/:id", Component: CampaignDetail },
              { path: "callers", Component: Callers },
              { path: "scripts", Component: Scripts },
              { path: "employees", Component: Employees },
              { path: "employees/:id", Component: EmployeeDetail },
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
