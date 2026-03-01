// ─── Status & Enum Types ─────────────────────────────────────────────

export type CampaignStatus = "draft" | "active" | "paused" | "completed";
export type CallStatus = "pending" | "in_progress" | "completed" | "failed";
export type EmployeeCompliance = "passed" | "failed" | "partial";
export type RiskLevel = "low" | "medium" | "high" | "unknown";

export type AttackVector =
  | "Technical Support Scam"
  | "Authority Impersonation"
  | "Urgency & Fear"
  | "Internal Authority"
  | "Financial Scam"
  | "Prize/Reward";

// ─── Entity Types ────────────────────────────────────────────────────

export interface Organization {
  id: string;
  name: string;
  slug: string;
  industry?: string;
  planTier: string;
  maxEmployees: number;
  maxCallers: number;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  orgId: string;
  email: string;
  fullName: string;
  role: string;
  isActive: boolean;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Caller {
  id: string;
  personaName: string;
  personaRole: string;
  personaCompany: string;
  phoneNumber: string;
  attackType: AttackVector | string;
  description: string;
  isActive: boolean;
  totalCalls: number;
  avgSuccessRate: number;
  createdAt?: string;
}

export interface Employee {
  id: string;
  fullName: string;
  email: string;
  phone: string;
  department: string;
  jobTitle: string;
  riskLevel: RiskLevel;
  totalTests: number;
  failedTests: number;
  lastTestDate: string;
  isActive: boolean;
}

export interface Campaign {
  id: string;
  name: string;
  description: string;
  attackVector: AttackVector | string;
  status: CampaignStatus;
  scheduledAt: string;
  startedAt?: string;
  completedAt?: string;
  totalCalls: number;
  completedCalls: number;
  avgRiskScore: number;
  createdAt: string;
}

export interface Call {
  id: string;
  employeeName: string;
  callerName: string;
  campaignName: string;
  status: CallStatus;
  startedAt: string;
  duration: string;
  durationSeconds?: number;
  riskScore: number;
  employeeCompliance: EmployeeCompliance;
  transcript: string;
  flags: string[];
  aiSummary?: string;
}

// ─── Dashboard aggregates ────────────────────────────────────────────

export interface DashboardStat {
  label: string;
  value: string;
  change: string;
  trend: "up" | "down" | "neutral";
}

export interface RiskDistribution {
  name: string;
  value: number;
  fill: string;
}

export interface CallsOverTime {
  date: string;
  calls: number;
  passed: number;
  failed: number;
}

// ─── Analytics types ────────────────────────────────────────────────

export interface RiskTrendPoint {
  date: string;
  avgRisk: number;
  callCount: number;
}

export interface DepartmentTrendPoint {
  date: string;
  department: string;
  totalCalls: number;
  failedCalls: number;
  failureRate: number;
}

export interface RepeatOffender {
  employeeId: string;
  employeeName: string;
  department: string;
  totalTests: number;
  failedTests: number;
  failureRate: number;
  mostRecentFailure: string;
  commonFlags: string[];
  riskScores: number[];
}

export interface CampaignEffectivenessItem {
  campaignId: string;
  campaignName: string;
  attackVector: string;
  totalCalls: number;
  failedCalls: number;
  passedCalls: number;
  partialCalls: number;
  failureRate: number;
  avgRiskScore: number;
  avgDurationSeconds: number;
}

export interface AttackVectorSummary {
  attackVector: string;
  totalCalls: number;
  failureRate: number;
  avgRiskScore: number;
}

export interface CampaignEffectivenessData {
  campaigns: CampaignEffectivenessItem[];
  byAttackVector: AttackVectorSummary[];
}

export interface FlagFrequency {
  flag: string;
  count: number;
  percentage: number;
  isPositive: boolean;
}

export interface HeatmapCell {
  attackVector: string;
  department: string;
  totalCalls: number;
  failureRate: number;
  avgRiskScore: number;
}

export interface EmployeeCallHistoryItem {
  id: string;
  campaignName: string;
  callerName: string;
  attackVector: string;
  status: string;
  startedAt: string;
  duration: string;
  durationSeconds?: number;
  riskScore: number;
  employeeCompliance: string;
  flags: string[];
  aiSummary: string;
}

export interface EmployeeAnalytics {
  id: string;
  fullName: string;
  email: string;
  phone: string;
  department: string;
  jobTitle: string;
  riskLevel: string;
  isActive: boolean;
  totalTests: number;
  passedTests: number;
  failedTests: number;
  partialTests: number;
  failureRate: number;
  avgRiskScore: number;
  riskScoreTrend: number[];
  riskScoreDates: string[];
  complianceBreakdown: Record<string, number>;
  flagSummary: FlagFrequency[];
  calls: EmployeeCallHistoryItem[];
}
