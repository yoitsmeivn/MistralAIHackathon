import type {
  Caller,
  Call,
  Campaign,
  Employee,
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
} from "../types";

// Hardcoded org for hackathon demo
const ORG_ID = "00000000-0000-0000-0000-000000000001";

// ─── Helpers ─────────────────────────────────────────────────────────

async function apiFetch<T>(path: string): Promise<T> {
  const sep = path.includes("?") ? "&" : "?";
  const url = `${path}${sep}org_id=${ORG_ID}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
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

// ─── Callers ────────────────────────────────────────────────────────

export async function getCallers(): Promise<Caller[]> {
  return apiFetch<Caller[]>("/api/callers/");
}

// ─── Employees ──────────────────────────────────────────────────────

export async function getEmployees(): Promise<Employee[]> {
  return apiFetch<Employee[]>("/api/employees/");
}

// ─── Calls ──────────────────────────────────────────────────────────

export async function getCalls(): Promise<Call[]> {
  return apiFetch<Call[]>("/api/calls/");
}

export async function getCampaignCalls(campaignId: string): Promise<Call[]> {
  return apiFetch<Call[]>(`/api/calls/?campaign_id=${campaignId}`);
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
