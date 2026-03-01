import { useState, useEffect } from "react";
import { Search, Download, Play } from "lucide-react";
import { motion } from "motion/react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "./ui/sheet";
import { Separator } from "./ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import type { Call } from "../types";
import { getCalls } from "../services/api";

const complianceBadgeStyle = (compliance: string) => {
  switch (compliance) {
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

const statusBadgeStyle = (status: string) => {
  switch (status) {
    case "completed":
      return { backgroundColor: "#f0fdf4", color: "#22c55e" };
    case "in_progress":
      return { backgroundColor: "#eff6ff", color: "#3b82f6" };
    case "pending":
      return { backgroundColor: "#fffbeb", color: "#f59e0b" };
    case "failed":
      return { backgroundColor: "#fef2f2", color: "#ef4444" };
    default:
      return { backgroundColor: "#f4f4f4", color: "#9ca3af" };
  }
};

const getRiskColor = (score: number) => {
  if (score >= 70) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export function Calls() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterCompliance, setFilterCompliance] = useState<string>("all");
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCalls().then((data) => {
      setCalls(data);
      setLoading(false);
    });
  }, []);

  const filteredCalls = calls.filter((call) => {
    const matchesSearch =
      call.employeeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.callerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.campaignName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      filterStatus === "all" || call.status === filterStatus;
    const matchesCompliance =
      filterCompliance === "all" ||
      call.employeeCompliance === filterCompliance;
    return matchesSearch && matchesStatus && matchesCompliance;
  });

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div className="mb-8" variants={item}>
        <h1 className="text-2xl font-medium mb-1 text-foreground">
          Call History
        </h1>
        <p className="text-sm text-muted-foreground">
          Review and analyze vishing test call results
        </p>
      </motion.div>

      {/* Filters */}
      <motion.div className="mb-5 flex gap-3 flex-wrap" variants={item}>
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search calls..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterCompliance} onValueChange={setFilterCompliance}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Compliance" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Compliance</SelectItem>
            <SelectItem value="passed">Passed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="partial">Partial</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline">
          <Download className="w-4 h-4" />
          Export
        </Button>
      </motion.div>

      {/* Table */}
      <motion.div variants={item}>
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6">Employee</TableHead>
                <TableHead>Caller</TableHead>
                <TableHead>Campaign</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Compliance</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="w-16" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCalls.map((call) => (
                <TableRow key={call.id}>
                  <TableCell className="pl-6 font-medium text-foreground">
                    {call.employeeName}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {call.callerName}
                  </TableCell>
                  <TableCell className="max-w-36">
                    <p className="truncate text-muted-foreground">
                      {call.campaignName}
                    </p>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className="capitalize border-0"
                      style={statusBadgeStyle(call.status)}
                    >
                      {call.status.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {call.duration}
                  </TableCell>
                  <TableCell>
                    <span
                      className="font-medium"
                      style={{ color: getRiskColor(call.riskScore) }}
                    >
                      {call.riskScore}%
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className="capitalize border-0"
                      style={complianceBadgeStyle(call.employeeCompliance)}
                    >
                      {call.employeeCompliance}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {call.startedAt}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedCall(call)}
                      className="text-xs"
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </motion.div>

      {/* Call Detail Sheet (slide-over panel) */}
      <Sheet
        open={!!selectedCall}
        onOpenChange={(open) => !open && setSelectedCall(null)}
      >
        <SheetContent className="sm:max-w-lg overflow-y-auto">
          {selectedCall && (
            <>
              <SheetHeader>
                <SheetTitle>Call Details</SheetTitle>
                <SheetDescription>
                  {selectedCall.campaignName}
                </SheetDescription>
              </SheetHeader>

              <div className="mt-6 space-y-5 px-4">
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  {[
                    {
                      label: "Employee",
                      value: selectedCall.employeeName,
                    },
                    { label: "Duration", value: selectedCall.duration },
                    {
                      label: "Caller Profile",
                      value: selectedCall.callerName,
                    },
                    {
                      label: "Date & Time",
                      value: selectedCall.startedAt,
                    },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <p className="text-xs text-muted-foreground mb-0.5">
                        {label}
                      </p>
                      <p className="text-sm text-foreground">{value}</p>
                    </div>
                  ))}
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">
                      Risk Score
                    </p>
                    <p
                      className="text-xl font-medium"
                      style={{
                        color: getRiskColor(selectedCall.riskScore),
                      }}
                    >
                      {selectedCall.riskScore}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">
                      Compliance
                    </p>
                    <Badge
                      className="capitalize border-0"
                      style={complianceBadgeStyle(
                        selectedCall.employeeCompliance
                      )}
                    >
                      {selectedCall.employeeCompliance}
                    </Badge>
                  </div>
                </div>

                <Separator />

                {/* Flags */}
                <div>
                  <p className="text-xs text-muted-foreground mb-2">
                    Red Flags
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedCall.flags.map((flag, index) => (
                      <Badge
                        key={index}
                        className="border-0"
                        style={{
                          backgroundColor:
                            flag === "Proper Verification" ||
                            flag === "Asked Questions"
                              ? "#f0fdf4"
                              : "#fef2f2",
                          color:
                            flag === "Proper Verification" ||
                            flag === "Asked Questions"
                              ? "#22c55e"
                              : "#ef4444",
                        }}
                      >
                        {flag}
                      </Badge>
                    ))}
                  </div>
                </div>

                <Separator />

                {/* AI Summary */}
                {selectedCall.aiSummary && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">
                      AI Summary
                    </p>
                    <div className="p-4 rounded-xl bg-muted/50 text-sm text-muted-foreground leading-relaxed">
                      {selectedCall.aiSummary}
                    </div>
                  </div>
                )}

                {/* Transcript */}
                {selectedCall.transcript && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">
                      Transcript
                    </p>
                    <div className="p-4 rounded-xl bg-muted/50 text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                      {selectedCall.transcript}
                    </div>
                  </div>
                )}

                <div className="flex gap-3 pt-2">
                  <Button variant="outline" size="sm">
                    <Play className="w-4 h-4" />
                    Play Recording
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="w-4 h-4" />
                    Download
                  </Button>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </motion.div>
  );
}
