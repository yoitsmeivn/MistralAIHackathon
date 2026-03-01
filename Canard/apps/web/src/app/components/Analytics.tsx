import { useState, useEffect } from "react";
import { Link } from "react-router";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import { motion } from "motion/react";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardAction } from "./ui/card";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { HeatmapGrid } from "./analytics/HeatmapGrid";
import { DeptFailurePivot } from "./analytics/DeptFailurePivot";
import type {
  RiskTrendPoint,
  DepartmentTrendPoint,
  RepeatOffender,
  CampaignEffectivenessData,
  FlagFrequency,
  HeatmapCell,
  DeptFlagPivotData,
} from "../types";
import {
  getRiskTrend,
  getDepartmentTrends,
  getRepeatOffenders,
  getCampaignEffectiveness,
  getFlagFrequency,
  getAttackHeatmap,
  getDeptFlagPivot,
} from "../services/api";

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

const COMPLIANCE_COLORS: Record<string, string> = {
  passed: "#22c55e",
  failed: "#ef4444",
  partial: "#f59e0b",
};

const DEPT_COLORS = [
  "#ef4444",
  "#3b82f6",
  "#22c55e",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];

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

// ─── Overview Tab ───────────────────────────────────────────────────

function OverviewTab() {
  const [riskTrend, setRiskTrend] = useState<RiskTrendPoint[]>([]);
  const [flags, setFlags] = useState<FlagFrequency[]>([]);
  const [offenders, setOffenders] = useState<RepeatOffender[]>([]);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getRiskTrend(days),
      getFlagFrequency(),
      getRepeatOffenders(),
    ]).then(([rt, fl, ro]) => {
      setRiskTrend(rt);
      setFlags(fl);
      setOffenders(ro);
      setLoading(false);
    });
  }, [days]);

  // Derive compliance totals from flags data
  const totalCalls = riskTrend.reduce((sum, r) => sum + r.callCount, 0);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-72 rounded-xl" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-72 rounded-xl" />
          <Skeleton className="h-72 rounded-xl" />
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  return (
    <motion.div
      className="space-y-6"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Risk Trend */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Organization Risk Trend
            </CardTitle>
            <CardAction>
              <div className="flex rounded-lg bg-muted p-0.5">
                {[7, 30, 90].map((d) => (
                  <button
                    key={d}
                    onClick={() => setDays(d)}
                    className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                      days === d
                        ? "bg-background text-foreground shadow-sm font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {d}d
                  </button>
                ))}
              </div>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={riskTrend}>
                  <defs>
                    <linearGradient
                      id="gradRisk"
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
                    tick={{ fill: "#868e96", fontSize: 12 }}
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
                    label={{
                      value: "Threshold",
                      position: "right",
                      fill: "#94a3b8",
                      fontSize: 11,
                    }}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [
                      `${value}%`,
                      "Avg Risk",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="avgRisk"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    fill="url(#gradRisk)"
                    name="Avg Risk"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-2">
              {totalCalls} calls over {days} days
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Flags + Compliance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Flag Frequency */}
        <motion.div variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Common Security Failures
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={flags.slice(0, 10)}
                    layout="vertical"
                    margin={{ left: 20 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      horizontal={false}
                      stroke="#e9ecef"
                    />
                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#868e96", fontSize: 12 }}
                    />
                    <YAxis
                      dataKey="flag"
                      type="category"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: "#868e96", fontSize: 11 }}
                      width={140}
                    />
                    <Tooltip
                      contentStyle={tooltipStyle}
                      formatter={(value: number, _: string, entry: { payload: FlagFrequency }) => [
                        `${value} (${entry.payload.percentage}%)`,
                        "Occurrences",
                      ]}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {flags.slice(0, 10).map((f, i) => (
                        <Cell
                          key={i}
                          fill={f.isPositive ? "#22c55e" : "#ef4444"}
                          fillOpacity={0.8}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Overall Compliance Donut */}
        <motion.div variants={item}>
          <Card className="h-full">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Overall Compliance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                // Derive compliance from offenders + risk trend data
                const passedFlags = flags.filter((f) => f.isPositive);
                const failedFlags = flags.filter((f) => !f.isPositive);
                const totalPositive = passedFlags.reduce(
                  (s, f) => s + f.count,
                  0
                );
                const totalNegative = failedFlags.reduce(
                  (s, f) => s + f.count,
                  0
                );
                const compData = [
                  {
                    name: "Positive Behaviors",
                    value: totalPositive,
                    fill: "#22c55e",
                  },
                  {
                    name: "Security Failures",
                    value: totalNegative,
                    fill: "#ef4444",
                  },
                ];
                const total = totalPositive + totalNegative;
                const passRate =
                  total > 0
                    ? Math.round((totalPositive / total) * 100)
                    : 0;
                return (
                  <>
                    <div className="h-48 relative">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={compData}
                            innerRadius={50}
                            outerRadius={70}
                            paddingAngle={4}
                            dataKey="value"
                          >
                            {compData.map((entry, i) => (
                              <Cell key={i} fill={entry.fill} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={tooltipStyle} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="text-center">
                          <p className="text-2xl font-medium text-foreground">
                            {passRate}%
                          </p>
                          <p className="text-[10px] text-muted-foreground">
                            positive
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3 justify-center">
                      {compData.map((r) => (
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
                  </>
                );
              })()}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Repeat Offenders */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="border-b">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              Repeat Offenders
            </CardTitle>
            <CardAction>
              <Badge variant="secondary" className="text-xs">
                {offenders.length} employee{offenders.length !== 1 ? "s" : ""}
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="pt-0">
            {offenders.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">
                No repeat offenders found
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-4">Employee</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Tests</TableHead>
                    <TableHead>Failures</TableHead>
                    <TableHead>Fail Rate</TableHead>
                    <TableHead>Common Flags</TableHead>
                    <TableHead>Trend</TableHead>
                    <TableHead className="w-8" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {offenders.map((o) => (
                    <TableRow key={o.employeeId}>
                      <TableCell className="pl-4">
                        <Link
                          to={`/employees/${o.employeeId}`}
                          className="text-sm font-medium text-foreground hover:underline"
                        >
                          {o.employeeName}
                        </Link>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {o.department}
                      </TableCell>
                      <TableCell className="text-sm">{o.totalTests}</TableCell>
                      <TableCell className="text-sm text-red-500 font-medium">
                        {o.failedTests}
                      </TableCell>
                      <TableCell>
                        <span
                          className="text-sm font-medium"
                          style={{ color: getRiskColor(o.failureRate) }}
                        >
                          {o.failureRate}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 flex-wrap">
                          {o.commonFlags.slice(0, 2).map((f) => (
                            <Badge
                              key={f}
                              variant="outline"
                              className="text-[10px] px-1.5 py-0 border-red-200 text-red-600"
                            >
                              {f}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        {o.riskScores.length > 1 && (
                          <ResponsiveContainer width={80} height={24}>
                            <LineChart data={o.riskScores.map((s) => ({ v: s }))}>
                              <Line
                                type="monotone"
                                dataKey="v"
                                stroke={getRiskColor(
                                  o.riskScores[o.riskScores.length - 1]
                                )}
                                strokeWidth={1.5}
                                dot={false}
                              />
                            </LineChart>
                          </ResponsiveContainer>
                        )}
                      </TableCell>
                      <TableCell>
                        <Link
                          to={`/employees/${o.employeeId}`}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </TableCell>
                    </TableRow>
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

// ─── Campaigns Tab ──────────────────────────────────────────────────

function CampaignsTab() {
  const [data, setData] = useState<CampaignEffectivenessData | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapCell[]>([]);
  const [sortCol, setSortCol] = useState<string>("failureRate");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCampaignEffectiveness(), getAttackHeatmap()]).then(
      ([ce, hm]) => {
        setData(ce);
        setHeatmap(hm);
        setLoading(false);
      }
    );
  }, []);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-56 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
        <Skeleton className="h-64 rounded-xl" />
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

  const sortedCampaigns = [...data.campaigns].sort((a, b) => {
    const aVal = a[sortCol as keyof typeof a] as number;
    const bVal = b[sortCol as keyof typeof b] as number;
    return sortDir === "asc" ? aVal - bVal : bVal - aVal;
  });

  return (
    <motion.div
      className="space-y-6"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Attack Vector Bar Chart */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Attack Vector Effectiveness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.byAttackVector}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e9ecef"
                  />
                  <XAxis
                    dataKey="attackVector"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#868e96", fontSize: 11 }}
                    dy={8}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#868e96", fontSize: 12 }}
                    domain={[0, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number, name: string) => {
                      if (name === "failureRate") return [`${value}%`, "Failure Rate"];
                      return [value, name];
                    }}
                  />
                  <Bar dataKey="failureRate" radius={[4, 4, 0, 0]}>
                    {data.byAttackVector.map((entry, i) => (
                      <Cell
                        key={i}
                        fill={getRiskColor(entry.failureRate)}
                        fillOpacity={0.85}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Heatmap */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Attack Vector vs Department
            </CardTitle>
            <CardAction>
              <span className="text-[10px] text-muted-foreground">
                Cell color = failure rate intensity
              </span>
            </CardAction>
          </CardHeader>
          <CardContent>
            <HeatmapGrid data={heatmap} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Campaign Comparison Table */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="border-b">
            <CardTitle className="text-sm font-medium">
              Campaign Comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-4">Campaign</TableHead>
                  <TableHead>Attack Vector</TableHead>
                  <TableHead
                    className="cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("totalCalls")}
                  >
                    Calls{" "}
                    {sortCol === "totalCalls"
                      ? sortDir === "asc"
                        ? "\u2191"
                        : "\u2193"
                      : ""}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("failureRate")}
                  >
                    Failure Rate{" "}
                    {sortCol === "failureRate"
                      ? sortDir === "asc"
                        ? "\u2191"
                        : "\u2193"
                      : ""}
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("avgRiskScore")}
                  >
                    Avg Risk{" "}
                    {sortCol === "avgRiskScore"
                      ? sortDir === "asc"
                        ? "\u2191"
                        : "\u2193"
                      : ""}
                  </TableHead>
                  <TableHead>Avg Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedCampaigns.map((c) => (
                  <TableRow key={c.campaignId}>
                    <TableCell className="pl-4 font-medium text-sm">
                      {c.campaignName}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {c.attackVector}
                    </TableCell>
                    <TableCell className="text-sm">{c.totalCalls}</TableCell>
                    <TableCell>
                      <span
                        className="text-sm font-medium"
                        style={{ color: getRiskColor(c.failureRate) }}
                      >
                        {c.failureRate}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <span
                        className="text-sm"
                        style={{ color: getRiskColor(c.avgRiskScore) }}
                      >
                        {c.avgRiskScore}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {Math.round(c.avgDurationSeconds / 60)}m{" "}
                      {Math.round(c.avgDurationSeconds % 60)}s
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

// ─── Vulnerabilities Tab ────────────────────────────────────────────

function VulnerabilitiesTab() {
  const [deptTrends, setDeptTrends] = useState<DepartmentTrendPoint[]>([]);
  const [pivotData, setPivotData] = useState<DeptFlagPivotData | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([getDepartmentTrends(days), getDeptFlagPivot()]).then(
      ([dt, pivot]) => {
        setDeptTrends(dt);
        setPivotData(pivot);
        setLoading(false);
      }
    );
  }, [days]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-72 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
    );
  }

  // Transform for multi-line chart: group by date, each dept as a key
  const departments = Array.from(new Set(deptTrends.map((d) => d.department)));
  const dateMap = new Map<string, Record<string, number>>();
  for (const pt of deptTrends) {
    const existing = dateMap.get(pt.date) || {};
    existing[pt.department] = pt.failureRate;
    dateMap.set(pt.date, existing);
  }
  const chartData = Array.from(dateMap.entries()).map(([date, depts]) => ({
    date,
    ...depts,
  }));

  // Department summary cards
  const deptSummary = new Map<
    string,
    { total: number; failed: number }
  >();
  for (const pt of deptTrends) {
    const cur = deptSummary.get(pt.department) || { total: 0, failed: 0 };
    cur.total += pt.totalCalls;
    cur.failed += pt.failedCalls;
    deptSummary.set(pt.department, cur);
  }

  return (
    <motion.div
      className="space-y-6"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Department Trends Line Chart */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Department Failure Rates Over Time
            </CardTitle>
            <CardAction>
              <div className="flex rounded-lg bg-muted p-0.5">
                {[7, 30, 90].map((d) => (
                  <button
                    key={d}
                    onClick={() => setDays(d)}
                    className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
                      days === d
                        ? "bg-background text-foreground shadow-sm font-medium"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {d}d
                  </button>
                ))}
              </div>
            </CardAction>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
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
                    domain={[0, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${value}%`, ""]}
                  />
                  <Legend />
                  {departments.map((dept, i) => (
                    <Line
                      key={dept}
                      type="monotone"
                      dataKey={dept}
                      stroke={DEPT_COLORS[i % DEPT_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                      name={dept}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Department Summary Cards */}
      <motion.div variants={item}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from(deptSummary.entries()).map(
            ([dept, { total, failed }], i) => {
              const failRate =
                total > 0 ? Math.round((failed / total) * 100) : 0;
              const passRate = 100 - failRate;
              const pieData = [
                { name: "Passed", value: passRate, fill: "#22c55e" },
                { name: "Failed", value: failRate, fill: "#ef4444" },
              ];
              return (
                <Card key={dept}>
                  <CardContent className="pt-5 pb-5">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {dept}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {total} tests
                        </p>
                      </div>
                      <div className="w-12 h-12">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={pieData}
                              innerRadius={14}
                              outerRadius={22}
                              paddingAngle={2}
                              dataKey="value"
                              strokeWidth={0}
                            >
                              {pieData.map((entry, j) => (
                                <Cell key={j} fill={entry.fill} />
                              ))}
                            </Pie>
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      <span
                        className="font-medium"
                        style={{ color: getRiskColor(failRate) }}
                      >
                        {failed} failures
                      </span>{" "}
                      out of {total} tests ({failRate}%)
                    </p>
                  </CardContent>
                </Card>
              );
            }
          )}
        </div>
      </motion.div>

      {/* Failure Types by Department Pivot */}
      {pivotData && (
        <motion.div variants={item}>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">
                Failure Types by Department
              </CardTitle>
            </CardHeader>
            <CardContent>
              <DeptFailurePivot data={pivotData} />
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

// ─── Main Analytics Page ────────────────────────────────────────────

export function Analytics() {
  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      <motion.div className="mb-8" variants={item}>
        <h1 className="text-2xl font-medium mb-1 text-foreground">
          Analytics & Reporting
        </h1>
        <p className="text-sm text-muted-foreground">
          Deep-dive into your organization's vishing resilience
        </p>
      </motion.div>

      <motion.div variants={item}>
        <Tabs defaultValue="overview">
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            <TabsTrigger value="vulnerabilities">Vulnerabilities</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab />
          </TabsContent>

          <TabsContent value="campaigns">
            <CampaignsTab />
          </TabsContent>

          <TabsContent value="vulnerabilities">
            <VulnerabilitiesTab />
          </TabsContent>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}
