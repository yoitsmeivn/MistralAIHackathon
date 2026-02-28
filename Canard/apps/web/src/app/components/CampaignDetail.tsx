import { useState, useEffect } from "react";
import { Link, useParams } from "react-router";
import {
  ArrowLeft,
  Play,
  Pause,
  Settings,
  Download,
  Phone,
  Users,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { motion } from "motion/react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Separator } from "./ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { Skeleton } from "./ui/skeleton";
import type { Campaign, Call } from "../types";
import { getCampaign, getCampaignCalls } from "../services/api";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const getRiskColor = (score: number) => {
  if (score >= 70) return "#ef4444";
  if (score >= 50) return "#f59e0b";
  return "#22c55e";
};

export function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [callResults, setCallResults] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([getCampaign(id), getCampaignCalls(id)]).then(
      ([camp, calls]) => {
        setCampaign(camp || null);
        setCallResults(calls);
        setLoading(false);
      }
    );
  }, [id]);

  if (loading || !campaign) {
    return (
      <div className="p-8 max-w-7xl space-y-4">
        <Skeleton className="h-8 w-60" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-40 rounded-xl" />
      </div>
    );
  }

  const progress = (campaign.completedCalls / campaign.totalCalls) * 100;
  const failedCount = callResults.filter(
    (c) => c.employeeCompliance === "failed"
  ).length;
  const passedCount = callResults.filter(
    (c) => c.employeeCompliance === "passed"
  ).length;

  const stats = [
    {
      label: "Completed Calls",
      value: String(campaign.completedCalls),
      icon: Phone,
    },
    {
      label: "Employees Tested",
      value: String(campaign.completedCalls),
      icon: Users,
    },
    { label: "Failed Tests", value: String(failedCount), icon: AlertTriangle },
    { label: "Passed Tests", value: String(passedCount), icon: CheckCircle },
  ];

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div className="mb-8" variants={item}>
        <Link
          to="/campaigns"
          className="inline-flex items-center gap-1.5 text-sm mb-4 transition-opacity hover:opacity-70 text-muted-foreground"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Campaigns
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-medium mb-1 text-foreground">
              {campaign.name}
            </h1>
            <p className="text-sm text-muted-foreground">
              {campaign.description}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button variant="outline" size="sm">
              <Settings className="w-4 h-4" />
              Settings
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button size="sm">
              {campaign.status === "active" ? (
                <>
                  <Pause className="w-4 h-4" /> Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Resume
                </>
              )}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <motion.div key={stat.label} variants={item}>
              <Card>
                <CardContent className="pt-5 pb-5">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                    style={{ backgroundColor: "#fdfbe1" }}
                  >
                    <Icon className="w-4 h-4 text-foreground" />
                  </div>
                  <p className="text-2xl font-medium text-foreground mb-0.5">
                    {stat.value}
                  </p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Progress Card */}
      <motion.div variants={item}>
        <Card className="mb-6">
          <CardHeader className="pb-0">
            <CardTitle className="text-sm font-medium">
              Campaign Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-5">
              <div className="flex items-center justify-between text-xs mb-2">
                <span className="text-muted-foreground">Completed Calls</span>
                <span className="text-foreground">
                  {campaign.completedCalls}/{campaign.totalCalls} ·{" "}
                  {Math.round(progress)}%
                </span>
              </div>
              <Progress value={progress} className="h-1.5" />
            </div>

            <Separator className="my-4" />

            <div className="grid grid-cols-3 gap-6">
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Average Risk Score
                </p>
                <p
                  className="text-xl font-medium"
                  style={{ color: getRiskColor(campaign.avgRiskScore) }}
                >
                  {campaign.avgRiskScore}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Started</p>
                <p className="text-sm text-foreground">
                  {campaign.startedAt
                    ? new Date(campaign.startedAt).toLocaleString()
                    : "Not started"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">
                  Attack Vector
                </p>
                <p className="text-sm text-foreground">
                  {campaign.attackVector}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Call Results Table */}
      <motion.div variants={item}>
        <Card>
          <CardHeader className="border-b pb-4">
            <CardTitle className="text-sm font-medium">Call Results</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6">Employee</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>Result</TableHead>
                  <TableHead className="pr-6">Timestamp</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {callResults.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No call results yet
                    </TableCell>
                  </TableRow>
                ) : (
                  callResults.map((result) => (
                    <TableRow key={result.id}>
                      <TableCell className="pl-6 font-medium">
                        {result.employeeName}
                      </TableCell>
                      <TableCell className="text-muted-foreground">—</TableCell>
                      <TableCell className="text-muted-foreground">
                        {result.duration}
                      </TableCell>
                      <TableCell>
                        <span
                          className="font-medium"
                          style={{ color: getRiskColor(result.riskScore) }}
                        >
                          {result.riskScore}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge
                          className="border-0 capitalize"
                          style={
                            result.employeeCompliance === "passed"
                              ? { backgroundColor: "#f0fdf4", color: "#22c55e" }
                              : { backgroundColor: "#fef2f2", color: "#ef4444" }
                          }
                        >
                          {result.employeeCompliance}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-6 text-xs text-muted-foreground">
                        {result.startedAt}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
