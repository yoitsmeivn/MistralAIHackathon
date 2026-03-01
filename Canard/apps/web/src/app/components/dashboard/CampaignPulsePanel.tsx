import { Link } from "react-router";
import { Trophy, AlertCircle } from "lucide-react";
import { Badge } from "../ui/badge";
import type { CampaignPulseWidget } from "../../types";

interface Props {
  data: CampaignPulseWidget;
}

export function CampaignPulsePanel({ data }: Props) {
  return (
    <div className="space-y-6">
      {/* KPI boxes */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{data.activeCount}</p>
          <p className="text-[11px] text-muted-foreground">Active</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{data.completionRate}%</p>
          <p className="text-[11px] text-muted-foreground">Completion</p>
        </div>
        <div className="rounded-lg border p-3 text-center">
          <p className="text-2xl font-bold text-foreground">{data.campaigns.length}</p>
          <p className="text-[11px] text-muted-foreground">Total</p>
        </div>
      </div>

      {/* Best / Worst */}
      <div className="grid grid-cols-2 gap-3">
        {data.bestPerforming && (
          <div className="rounded-lg border p-3 bg-green-50/50">
            <div className="flex items-center gap-2 mb-1">
              <Trophy className="w-3.5 h-3.5 text-green-500" />
              <span className="text-[11px] text-muted-foreground uppercase tracking-wide">Best</span>
            </div>
            <p className="text-sm font-medium truncate">{data.bestPerforming}</p>
          </div>
        )}
        {data.worstPerforming && (
          <div className="rounded-lg border p-3 bg-red-50/50">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-3.5 h-3.5 text-red-400" />
              <span className="text-[11px] text-muted-foreground uppercase tracking-wide">Worst</span>
            </div>
            <p className="text-sm font-medium truncate">{data.worstPerforming}</p>
          </div>
        )}
      </div>

      {/* Campaign table */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-2">All Campaigns</p>
        <div className="space-y-1.5">
          {data.campaigns.map((camp) => {
            const progress =
              camp.totalCalls > 0
                ? Math.round((camp.completedCalls / camp.totalCalls) * 100)
                : 0;
            return (
              <Link
                key={camp.id}
                to={`/campaigns/${camp.id}`}
                className="block p-2.5 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-muted"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-sm font-medium truncate flex-1">{camp.name}</p>
                  <Badge variant="outline" className="text-[10px] ml-2 shrink-0">
                    {camp.attackVector}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-1.5">
                  <span>{camp.completedCalls}/{camp.totalCalls} calls</span>
                  <span>Fail: {camp.failureRate}%</span>
                  <span>Risk: {camp.avgRisk}</span>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${progress}%`,
                      backgroundColor: camp.failureRate >= 50 ? "#ef4444" : camp.failureRate >= 25 ? "#f59e0b" : "#22c55e",
                    }}
                  />
                </div>
              </Link>
            );
          })}
          {data.campaigns.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No campaigns</p>
          )}
        </div>
      </div>
    </div>
  );
}
