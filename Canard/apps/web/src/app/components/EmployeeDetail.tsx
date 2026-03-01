import { useState, useEffect } from "react";
import { useParams, Link } from "react-router";
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { motion } from "motion/react";
import { ArrowLeft, ChevronDown, ChevronUp, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardAction } from "./ui/card";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { OrgRiskTree } from "./analytics/OrgRiskTree";
import type { EmployeeAnalytics, HierarchyRiskData } from "../types";
import { getEmployeeAnalytics, getHierarchyRisk } from "../services/api";

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

const riskBadgeStyle = (risk: string) => {
  switch (risk) {
    case "high":
    case "critical":
      return { backgroundColor: "#fef2f2", color: "#ef4444" };
    case "medium":
      return { backgroundColor: "#fffbeb", color: "#f59e0b" };
    case "low":
      return { backgroundColor: "#f0fdf4", color: "#22c55e" };
    default:
      return { backgroundColor: "#f4f4f4", color: "#9ca3af" };
  }
};

const complianceBadgeStyle = (c: string) => {
  switch (c) {
    case "passed":
      return { backgroundColor: "#f0fdf4", color: "#22c55e" };
    case "failed":
      return { backgroundColor: "#fef2f2", color: "#ef4444" };
    case "partial":
      return { backgroundColor: "#fffbeb", color: "#f59e0b" };
    default:
      return { backgroundColor: "#f4f4f4", color: "#9ca3af" };
  }
};

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

const tooltipStyle = {
  borderRadius: "8px",
  border: "none",
  boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
  fontSize: 13,
};

const getInitials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

// ─── Risk Score Gauge (SVG) ─────────────────────────────────────────

function RiskGauge({ score }: { score: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color = getRiskColor(score);

  return (
    <div className="relative w-24 h-24">
      <svg
        width="96"
        height="96"
        viewBox="0 0 96 96"
        className="transform -rotate-90"
      >
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke="#e9ecef"
          strokeWidth="6"
        />
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl font-medium" style={{ color }}>
            {score}
          </p>
          <p className="text-[9px] text-muted-foreground">risk</p>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function EmployeeDetail() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<EmployeeAnalytics | null>(null);
  const [hierarchyData, setHierarchyData] = useState<HierarchyRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedCall, setExpandedCall] = useState<string | null>(null);
  const [sortCol, setSortCol] = useState<string>("startedAt");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    if (!id) return;
    Promise.all([
      getEmployeeAnalytics(id),
      getHierarchyRisk(id).catch(() => null),
    ]).then(([d, h]) => {
      setData(d);
      setHierarchyData(h);
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="p-8 max-w-7xl space-y-6">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-32 rounded-xl" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 max-w-7xl">
        <Link
          to="/employees"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Employees
        </Link>
        <p className="text-muted-foreground">Employee not found.</p>
      </div>
    );
  }

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir("desc");
    }
  };

  const sortedCalls = [...data.calls].sort((a, b) => {
    if (sortCol === "startedAt") {
      return sortDir === "asc"
        ? a.startedAt.localeCompare(b.startedAt)
        : b.startedAt.localeCompare(a.startedAt);
    }
    if (sortCol === "riskScore") {
      return sortDir === "asc"
        ? a.riskScore - b.riskScore
        : b.riskScore - a.riskScore;
    }
    return 0;
  });

  const trendData = data.riskScoreTrend.map((score, i) => ({
    date: data.riskScoreDates[i] || `#${i + 1}`,
    score,
  }));

  const complianceData = [
    { name: "Passed", value: data.passedTests, fill: "#22c55e" },
    { name: "Failed", value: data.failedTests, fill: "#ef4444" },
    { name: "Partial", value: data.partialTests, fill: "#f59e0b" },
  ].filter((d) => d.value > 0);

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Back Link */}
      <motion.div variants={item}>
        <Link
          to="/employees"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-6"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Employees
        </Link>
      </motion.div>

      {/* Profile Header */}
      <motion.div variants={item} className="mb-6">
        <Card>
          <CardContent className="pt-6 pb-6">
            <div className="flex items-center gap-6">
              <div
                className="w-14 h-14 rounded-full flex items-center justify-center text-lg shrink-0 font-medium"
                style={{ backgroundColor: "#fdfbe1", color: "#252a39" }}
              >
                {getInitials(data.fullName)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-xl font-medium text-foreground">
                    {data.fullName}
                  </h1>
                  <Badge
                    className="capitalize border-0"
                    style={riskBadgeStyle(data.riskLevel)}
                  >
                    {data.riskLevel} risk
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  {data.jobTitle} &middot; {data.department}
                </p>
                <p className="text-xs text-muted-foreground/60 mt-0.5">
                  {data.email} &middot; {data.phone}
                </p>
              </div>
              <RiskGauge score={Math.round(data.avgRiskScore)} />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Tests", value: String(data.totalTests) },
          {
            label: "Failed Tests",
            value: String(data.failedTests),
            color: "#ef4444",
          },
          {
            label: "Failure Rate",
            value: `${data.failureRate}%`,
            color: getRiskColor(data.failureRate),
          },
          {
            label: "Avg Risk Score",
            value: String(Math.round(data.avgRiskScore)),
            color: getRiskColor(data.avgRiskScore),
          },
        ].map((stat) => (
          <motion.div key={stat.label} variants={item}>
            <Card>
              <CardContent className="pt-5 pb-5">
                <p
                  className="text-2xl font-medium mb-0.5"
                  style={{ color: stat.color || "inherit" }}
                >
                  {stat.value}
                </p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-6">
        {/* Risk Score Trend */}
        <motion.div className="lg:col-span-3" variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Risk Score Over Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-48">
                {trendData.length > 1 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trendData}>
                      <defs>
                        <linearGradient
                          id="gradEmpRisk"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#f59e0b"
                            stopOpacity={0.2}
                          />
                          <stop
                            offset="95%"
                            stopColor="#f59e0b"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        vertical={false}
                        stroke="#e9ecef"
                      />
                      <XAxis
                        dataKey="date"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#868e96", fontSize: 11 }}
                        dy={8}
                      />
                      <YAxis
                        domain={[0, 100]}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#868e96", fontSize: 12 }}
                      />
                      <ReferenceLine
                        y={50}
                        stroke="#94a3b8"
                        strokeDasharray="4 4"
                      />
                      <Tooltip
                        contentStyle={tooltipStyle}
                        formatter={(value: number) => [`${value}`, "Risk Score"]}
                      />
                      <Area
                        type="monotone"
                        dataKey="score"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        fill="url(#gradEmpRisk)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                    Not enough data for trend
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Compliance Breakdown */}
        <motion.div className="lg:col-span-2" variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Compliance Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40 mb-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={complianceData}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {complianceData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-3 justify-center">
                {complianceData.map((r) => (
                  <div
                    key={r.name}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground"
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: r.fill }}
                    />
                    {r.name} ({r.value})
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Flag Summary */}
      {data.flagSummary.length > 0 && (
        <motion.div variants={item} className="mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Security Failure Patterns
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {data.flagSummary.map((f) => (
                  <Badge
                    key={f.flag}
                    variant="outline"
                    className="text-xs px-2 py-1"
                    style={{
                      borderColor: f.isPositive ? "#bbf7d0" : "#fecaca",
                      backgroundColor: f.isPositive ? "#f0fdf4" : "#fef2f2",
                      color: f.isPositive ? "#16a34a" : "#dc2626",
                    }}
                  >
                    {f.flag}
                    <span className="ml-1.5 opacity-60">({f.count})</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Team Risk Overview */}
      {hierarchyData && hierarchyData.totalDownstreamEmployees > 0 && (
        <motion.div variants={item} className="mb-6">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-muted-foreground" />
                <CardTitle className="text-sm font-medium">
                  Team Risk Overview
                </CardTitle>
              </div>
              <CardAction>
                <Badge variant="secondary" className="text-xs">
                  {hierarchyData.totalDownstreamEmployees} report{hierarchyData.totalDownstreamEmployees !== 1 ? "s" : ""}
                </Badge>
              </CardAction>
            </CardHeader>
            <CardContent>
              {/* Mini stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                <div className="rounded-lg border p-2.5 text-center">
                  <p
                    className="text-lg font-medium"
                    style={{ color: getRiskColor(hierarchyData.manager.personalRiskScore) }}
                  >
                    {hierarchyData.manager.personalRiskScore}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Personal Risk</p>
                </div>
                <div className="rounded-lg border p-2.5 text-center">
                  <p
                    className="text-lg font-medium"
                    style={{ color: getRiskColor(hierarchyData.manager.teamRiskScore) }}
                  >
                    {hierarchyData.manager.teamRiskScore}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Team Risk</p>
                </div>
                <div className="rounded-lg border p-2.5 text-center">
                  <p className="text-lg font-medium text-foreground">
                    {hierarchyData.manager.teamTotalTests}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Team Tests</p>
                </div>
                <div className="rounded-lg border p-2.5 text-center">
                  <p className="text-lg font-medium text-red-500">
                    {hierarchyData.manager.teamFailedTests}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Team Failures</p>
                </div>
              </div>

              {/* Org Tree */}
              <OrgRiskTree data={hierarchyData} />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Call History Table */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="border-b">
            <CardTitle className="text-sm font-medium">Call History</CardTitle>
            <CardAction>
              <Badge variant="secondary" className="text-xs">
                {data.calls.length} call{data.calls.length !== 1 ? "s" : ""}
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="pt-0">
            {data.calls.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No call history
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="pl-4 cursor-pointer hover:text-foreground"
                      onClick={() => handleSort("startedAt")}
                    >
                      Date{" "}
                      {sortCol === "startedAt"
                        ? sortDir === "asc"
                          ? "\u2191"
                          : "\u2193"
                        : ""}
                    </TableHead>
                    <TableHead>Campaign</TableHead>
                    <TableHead>Caller</TableHead>
                    <TableHead>Attack Vector</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead
                      className="cursor-pointer hover:text-foreground"
                      onClick={() => handleSort("riskScore")}
                    >
                      Risk{" "}
                      {sortCol === "riskScore"
                        ? sortDir === "asc"
                          ? "\u2191"
                          : "\u2193"
                        : ""}
                    </TableHead>
                    <TableHead>Compliance</TableHead>
                    <TableHead>Flags</TableHead>
                    <TableHead className="w-8" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedCalls.map((call) => (
                    <>
                      <TableRow
                        key={call.id}
                        className="cursor-pointer"
                        onClick={() =>
                          setExpandedCall(
                            expandedCall === call.id ? null : call.id
                          )
                        }
                      >
                        <TableCell className="pl-4 text-sm text-muted-foreground">
                          {call.startedAt
                            ? new Date(call.startedAt).toLocaleDateString()
                            : "-"}
                        </TableCell>
                        <TableCell className="text-sm">
                          {call.campaignName}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {call.callerName}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {call.attackVector}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {call.duration}
                        </TableCell>
                        <TableCell>
                          <span
                            className="text-sm font-medium"
                            style={{ color: getRiskColor(call.riskScore) }}
                          >
                            {call.riskScore}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            className="capitalize border-0 text-xs"
                            style={complianceBadgeStyle(
                              call.employeeCompliance
                            )}
                          >
                            {call.employeeCompliance}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1 flex-wrap max-w-[180px]">
                            {call.flags.slice(0, 2).map((f) => (
                              <Badge
                                key={f}
                                variant="outline"
                                className="text-[10px] px-1 py-0"
                              >
                                {f}
                              </Badge>
                            ))}
                            {call.flags.length > 2 && (
                              <Badge
                                variant="outline"
                                className="text-[10px] px-1 py-0 text-muted-foreground"
                              >
                                +{call.flags.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {expandedCall === call.id ? (
                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                          )}
                        </TableCell>
                      </TableRow>
                      {expandedCall === call.id && call.aiSummary && (
                        <TableRow key={`${call.id}-detail`}>
                          <TableCell
                            colSpan={9}
                            className="pl-4 bg-muted/30"
                          >
                            <div className="py-2">
                              <p className="text-xs font-medium text-muted-foreground mb-1">
                                AI Summary
                              </p>
                              <p className="text-sm text-foreground">
                                {call.aiSummary}
                              </p>
                              {call.flags.length > 0 && (
                                <div className="flex gap-1 flex-wrap mt-2">
                                  {call.flags.map((f) => (
                                    <Badge
                                      key={f}
                                      variant="outline"
                                      className="text-[10px] px-1.5 py-0"
                                    >
                                      {f}
                                    </Badge>
                                  ))}
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
