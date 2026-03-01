import type {
  Caller,
  Call,
  Campaign,
  Employee,
  Script,
  DashboardStat,
  RiskDistribution,
  CallsOverTime,
  RiskTrendPoint,
  DepartmentTrendPoint,
  RepeatOffender,
  CampaignEffectivenessData,
  FlagFrequency,
  HeatmapCell,
  EmployeeAnalytics,
  SmartWidgetsData,
  DeptFlagPivotData,
  HierarchyRiskData,
} from "../types";
import { supabase } from "../lib/supabase";

// ─── Helpers ─────────────────────────────────────────────────────────

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeaders = await getAuthHeaders();
  const res = await fetch(path, {
    ...init,
    headers: { ...authHeaders, ...init?.headers },
  });
  if (res.status === 401) {
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((e: { msg?: string }) => e.msg).join(", ")
      : body.detail;
    throw new Error(detail || `API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// ─── Dashboard ──────────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStat[]> {
  return apiFetch<DashboardStat[]>("/api/dashboard/stats");
}

export async function getRiskDistribution(): Promise<RiskDistribution[]> {
  return apiFetch<RiskDistribution[]>("/api/dashboard/risk-distribution");
}

export async function getRiskByDepartment(): Promise<RiskDistribution[]> {
  return apiFetch<RiskDistribution[]>("/api/dashboard/risk-by-department");
}

export async function getCallsOverTime(): Promise<CallsOverTime[]> {
  return apiFetch<CallsOverTime[]>("/api/dashboard/calls-over-time");
}

// ─── Campaigns ──────────────────────────────────────────────────────

export async function getCampaigns(): Promise<Campaign[]> {
  return apiFetch<Campaign[]>("/api/campaigns/");
}

export async function getCampaign(id: string): Promise<Campaign | undefined> {
  try {
    return await apiFetch<Campaign>(`/api/campaigns/${id}`);
  } catch {
    return undefined;
  }
}

export async function createCampaign(data: {
  name: string;
  description?: string;
  attack_vector?: string;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/campaigns/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateCampaign(
  id: string,
  data: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/campaigns/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteCampaign(id: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/campaigns/${id}`, {
    method: "DELETE",
  });
}

export async function getCampaignScripts(campaignId: string): Promise<Script[]> {
  return apiFetch<Script[]>(`/api/campaigns/${campaignId}/scripts`);
}

export async function launchCampaign(
  campaignId: string,
  data: {
    script_id?: string;
    caller_id?: string;
    department?: string;
    employee_ids?: string[];
  }
): Promise<{ campaign_id: string; status: string; assignment_count: number }> {
  return apiFetch<{ campaign_id: string; status: string; assignment_count: number }>(
    `/api/campaigns/${campaignId}/launch`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  );
}

// ─── Callers ────────────────────────────────────────────────────────

export async function getCallers(): Promise<Caller[]> {
  return apiFetch<Caller[]>("/api/callers/");
}

export async function createCaller(data: {
  persona_name: string;
  persona_role?: string;
  persona_company?: string;
  phone_number?: string;
  attack_type?: string;
  description?: string;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/callers/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteCaller(id: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/callers/${id}`, {
    method: "DELETE",
  });
}

// ─── Scripts ─────────────────────────────────────────────────────────

export async function getScripts(): Promise<Script[]> {
  return apiFetch<Script[]>("/api/scripts/");
}

export async function createScript(data: {
  name: string;
  campaign_id: string;
  attack_type?: string;
  difficulty?: string;
  system_prompt: string;
  objectives?: string[];
  escalation_steps?: string[];
  description?: string;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/scripts/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateScript(
  id: string,
  data: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/scripts/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteScript(id: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/scripts/${id}`, {
    method: "DELETE",
  });
}

// ─── Employees ──────────────────────────────────────────────────────

export async function getEmployees(): Promise<Employee[]> {
  return apiFetch<Employee[]>("/api/employees/");
}

export async function createEmployee(data: {
  full_name: string;
  email: string;
  phone: string;
  department?: string;
  job_title?: string;
}): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>("/api/employees/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function importEmployeesCSV(
  file: File
): Promise<{ created: number; updated: number; errors: string[] }> {
  const formData = new FormData();
  formData.append("file", file);
  const authHeaders = await getAuthHeaders();
  const res = await fetch("/api/employees/import", {
    method: "POST",
    headers: authHeaders,
    body: formData,
  });
  if (res.status === 401) {
    await supabase.auth.signOut();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = Array.isArray(body.detail)
      ? body.detail.map((e: { msg?: string }) => e.msg).join(", ")
      : body.detail;
    throw new Error(detail || `API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// ─── Calls ──────────────────────────────────────────────────────────

export async function getCalls(): Promise<Call[]> {
  return apiFetch<Call[]>("/api/calls/");
}

export async function getCampaignCalls(campaignId: string): Promise<Call[]> {
  return apiFetch<Call[]>(`/api/calls/?campaign_id=${campaignId}`);
}

// ─── User Management ─────────────────────────────────────────────────

export interface OrgUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export async function getOrgUsers(): Promise<OrgUser[]> {
  return apiFetch<OrgUser[]>("/api/auth/users");
}

export async function createOrgUser(data: {
  email: string;
  full_name: string;
}): Promise<OrgUser> {
  return apiFetch<OrgUser>("/api/auth/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function transferAdmin(userId: string): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/api/auth/transfer-admin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_user_id: userId }),
  });
}

export async function deleteAccount(): Promise<{ message: string }> {
  return apiFetch<{ message: string }>("/api/auth/me", {
    method: "DELETE",
  });
}

// ─── Analytics ──────────────────────────────────────────────────────

export async function getRiskTrend(days: number = 30): Promise<RiskTrendPoint[]> {
  return apiFetch<RiskTrendPoint[]>(`/api/analytics/risk-trend?days=${days}`);
}

export async function getDepartmentTrends(days: number = 30): Promise<DepartmentTrendPoint[]> {
  return apiFetch<DepartmentTrendPoint[]>(`/api/analytics/department-trends?days=${days}`);
}

export async function getRepeatOffenders(minFailures: number = 2): Promise<RepeatOffender[]> {
  return apiFetch<RepeatOffender[]>(`/api/analytics/repeat-offenders?min_failures=${minFailures}`);
}

export async function getCampaignEffectiveness(): Promise<CampaignEffectivenessData> {
  return apiFetch<CampaignEffectivenessData>("/api/analytics/campaign-effectiveness");
}

export async function getFlagFrequency(campaignId?: string): Promise<FlagFrequency[]> {
  const extra = campaignId ? `&campaign_id=${campaignId}` : "";
  return apiFetch<FlagFrequency[]>(`/api/analytics/flag-frequency${extra}`);
}

export async function getAttackHeatmap(): Promise<HeatmapCell[]> {
  return apiFetch<HeatmapCell[]>("/api/analytics/attack-heatmap");
}

export async function getEmployeeAnalytics(employeeId: string): Promise<EmployeeAnalytics> {
  return apiFetch<EmployeeAnalytics>(`/api/analytics/employee-detail/${employeeId}`);
}

export async function getSmartWidgets(): Promise<SmartWidgetsData> {
  return apiFetch<SmartWidgetsData>("/api/dashboard/smart-widgets");
}

export async function getDeptFlagPivot(flagType?: string): Promise<DeptFlagPivotData> {
  const extra = flagType ? `&flag_type=${flagType}` : "";
  return apiFetch<DeptFlagPivotData>(`/api/analytics/dept-flag-pivot${extra}`);
}

export async function getHierarchyRisk(employeeId: string): Promise<HierarchyRiskData> {
  return apiFetch<HierarchyRiskData>(`/api/analytics/hierarchy-risk/${employeeId}`);
}

// ─── Derived ────────────────────────────────────────────────────────

const deptColors = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

export async function getRiskByDepartmentLocal(): Promise<RiskDistribution[]> {
  const employees = await getEmployees();
  const deptMap = new Map<string, { failed: number; total: number }>();
  for (const e of employees) {
    const cur = deptMap.get(e.department) || { failed: 0, total: 0 };
    cur.failed += e.failedTests;
    cur.total += e.totalTests;
    deptMap.set(e.department, cur);
  }
  return Array.from(deptMap.entries()).map(([dept, { failed, total }], i) => ({
    name: dept,
    value: total > 0 ? Math.round((failed / total) * 100) : 0,
    fill: deptColors[i % deptColors.length],
  }));
}
