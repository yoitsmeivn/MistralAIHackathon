import { useState } from "react";
import { Link } from "react-router";
import { AnimatePresence, motion } from "motion/react";
import { ChevronRight, Flame, Eye, UserCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import type { OrgTreeNode, HierarchyRiskData } from "../../types";

interface TreeProps {
  data: HierarchyRiskData;
}

interface NodeProps {
  node: OrgTreeNode;
  isRoot?: boolean;
  isOnRiskPath: boolean;
  isHotspot: boolean;
  riskPathIds: Set<string>;
  hotspotIds: Set<string>;
  defaultExpanded: boolean;
}

const getRiskColor = (score: number) => {
  if (score >= 75) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

function OrgRiskTreeNode({
  node,
  isRoot,
  isOnRiskPath,
  isHotspot,
  riskPathIds,
  hotspotIds,
  defaultExpanded,
}: NodeProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const hasChildren = node.children.length > 0;

  return (
    <div className={`${isRoot ? "" : "ml-5 border-l border-muted-foreground/20 pl-4"}`}>
      <div
        className={`flex items-center gap-2 p-2 rounded-lg transition-colors hover:bg-muted/50 ${
          isOnRiskPath ? "border-l-2 border-red-400 -ml-[2px] pl-[14px]" : ""
        }`}
      >
        {/* Expand toggle */}
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-5 h-5 flex items-center justify-center rounded hover:bg-muted shrink-0"
          >
            <ChevronRight
              className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${expanded ? "rotate-90" : ""}`}
            />
          </button>
        ) : (
          <span className="w-5" />
        )}

        {/* Avatar */}
        <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 bg-muted">
          <UserCircle className="w-4 h-4 text-muted-foreground" />
        </div>

        {/* Name + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <Link
              to={`/employees/${node.id}`}
              className="text-sm font-medium hover:underline truncate"
            >
              {node.fullName}
            </Link>
            {isRoot && (
              <span className="text-[10px] bg-blue-100 text-blue-600 px-1.5 py-0 rounded-full font-medium">
                <Eye className="w-2.5 h-2.5 inline -mt-0.5" /> viewing
              </span>
            )}
            {isHotspot && !isRoot && (
              <Flame className="w-3.5 h-3.5 text-orange-500 shrink-0" />
            )}
          </div>
          <p className="text-[11px] text-muted-foreground truncate">
            {node.jobTitle}{node.department ? ` · ${node.department}` : ""}
          </p>
        </div>

        {/* Scores */}
        <TooltipProvider delayDuration={200}>
          <div className="flex items-center gap-3 shrink-0">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-center min-w-[40px]">
                  <p className="text-xs font-medium" style={{ color: getRiskColor(node.personalRiskScore) }}>
                    {node.personalRiskScore}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Personal</p>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <div className="text-xs space-y-0.5">
                  <p className="font-medium">Personal Stats</p>
                  <p>Risk: {node.personalRiskScore}</p>
                  <p>Fail Rate: {node.personalFailureRate}%</p>
                  <p>Tests: {node.personalTotalTests}</p>
                  <p>Failed: {node.personalFailedTests}</p>
                </div>
              </TooltipContent>
            </Tooltip>

            {node.children.length > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="text-center min-w-[40px]">
                    <p className="text-xs font-medium" style={{ color: getRiskColor(node.teamRiskScore) }}>
                      {node.teamRiskScore}
                    </p>
                    <p className="text-[10px] text-muted-foreground">Team</p>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="text-xs space-y-0.5">
                    <p className="font-medium">Team Stats</p>
                    <p>Risk: {node.teamRiskScore}</p>
                    <p>Fail Rate: {node.teamFailureRate}%</p>
                    <p>Tests: {node.teamTotalTests}</p>
                    <p>Failed: {node.teamFailedTests}</p>
                  </div>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </TooltipProvider>
      </div>

      {/* Children */}
      <AnimatePresence>
        {expanded && hasChildren && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            {node.children
              .slice()
              .sort((a, b) => b.teamRiskScore - a.teamRiskScore)
              .map((child) => (
                <OrgRiskTreeNode
                  key={child.id}
                  node={child}
                  isOnRiskPath={riskPathIds.has(child.id)}
                  isHotspot={hotspotIds.has(child.id)}
                  riskPathIds={riskPathIds}
                  hotspotIds={hotspotIds}
                  defaultExpanded={child.depth < 2}
                />
              ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function OrgRiskTree({ data }: TreeProps) {
  const riskPathIds = new Set(data.highestRiskPath);
  const hotspotIds = new Set(data.riskHotspots.map((n) => n.id));

  return (
    <div className="py-1">
      <OrgRiskTreeNode
        node={data.manager}
        isRoot
        isOnRiskPath={riskPathIds.has(data.manager.id)}
        isHotspot={false}
        riskPathIds={riskPathIds}
        hotspotIds={hotspotIds}
        defaultExpanded
      />
    </div>
  );
}
