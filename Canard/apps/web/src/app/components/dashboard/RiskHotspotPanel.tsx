import { Link } from "react-router";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { AlertTriangle, Building2, Crosshair } from "lucide-react";
import { Badge } from "../ui/badge";
import type { RiskHotspotWidget } from "../../types";

interface Props {
  data: RiskHotspotWidget;
}

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

export function RiskHotspotPanel({ data }: Props) {
  const chartData = data.deptBreakdown.map((d) => ({
    name: d.department,
    risk: d.avgRisk,
  }));

  return (
    <div className="space-y-6">
      {/* Hero stat */}
      <div className="flex items-center gap-4">
        <div className="text-5xl font-bold" style={{ color: getRiskColor(data.overallRisk) }}>
          {data.overallRisk}
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Overall Risk Score</p>
          <Badge
            variant="outline"
            className={`text-xs mt-1 ${
              data.riskTrend === "up"
                ? "border-red-200 text-red-600 bg-red-50"
                : data.riskTrend === "down"
                  ? "border-green-200 text-green-600 bg-green-50"
                  : "border-muted text-muted-foreground"
            }`}
          >
            {data.riskTrend === "up" ? "Trending Up" : data.riskTrend === "down" ? "Improving" : "Stable"}
          </Badge>
        </div>
      </div>

      {/* Callout cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border p-3 bg-muted/30">
          <div className="flex items-center gap-2 mb-1">
            <Building2 className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-[11px] text-muted-foreground uppercase tracking-wide">Worst Department</span>
          </div>
          <p className="text-sm font-medium truncate">{data.worstDepartment || "N/A"}</p>
        </div>
        <div className="rounded-lg border p-3 bg-muted/30">
          <div className="flex items-center gap-2 mb-1">
            <Crosshair className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-[11px] text-muted-foreground uppercase tracking-wide">Worst Vector</span>
          </div>
          <p className="text-sm font-medium truncate">{data.worstAttackVector || "N/A"}</p>
        </div>
      </div>

      {/* Dept risk chart */}
      {chartData.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">Department Risk Scores</p>
          <div className="h-36">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 0 }}>
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={80}
                  tick={{ fontSize: 11, fill: "#868e96" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "8px",
                    border: "none",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                    fontSize: 12,
                  }}
                  formatter={(v: number) => [`${v}`, "Avg Risk"]}
                />
                <Bar dataKey="risk" radius={[0, 4, 4, 0]} fill="#f59e0b" barSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Top risk employees */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-2">Top Risk Employees</p>
        <div className="space-y-1">
          {data.topRiskEmployees.map((emp) => (
            <Link
              key={emp.id}
              to={`/employees/${emp.id}`}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-2 min-w-0">
                <AlertTriangle
                  className="w-3.5 h-3.5 shrink-0"
                  style={{ color: getRiskColor(emp.riskScore) }}
                />
                <div className="min-w-0">
                  <p className="text-sm truncate">{emp.fullName}</p>
                  <p className="text-[11px] text-muted-foreground">{emp.department}</p>
                </div>
              </div>
              <div className="text-right shrink-0 ml-2">
                <span className="text-sm font-medium" style={{ color: getRiskColor(emp.riskScore) }}>
                  {emp.riskScore}
                </span>
                {emp.recentFlags.length > 0 && (
                  <p className="text-[10px] text-muted-foreground truncate max-w-[120px]">
                    {emp.recentFlags[0]}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
