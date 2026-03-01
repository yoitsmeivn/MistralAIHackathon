import { Link } from "react-router";
import { TrendingUp, TrendingDown, Tag } from "lucide-react";
import { Badge } from "../ui/badge";
import type { RecentFailuresWidget } from "../../types";

interface Props {
  data: RecentFailuresWidget;
}

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

export function RecentFailuresPanel({ data }: Props) {
  const TrendIcon = data.trend === "up" ? TrendingUp : data.trend === "down" ? TrendingDown : null;

  return (
    <div className="space-y-6">
      {/* KPI boxes */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-red-500">{data.failures7d}</p>
          <p className="text-[11px] text-muted-foreground">Last 7 days</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{data.failures30d}</p>
          <p className="text-[11px] text-muted-foreground">Last 30 days</p>
        </div>
        <div className="rounded-lg border p-3 text-center flex flex-col items-center justify-center">
          {TrendIcon && (
            <TrendIcon
              className={`w-5 h-5 ${data.trend === "up" ? "text-red-500" : "text-green-500"}`}
            />
          )}
          <p className="text-[11px] text-muted-foreground mt-1">
            {data.trend === "up" ? "Increasing" : data.trend === "down" ? "Decreasing" : "Stable"}
          </p>
        </div>
      </div>

      {/* Most common flag */}
      {data.mostCommonFlag && (
        <div className="rounded-lg border p-3 bg-red-50/50">
          <div className="flex items-center gap-2 mb-1">
            <Tag className="w-3.5 h-3.5 text-red-400" />
            <span className="text-[11px] text-muted-foreground uppercase tracking-wide">Top Failure Pattern</span>
          </div>
          <Badge variant="outline" className="border-red-200 text-red-600 bg-white text-xs">
            {data.mostCommonFlag}
          </Badge>
        </div>
      )}

      {/* Recent failures list */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-2">Recent Failures</p>
        <div className="space-y-1 max-h-[360px] overflow-y-auto">
          {data.recentFailures.map((failure) => (
            <Link
              key={failure.callId}
              to={`/employees/${failure.employeeId}`}
              className="flex items-center justify-between p-2.5 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-muted"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{failure.employeeName}</p>
                <p className="text-[11px] text-muted-foreground">
                  {failure.department} · {failure.attackVector}
                </p>
                {failure.flags.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {failure.flags.slice(0, 2).map((flag) => (
                      <Badge key={flag} variant="outline" className="text-[10px] px-1 py-0 border-red-200 text-red-500">
                        {flag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="text-right shrink-0 ml-3">
                <span className="text-sm font-medium" style={{ color: getRiskColor(failure.riskScore) }}>
                  {failure.riskScore}
                </span>
                <p className="text-[10px] text-muted-foreground">
                  {failure.occurredAt ? new Date(failure.occurredAt).toLocaleDateString() : ""}
                </p>
              </div>
            </Link>
          ))}
          {data.recentFailures.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No recent failures</p>
          )}
        </div>
      </div>
    </div>
  );
}
