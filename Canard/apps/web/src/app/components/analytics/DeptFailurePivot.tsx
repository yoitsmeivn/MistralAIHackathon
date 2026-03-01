import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import type { DeptFlagPivotData } from "../../types";

interface Props {
  data: DeptFlagPivotData;
  onFilterChange?: (flagType: string | undefined) => void;
}

function getCellColor(percentage: number, isPositive: boolean): string {
  if (isPositive) {
    if (percentage >= 60) return "bg-green-400 text-white";
    if (percentage >= 30) return "bg-green-200 text-green-900";
    if (percentage > 0) return "bg-green-100 text-green-800";
    return "bg-muted text-muted-foreground";
  }
  if (percentage >= 60) return "bg-red-400 text-white";
  if (percentage >= 30) return "bg-red-200 text-red-900";
  if (percentage > 0) return "bg-amber-200 text-amber-900";
  return "bg-muted text-muted-foreground";
}

export function DeptFailurePivot({ data, onFilterChange }: Props) {
  const [filter, setFilter] = useState<"negative" | "positive" | "all">("negative");
  const [selectedCell, setSelectedCell] = useState<string | null>(null);

  const handleFilterChange = (f: "negative" | "positive" | "all") => {
    setFilter(f);
    setSelectedCell(null);
    onFilterChange?.(f === "all" ? undefined : f);
  };

  // Build lookup
  const lookup = new Map<string, (typeof data.cells)[0]>();
  for (const cell of data.cells) {
    lookup.set(`${cell.flag}::${cell.department}`, cell);
  }

  // Filter flags based on selected filter
  const displayFlags = data.flags.filter((f) => {
    if (filter === "all") return true;
    const isPos = data.positiveFlags.includes(f);
    return filter === "positive" ? isPos : !isPos;
  });

  const selected = selectedCell ? lookup.get(selectedCell) : null;

  if (data.departments.length === 0 || displayFlags.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No data available
      </p>
    );
  }

  return (
    <div>
      {/* Filter toggle */}
      <div className="flex rounded-lg bg-muted p-0.5 mb-4 w-fit">
        {(["negative", "positive", "all"] as const).map((f) => (
          <button
            key={f}
            onClick={() => handleFilterChange(f)}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors capitalize ${
              filter === f
                ? "bg-background text-foreground shadow-sm font-medium"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {f === "negative" ? "Failures" : f === "positive" ? "Positive" : "All"}
          </button>
        ))}
      </div>

      <TooltipProvider delayDuration={200}>
        <div className="overflow-x-auto">
          <div
            className="grid gap-1 min-w-[500px]"
            style={{
              gridTemplateColumns: `180px repeat(${data.departments.length}, minmax(80px, 1fr))`,
            }}
          >
            {/* Header row */}
            <div />
            {data.departments.map((dept) => (
              <div key={dept} className="text-xs font-medium text-muted-foreground text-center px-1 pb-2">
                <span className="truncate block">{dept}</span>
                <span className="text-[10px] text-muted-foreground/60">
                  {data.departmentTotals[dept] || 0} calls
                </span>
              </div>
            ))}

            {/* Data rows */}
            {displayFlags.map((flag) => {
              const isPositive = data.positiveFlags.includes(flag);
              return (
                <div key={flag} className="contents">
                  <div className="text-xs text-muted-foreground flex items-center pr-2 gap-1.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-full shrink-0 ${isPositive ? "bg-green-400" : "bg-red-400"}`}
                    />
                    <span className="truncate">{flag}</span>
                  </div>
                  {data.departments.map((dept) => {
                    const cell = lookup.get(`${flag}::${dept}`);
                    const key = `${flag}::${dept}`;
                    if (!cell) {
                      return (
                        <div
                          key={key}
                          className="h-10 rounded-md border border-dashed border-muted-foreground/20 flex items-center justify-center"
                        >
                          <span className="text-[10px] text-muted-foreground/40">–</span>
                        </div>
                      );
                    }
                    const isSelected = selectedCell === key;
                    return (
                      <Tooltip key={key}>
                        <TooltipTrigger asChild>
                          <button
                            onClick={() => setSelectedCell(isSelected ? null : key)}
                            className={`h-10 rounded-md flex items-center justify-center cursor-pointer transition-all hover:scale-105 ${getCellColor(cell.percentage, cell.isPositive)} ${
                              isSelected ? "ring-2 ring-foreground ring-offset-1" : ""
                            }`}
                          >
                            <span className="text-xs font-medium">{cell.count}</span>
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs space-y-0.5">
                            <p className="font-medium">{flag}</p>
                            <p>{dept}</p>
                            <p>Count: {cell.count}</p>
                            <p>{cell.percentage}% of dept calls</p>
                            <p>{cell.affectedEmployees} employee{cell.affectedEmployees !== 1 ? "s" : ""}</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      </TooltipProvider>

      {/* Detail panel */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 rounded-lg border p-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{selected.flag}</p>
                  <p className="text-xs text-muted-foreground">{selected.department}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold">{selected.count}</p>
                  <p className="text-xs text-muted-foreground">
                    {selected.percentage}% of {selected.totalDeptCalls} calls · {selected.affectedEmployees} employee{selected.affectedEmployees !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
