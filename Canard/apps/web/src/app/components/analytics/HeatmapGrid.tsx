import type { HeatmapCell } from "../../types";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";

interface HeatmapGridProps {
  data: HeatmapCell[];
}

function getCellColor(failureRate: number): string {
  if (failureRate >= 75) return "bg-red-400 text-white";
  if (failureRate >= 50) return "bg-red-200 text-red-900";
  if (failureRate >= 25) return "bg-amber-200 text-amber-900";
  if (failureRate > 0) return "bg-green-100 text-green-800";
  return "bg-muted text-muted-foreground";
}

export function HeatmapGrid({ data }: HeatmapGridProps) {
  const vectors = Array.from(new Set(data.map((d) => d.attackVector)));
  const departments = Array.from(new Set(data.map((d) => d.department)));

  const lookup = new Map<string, HeatmapCell>();
  for (const cell of data) {
    lookup.set(`${cell.attackVector}::${cell.department}`, cell);
  }

  if (vectors.length === 0 || departments.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No data available for heatmap
      </p>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="overflow-x-auto">
        <div
          className="grid gap-1 min-w-[500px]"
          style={{
            gridTemplateColumns: `140px repeat(${departments.length}, minmax(80px, 1fr))`,
          }}
        >
          {/* Header row */}
          <div />
          {departments.map((dept) => (
            <div
              key={dept}
              className="text-xs font-medium text-muted-foreground text-center px-1 pb-2 truncate"
            >
              {dept}
            </div>
          ))}

          {/* Data rows */}
          {vectors.map((vector) => (
            <>
              <div
                key={`label-${vector}`}
                className="text-xs text-muted-foreground flex items-center pr-2 truncate"
              >
                {vector}
              </div>
              {departments.map((dept) => {
                const cell = lookup.get(`${vector}::${dept}`);
                if (!cell) {
                  return (
                    <div
                      key={`${vector}-${dept}`}
                      className="h-10 rounded-md border border-dashed border-muted-foreground/20 flex items-center justify-center"
                    >
                      <span className="text-[10px] text-muted-foreground/40">
                        N/A
                      </span>
                    </div>
                  );
                }
                return (
                  <Tooltip key={`${vector}-${dept}`}>
                    <TooltipTrigger asChild>
                      <div
                        className={`h-10 rounded-md flex items-center justify-center cursor-default transition-transform hover:scale-105 ${getCellColor(cell.failureRate)}`}
                      >
                        <span className="text-xs font-medium">
                          {cell.failureRate}%
                        </span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-xs space-y-0.5">
                        <p className="font-medium">
                          {vector} vs {dept}
                        </p>
                        <p>{cell.totalCalls} calls</p>
                        <p>Failure rate: {cell.failureRate}%</p>
                        <p>Avg risk: {cell.avgRiskScore}</p>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </>
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}
