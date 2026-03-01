import { useState, useEffect } from "react";
import { Link } from "react-router";
import {
  PhoneCall,
  Users,
  UserCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  ShieldAlert,
  XCircle,
  Activity,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { motion } from "motion/react";
import { Card, CardContent, CardHeader, CardTitle, CardAction } from "./ui/card";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "./ui/sheet";
import { RiskHotspotPanel } from "./dashboard/RiskHotspotPanel";
import { RecentFailuresPanel } from "./dashboard/RecentFailuresPanel";
import { CampaignPulsePanel } from "./dashboard/CampaignPulsePanel";
import type {
  DashboardStat,
  RiskDistribution,
  CallsOverTime,
  Campaign,
  Employee,
  SmartWidgetsData,
} from "../types";
import {
  getDashboardStats,
  getRiskDistribution,
  getRiskByDepartment,
  getCallsOverTime,
  getCampaigns,
  getEmployees,
  getSmartWidgets,
} from "../services/api";

const statIcons = [PhoneCall, PhoneCall, Users, AlertTriangle];

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStat[]>([]);
  const [riskDist, setRiskDist] = useState<RiskDistribution[]>([]);
  const [riskByDept, setRiskByDept] = useState<RiskDistribution[]>([]);
  const [riskPivot, setRiskPivot] = useState<"level" | "department">("level");
  const [callsTime, setCallsTime] = useState<CallsOverTime[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [widgets, setWidgets] = useState<SmartWidgetsData | null>(null);
  const [activePanel, setActivePanel] = useState<"risk" | "failures" | "campaigns" | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getDashboardStats(),
      getRiskDistribution(),
      getRiskByDepartment(),
      getCallsOverTime(),
      getCampaigns(),
      getEmployees(),
      getSmartWidgets(),
    ]).then(([s, r, rd, c, camp, emp, w]) => {
      setStats(s);
      setRiskDist(r);
      setRiskByDept(rd);
      setCallsTime(c);
      setCampaigns(camp.filter((c) => c.status !== "draft").slice(0, 3));
      setEmployees(
        emp
          .filter((e) => e.riskLevel === "high" || e.riskLevel === "medium")
          .sort((a, b) => b.failedTests - a.failedTests)
          .slice(0, 3)
      );
      setWidgets(w);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="p-8 max-w-7xl space-y-6">
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-72 rounded-xl" />
          <Skeleton className="h-72 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div className="mb-8" variants={item}>
        <h1 className="text-2xl font-medium mb-1 text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Monitor your vishing security testing campaigns
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat, i) => {
          const IconComponent = statIcons[i] || PhoneCall;
          const TrendIcon =
            stat.trend === "up"
              ? TrendingUp
              : stat.trend === "down"
                ? TrendingDown
                : null;
          return (
            <motion.div key={stat.label} variants={item}>
              <Card className="hover:shadow-md transition-shadow">
                <CardContent className="pt-5 pb-5">
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: "#fdfbe1" }}
                    >
                      <IconComponent className="w-4 h-4 text-foreground" />
                    </div>
                    {TrendIcon && (
                      <TrendIcon
                        className={`w-4 h-4 ${stat.trend === "up" ? "text-emerald-500" : "text-red-500"}`}
                      />
                    )}
                  </div>
                  <p className="text-2xl font-medium text-foreground mb-0.5">
                    {stat.value}
                  </p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-xs text-muted-foreground/60 mt-1">
                    {stat.change}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Smart Widget Cards */}
      {widgets && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
          <motion.div variants={item}>
            <Card
              className="cursor-pointer hover:shadow-md hover:border-red-200 transition-all"
              onClick={() => setActivePanel("risk")}
            >
              <CardContent className="pt-5 pb-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center">
                    <ShieldAlert className="w-4 h-4 text-red-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground">Risk Hotspots</p>
                    <p className="text-lg font-medium" style={{ color: widgets.riskHotspot.overallRisk >= 50 ? "#ef4444" : "#f59e0b" }}>
                      {widgets.riskHotspot.overallRisk}
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  Worst: {widgets.riskHotspot.worstDepartment || "N/A"} · Click to drill down
                </p>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={item}>
            <Card
              className="cursor-pointer hover:shadow-md hover:border-amber-200 transition-all"
              onClick={() => setActivePanel("failures")}
            >
              <CardContent className="pt-5 pb-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
                    <XCircle className="w-4 h-4 text-amber-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground">Recent Failures</p>
                    <p className="text-lg font-medium text-foreground">
                      {widgets.recentFailures.failures7d}
                      <span className="text-xs text-muted-foreground font-normal ml-1">last 7d</span>
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {widgets.recentFailures.mostCommonFlag ? `Top: ${widgets.recentFailures.mostCommonFlag}` : "No failures"} · Click to drill down
                </p>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={item}>
            <Card
              className="cursor-pointer hover:shadow-md hover:border-blue-200 transition-all"
              onClick={() => setActivePanel("campaigns")}
            >
              <CardContent className="pt-5 pb-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
                    <Activity className="w-4 h-4 text-blue-500" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-muted-foreground">Campaign Pulse</p>
                    <p className="text-lg font-medium text-foreground">
                      {widgets.campaignPulse.activeCount}
                      <span className="text-xs text-muted-foreground font-normal ml-1">active</span>
                    </p>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {widgets.campaignPulse.completionRate}% completion · Click to drill down
                </p>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
        {/* Calls Over Time */}
        <motion.div className="lg:col-span-3" variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Calls Over Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={callsTime}>
                    <defs>
                      <linearGradient
                        id="gradFailed"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#ef4444"
                          stopOpacity={0.2}
                        />
                        <stop
                          offset="95%"
                          stopColor="#ef4444"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient
                        id="gradPassed"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#22c55e"
                          stopOpacity={0.2}
                        />
                        <stop
                          offset="95%"
                          stopColor="#22c55e"
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
                      tick={{ fill: "#868e96", fontSize: 12 }}
                      dy={8}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#868e96", fontSize: 12 }}
                    />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "8px",
                        border: "none",
                        boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                        fontSize: 13,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="failed"
                      stroke="#ef4444"
                      strokeWidth={2}
                      fill="url(#gradFailed)"
                      name="Failed"
                    />
                    <Area
                      type="monotone"
                      dataKey="passed"
                      stroke="#22c55e"
                      strokeWidth={2}
                      fill="url(#gradPassed)"
                      name="Passed"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Risk Distribution */}
        <motion.div className="lg:col-span-2" variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Risk Distribution
              </CardTitle>
              <CardAction>
                <div className="flex rounded-lg bg-muted p-0.5">
                  <button
                    onClick={() => setRiskPivot("level")}
                    className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                      riskPivot === "level"
                        ? "bg-background text-foreground shadow-sm font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    Risk Level
                  </button>
                  <button
                    onClick={() => setRiskPivot("department")}
                    className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                      riskPivot === "department"
                        ? "bg-background text-foreground shadow-sm font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    Department
                  </button>
                </div>
              </CardAction>
            </CardHeader>
            <CardContent>
              <div className="h-40 mb-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPivot === "level" ? riskDist : riskByDept}
                      innerRadius={45}
                      outerRadius={65}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {(riskPivot === "level" ? riskDist : riskByDept).map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        borderRadius: "8px",
                        border: "none",
                        boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                        fontSize: 13,
                      }}
                      formatter={(value: number) => [
                        `${value}%`,
                        riskPivot === "department" ? "Fail Rate" : "",
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-3 justify-center">
                {(riskPivot === "level" ? riskDist : riskByDept).map((r) => (
                  <div
                    key={r.name}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground"
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: r.fill }}
                    />
                    {r.name}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Campaigns */}
        <motion.div variants={item}>
          <Card>
            <CardHeader className="border-b">
              <CardTitle className="text-sm font-medium">
                Recent Campaigns
              </CardTitle>
              <CardAction>
                <Link
                  to="/campaigns"
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  View all <ArrowRight className="w-3 h-3" />
                </Link>
              </CardAction>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="space-y-1">
                {campaigns.map((campaign) => (
                  <Link
                    key={campaign.id}
                    to={`/campaigns/${campaign.id}`}
                    className="flex items-center justify-between p-3 rounded-lg transition-colors hover:bg-muted/50 group"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm truncate text-foreground">
                          {campaign.name}
                        </p>
                        <Badge
                          variant={
                            campaign.status === "active"
                              ? "secondary"
                              : "outline"
                          }
                          className="text-[10px] px-1.5 py-0"
                        >
                          {campaign.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {campaign.completedCalls} calls ·{" "}
                        {new Date(campaign.scheduledAt).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="ml-4 text-right">
                      <p
                        className="text-sm font-medium"
                        style={{
                          color: getRiskColor(campaign.avgRiskScore),
                        }}
                      >
                        {campaign.avgRiskScore}%
                      </p>
                      <p className="text-xs text-muted-foreground">risk</p>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* High Risk Employees */}
        <motion.div variants={item}>
          <Card>
            <CardHeader className="border-b">
              <CardTitle className="text-sm font-medium">
                High Risk Employees
              </CardTitle>
              <CardAction>
                <Link
                  to="/employees"
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  View all <ArrowRight className="w-3 h-3" />
                </Link>
              </CardAction>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="space-y-1">
                {employees.map((employee, index) => (
                  <div
                    key={employee.id}
                    className={`flex items-center gap-3 p-3 rounded-lg ${index === 0 ? "bg-red-50/60" : ""}`}
                  >
                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-muted">
                      <UserCircle className="w-5 h-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate text-foreground">
                        {employee.fullName}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {employee.department} · {employee.lastTestDate}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <Badge
                        className="text-xs border-0"
                        style={{
                          backgroundColor:
                            employee.riskLevel === "high"
                              ? "#fef2f2"
                              : "#fffbeb",
                          color:
                            employee.riskLevel === "high"
                              ? "#ef4444"
                              : "#f59e0b",
                        }}
                      >
                        {employee.riskLevel}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Drill-down Sheet */}
      <Sheet open={activePanel !== null} onOpenChange={(open) => !open && setActivePanel(null)}>
        <SheetContent side="right" className="sm:max-w-md overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              {activePanel === "risk" && "Risk Hotspots"}
              {activePanel === "failures" && "Recent Failures"}
              {activePanel === "campaigns" && "Campaign Pulse"}
            </SheetTitle>
            <SheetDescription>
              {activePanel === "risk" && "Deep dive into organizational risk distribution"}
              {activePanel === "failures" && "Investigate recent security test failures"}
              {activePanel === "campaigns" && "Monitor active campaign progress"}
            </SheetDescription>
          </SheetHeader>
          {widgets && activePanel === "risk" && <RiskHotspotPanel data={widgets.riskHotspot} />}
          {widgets && activePanel === "failures" && <RecentFailuresPanel data={widgets.recentFailures} />}
          {widgets && activePanel === "campaigns" && <CampaignPulsePanel data={widgets.campaignPulse} />}
        </SheetContent>
      </Sheet>
    </motion.div>
  );
}
