import type {
  Caller,
  Call,
  Campaign,
  Employee,
  DashboardStat,
  RiskDistribution,
  CallsOverTime,
} from "../types";

// ─── Mock Data ───────────────────────────────────────────────────────

const campaigns: Campaign[] = [
  {
    id: "1",
    name: "IT Support Impersonation",
    description: "Test employee response to fake IT support requests for credentials",
    attackVector: "Technical Support Scam",
    status: "active",
    scheduledAt: "2026-02-28T09:00:00",
    startedAt: "2026-02-28T09:05:00",
    totalCalls: 50,
    completedCalls: 45,
    avgRiskScore: 72,
    createdAt: "2026-02-20T10:00:00",
  },
  {
    id: "2",
    name: "CEO Fraud Test",
    description: "Impersonate CEO requesting urgent wire transfer",
    attackVector: "Authority Impersonation",
    status: "active",
    scheduledAt: "2026-02-27T14:00:00",
    startedAt: "2026-02-27T14:10:00",
    totalCalls: 40,
    completedCalls: 32,
    avgRiskScore: 58,
    createdAt: "2026-02-22T11:30:00",
  },
  {
    id: "3",
    name: "Bank Security Alert",
    description: "Fake security alert from employee's bank",
    attackVector: "Urgency & Fear",
    status: "completed",
    scheduledAt: "2026-02-20T10:00:00",
    startedAt: "2026-02-20T10:02:00",
    completedAt: "2026-02-21T18:00:00",
    totalCalls: 67,
    completedCalls: 67,
    avgRiskScore: 81,
    createdAt: "2026-02-15T09:00:00",
  },
  {
    id: "4",
    name: "HR Benefits Update",
    description: "Test response to fake HR calls about benefits verification",
    attackVector: "Internal Authority",
    status: "draft",
    scheduledAt: "2026-03-05T09:00:00",
    totalCalls: 30,
    completedCalls: 0,
    avgRiskScore: 0,
    createdAt: "2026-02-26T15:00:00",
  },
];

const callers: Caller[] = [
  {
    id: "1",
    personaName: "John Mitchell",
    personaRole: "IT Support Technician",
    personaCompany: "TechSupport Solutions",
    phoneNumber: "+1 (555) 123-4567",
    attackType: "Technical Support Scam",
    description: "Poses as IT support requesting password resets and remote access",
    isActive: true,
    totalCalls: 156,
    avgSuccessRate: 72,
  },
  {
    id: "2",
    personaName: "Robert Chen",
    personaRole: "Chief Executive Officer",
    personaCompany: "Executive Office",
    phoneNumber: "+1 (555) 234-5678",
    attackType: "Authority Impersonation",
    description: "Impersonates CEO requesting urgent wire transfers",
    isActive: true,
    totalCalls: 89,
    avgSuccessRate: 58,
  },
  {
    id: "3",
    personaName: "Amanda Stevens",
    personaRole: "Security Specialist",
    personaCompany: "First National Bank",
    phoneNumber: "+1 (555) 345-6789",
    attackType: "Urgency & Fear",
    description: "Creates urgency by claiming account security breach",
    isActive: true,
    totalCalls: 124,
    avgSuccessRate: 81,
  },
  {
    id: "4",
    personaName: "David Wilson",
    personaRole: "HR Benefits Manager",
    personaCompany: "Human Resources",
    phoneNumber: "+1 (555) 456-7890",
    attackType: "Internal Authority",
    description: "Requests personal information for benefits verification",
    isActive: false,
    totalCalls: 45,
    avgSuccessRate: 63,
  },
];

const employees: Employee[] = [
  { id: "1", fullName: "Sarah Johnson", email: "sarah.johnson@company.com", phone: "+1 (555) 111-2222", department: "Finance", jobTitle: "Financial Analyst", riskLevel: "high", totalTests: 8, failedTests: 7, lastTestDate: "Feb 25, 2026", isActive: true },
  { id: "2", fullName: "Michael Chen", email: "michael.chen@company.com", phone: "+1 (555) 222-3333", department: "HR", jobTitle: "HR Manager", riskLevel: "high", totalTests: 6, failedTests: 5, lastTestDate: "Feb 24, 2026", isActive: true },
  { id: "3", fullName: "Emily Rodriguez", email: "emily.rodriguez@company.com", phone: "+1 (555) 333-4444", department: "Sales", jobTitle: "Sales Representative", riskLevel: "medium", totalTests: 5, failedTests: 4, lastTestDate: "Feb 26, 2026", isActive: true },
  { id: "4", fullName: "David Kim", email: "david.kim@company.com", phone: "+1 (555) 444-5555", department: "Engineering", jobTitle: "Software Engineer", riskLevel: "low", totalTests: 7, failedTests: 2, lastTestDate: "Feb 23, 2026", isActive: true },
  { id: "5", fullName: "Lisa Anderson", email: "lisa.anderson@company.com", phone: "+1 (555) 555-6666", department: "Marketing", jobTitle: "Marketing Director", riskLevel: "high", totalTests: 9, failedTests: 8, lastTestDate: "Feb 27, 2026", isActive: true },
];

const calls: Call[] = [
  { id: "1", employeeName: "Sarah Johnson", callerName: "John Mitchell", campaignName: "IT Support Impersonation", status: "completed", startedAt: "Feb 28, 09:15", duration: "3:45", riskScore: 89, employeeCompliance: "failed", transcript: "Employee shared their password and provided remote access credentials without proper verification.", flags: ["Password Shared", "No Verification", "Remote Access Granted"] },
  { id: "2", employeeName: "Michael Chen", callerName: "Robert Chen", campaignName: "CEO Fraud Test", status: "completed", startedAt: "Feb 28, 09:30", duration: "2:20", riskScore: 45, employeeCompliance: "passed", transcript: "Employee properly verified the caller's identity and followed proper authorization procedures before acting.", flags: ["Proper Verification"] },
  { id: "3", employeeName: "Emily Rodriguez", callerName: "Amanda Stevens", campaignName: "Bank Security Alert", status: "completed", startedAt: "Feb 28, 09:45", duration: "4:12", riskScore: 78, employeeCompliance: "failed", transcript: "Employee became anxious under pressure and shared personal information including SSN last 4 digits.", flags: ["Personal Info Shared", "High Anxiety", "No Callback Verification"] },
  { id: "4", employeeName: "David Kim", callerName: "John Mitchell", campaignName: "IT Support Impersonation", status: "completed", startedAt: "Feb 28, 10:00", duration: "1:55", riskScore: 32, employeeCompliance: "passed", transcript: "Employee questioned the request, asked for ticket number, and verified through official channels.", flags: ["Proper Verification", "Asked Questions"] },
  { id: "5", employeeName: "Lisa Anderson", callerName: "Amanda Stevens", campaignName: "Bank Security Alert", status: "completed", startedAt: "Feb 28, 10:15", duration: "5:30", riskScore: 92, employeeCompliance: "failed", transcript: "Employee panicked and provided full credit card details, security code, and online banking credentials.", flags: ["Credit Card Shared", "Banking Credentials", "Extreme Risk", "No Verification"] },
];

// ─── Helpers ─────────────────────────────────────────────────────────

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms));

// ─── API Functions ───────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStat[]> {
  await delay();
  return [
    { label: "Active Campaigns", value: "3", change: "+2 this week", trend: "up" },
    { label: "Total Calls", value: "247", change: "+18 today", trend: "up" },
    { label: "Employees Tested", value: "89", change: "of 120 total", trend: "neutral" },
    { label: "Avg Risk Score", value: "67%", change: "+5% vs last month", trend: "down" },
  ];
}

export async function getRiskDistribution(): Promise<RiskDistribution[]> {
  await delay();
  return [
    { name: "High Risk", value: 34, fill: "#ef4444" },
    { name: "Medium Risk", value: 28, fill: "#f59e0b" },
    { name: "Low Risk", value: 27, fill: "#22c55e" },
    { name: "Unknown", value: 11, fill: "#94a3b8" },
  ];
}

export async function getCallsOverTime(): Promise<CallsOverTime[]> {
  await delay();
  return [
    { date: "Feb 22", calls: 12, passed: 4, failed: 8 },
    { date: "Feb 23", calls: 18, passed: 7, failed: 11 },
    { date: "Feb 24", calls: 24, passed: 10, failed: 14 },
    { date: "Feb 25", calls: 31, passed: 12, failed: 19 },
    { date: "Feb 26", calls: 22, passed: 9, failed: 13 },
    { date: "Feb 27", calls: 38, passed: 15, failed: 23 },
    { date: "Feb 28", calls: 45, passed: 17, failed: 28 },
  ];
}

export async function getCampaigns(): Promise<Campaign[]> {
  await delay();
  return [...campaigns];
}

export async function getCampaign(id: string): Promise<Campaign | undefined> {
  await delay();
  return campaigns.find((c) => c.id === id);
}

export async function getCallers(): Promise<Caller[]> {
  await delay();
  return [...callers];
}

export async function getEmployees(): Promise<Employee[]> {
  await delay();
  return [...employees];
}

export async function getCalls(): Promise<Call[]> {
  await delay();
  return [...calls];
}

export async function getCampaignCalls(campaignId: string): Promise<Call[]> {
  await delay();
  const campaign = campaigns.find((c) => c.id === campaignId);
  if (!campaign) return [];
  return calls.filter((c) => c.campaignName === campaign.name);
}

const deptColors = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

export async function getRiskByDepartment(): Promise<RiskDistribution[]> {
  await delay();
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
