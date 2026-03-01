import { createBrowserRouter } from "react-router";
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
import { ManagerAccountCreation } from "./components/ManagerAccountCreation";
import { CallMonitoring } from "./components/CallMonitoring";
import { Analytics } from "./components/Analytics";
import { EmployeeDetail } from "./components/EmployeeDetail";

export const router = createBrowserRouter([
  /* Auth pages — full-viewport, no dashboard shell */
  { path: "/login", Component: LoginPage },
  { path: "/signup", Component: CompanySignUp },
  { path: "/create-account", Component: ManagerAccountCreation },

  /* Dashboard shell */
  {
    path: "/",
    Component: DashboardLayout,
    children: [
      { index: true, Component: Dashboard },
      { path: "analytics", Component: Analytics },
      { path: "campaigns", Component: Campaigns },
      { path: "campaigns/:id", Component: CampaignDetail },
      { path: "callers", Component: Callers },
      { path: "employees", Component: Employees },
      { path: "employees/:id", Component: EmployeeDetail },
      { path: "calls", Component: Calls },
      { path: "monitoring", Component: CallMonitoring },
      { path: "*", Component: NotFound },
    ],
  },
]);
