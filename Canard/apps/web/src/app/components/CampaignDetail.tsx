import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Link, useParams } from "react-router";
import {
  ArrowLeft,
  Pause,
  Settings,
  Download,
  Phone,
  Users,
  AlertTriangle,
  CheckCircle,
  Rocket,
  Loader2,
  FileText,
  Shield,
  Plus,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Input } from "./ui/input";
import { Skeleton } from "./ui/skeleton";
import type { Campaign, Call, Script, Caller, Employee } from "../types";
import {
  getCampaign,
  getCampaignCalls,
  getCampaignScripts,
  getCallers,
  getEmployees,
  launchCampaign,
  createScript,
  updateScript,
  updateCampaign,
} from "../services/api";

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

const difficultyStyle = (d: string) => {
  switch (d) {
    case "easy":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "hard":
      return "bg-red-50 text-red-700 border-red-200";
    default:
      return "bg-amber-50 text-amber-700 border-amber-200";
  }
};

const statusStyle = (status: string) => {
  switch (status) {
    case "running":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "active":
      return "bg-[#fdfbe1] text-foreground border-[#fdfbe1]";
    case "paused":
      return "bg-orange-50 text-orange-700 border-orange-50";
    case "completed":
      return "bg-muted text-muted-foreground border-muted";
    case "draft":
      return "bg-blue-50 text-indigo-600 border-blue-50";
    default:
      return "";
  }
};

export function CampaignDetail() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [callResults, setCallResults] = useState<Call[]>([]);
  const [campaignScripts, setCampaignScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);

  // Script detail/edit dialog state
  const [editingScript, setEditingScript] = useState<Script | null>(null);
  const [isNewScript, setIsNewScript] = useState(false);
  const [scriptForm, setScriptForm] = useState({
    name: "",
    attack_type: "",
    difficulty: "medium",
    objectives: "",
    escalation_steps: "",
    description: "",
  });
  const [saving, setSaving] = useState(false);

  // Launch dialog state
  const [showLaunchDialog, setShowLaunchDialog] = useState(false);
  const [callers, setCallers] = useState<Caller[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [scriptMode, setScriptMode] = useState<"single" | "all">("all");
  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedCallerId, setSelectedCallerId] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [launching, setLaunching] = useState(false);

  // Call detail dialog state
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);

  // Campaign edit dialog state
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [campaignForm, setCampaignForm] = useState({
    name: "",
    description: "",
    attack_vector: "",
    status: "",
    scheduled_at: "",
  });
  const [savingCampaign, setSavingCampaign] = useState(false);

  // Polling ref
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadCampaignData = useCallback(() => {
    if (!id) return;
    Promise.all([getCampaign(id), getCampaignCalls(id), getCampaignScripts(id)]).then(
      ([camp, calls, scripts]) => {
        setCampaign(camp || null);
        setCallResults(calls);
        setCampaignScripts(scripts);
        setLoading(false);
      }
    );
  }, [id]);

  const refreshCampaignStatus = useCallback(() => {
    if (!id) return;
    getCampaign(id).then((camp) => {
      setCampaign(camp || null);
    });
  }, [id]);

  useEffect(() => {
    loadCampaignData();
  }, [loadCampaignData]);

  useEffect(() => {
    Promise.all([getCallers(), getEmployees()]).then(([c, e]) => {
      setCallers(c.filter((x) => x.isActive));
      setEmployees(e.filter((x) => x.isActive));
    });
  }, []);

  // Poll when campaign is running
  useEffect(() => {
    if (campaign?.status === "running") {
      pollRef.current = setInterval(refreshCampaignStatus, 15000);
    } else if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [campaign?.status, refreshCampaignStatus]);

  // Department list derived from employees
  const departments = useMemo(() => {
    const deptMap = new Map<string, number>();
    for (const e of employees) {
      if (e.department) {
        deptMap.set(e.department, (deptMap.get(e.department) || 0) + 1);
      }
    }
    return Array.from(deptMap.entries()).map(([name, count]) => ({
      name,
      count,
    }));
  }, [employees]);

  const handleOpenLaunchDialog = async () => {
    setShowLaunchDialog(true);
    if (callers.length === 0 || employees.length === 0) {
      const [c, e] = await Promise.all([getCallers(), getEmployees()]);
      setCallers(c.filter((x) => x.isActive));
      setEmployees(e.filter((x) => x.isActive));
    }
  };

  const handleLaunch = async () => {
    if (!id) return;
    if (scriptMode === "single" && (!selectedScriptId || !selectedCallerId)) return;
    setLaunching(true);
    try {
      await launchCampaign(id, {
        script_id: scriptMode === "single" ? selectedScriptId : undefined,
        caller_id: scriptMode === "single" ? selectedCallerId : undefined,
        department: selectedDepartment && selectedDepartment !== "__all__" ? selectedDepartment : undefined,
      });
      setShowLaunchDialog(false);
      setScriptMode("all");
      setSelectedScriptId("");
      setSelectedCallerId("");
      setSelectedDepartment("");
      loadCampaignData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to launch campaign");
    } finally {
      setLaunching(false);
    }
  };

  const handleOpenEditDialog = () => {
    if (!campaign) return;
    setCampaignForm({
      name: campaign.name,
      description: campaign.description,
      attack_vector: campaign.attackVector,
      status: campaign.status,
      scheduled_at: campaign.scheduledAt || "",
    });
    setShowEditDialog(true);
  };

  const handleSaveCampaign = async () => {
    if (!id) return;
    setSavingCampaign(true);
    try {
      const updates: Record<string, unknown> = {};
      if (campaignForm.name !== campaign?.name) updates.name = campaignForm.name;
      if (campaignForm.description !== campaign?.description) updates.description = campaignForm.description;
      if (campaignForm.attack_vector !== campaign?.attackVector) updates.attack_vector = campaignForm.attack_vector;
      if (campaignForm.status !== campaign?.status) updates.status = campaignForm.status;
      if (campaignForm.scheduled_at !== (campaign?.scheduledAt || "")) updates.scheduled_at = campaignForm.scheduled_at || null;

      if (Object.keys(updates).length > 0) {
        await updateCampaign(id, updates);
        loadCampaignData();
      }
      setShowEditDialog(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update campaign");
    } finally {
      setSavingCampaign(false);
    }
  };

  const handleOpenScript = (script: Script) => {
    setIsNewScript(false);
    setEditingScript(script);
    setScriptForm({
      name: script.name,
      attack_type: script.attackType,
      difficulty: script.difficulty,
      objectives: script.objectives.join(", "),
      escalation_steps: script.escalationSteps.join(", "),
      description: script.description,
    });
  };

  const handleNewScript = () => {
    setIsNewScript(true);
    setEditingScript({} as Script);
    setScriptForm({
      name: "",
      attack_type: "",
      difficulty: "medium",
      objectives: "",
      escalation_steps: "",
      description: "",
    });
  };

  const handleSaveScript = async () => {
    if (!editingScript) return;
    setSaving(true);
    try {
      const payload = {
        name: scriptForm.name,
        attack_type: scriptForm.attack_type,
        difficulty: scriptForm.difficulty,
        objectives: scriptForm.objectives.split(",").map((s) => s.trim()).filter(Boolean),
        escalation_steps: scriptForm.escalation_steps.split(",").map((s) => s.trim()).filter(Boolean),
        description: scriptForm.description,
      };
      if (isNewScript) {
        await createScript({ ...payload, campaign_id: id! });
      } else {
        await updateScript(editingScript.id, payload);
      }
      setEditingScript(null);
      setIsNewScript(false);
      loadCampaignData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save script");
    } finally {
      setSaving(false);
    }
  };

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

  const totalCalls = campaign.totalCalls || 1;
  const progress = (campaign.completedCalls / totalCalls) * 100;
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

  const canLaunch = campaign.status === "draft" || campaign.status === "paused";
  const isRunning = campaign.status === "running";

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
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-medium mb-1 text-foreground">
                {campaign.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {campaign.description}
              </p>
            </div>
            <Badge className={`${statusStyle(campaign.status)} border`}>
              {isRunning && (
                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
              )}
              {campaign.status}
            </Badge>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button variant="outline" size="sm" onClick={handleOpenEditDialog}>
              <Settings className="w-4 h-4" />
              Settings
            </Button>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4" />
              Export
            </Button>
            {canLaunch && (
              <Button size="sm" onClick={handleOpenLaunchDialog}>
                <Rocket className="w-4 h-4" />
                Launch
              </Button>
            )}
            {isRunning && (
              <Button size="sm" variant="outline" disabled>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running...
              </Button>
            )}
            {!canLaunch && !isRunning && (
              <Button size="sm" variant="outline" disabled>
                {campaign.status === "completed" ? (
                  <>
                    <CheckCircle className="w-4 h-4" /> Completed
                  </>
                ) : (
                  <>
                    <Pause className="w-4 h-4" /> Paused
                  </>
                )}
              </Button>
            )}
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
                  {campaign.totalCalls > 0 ? Math.round(progress) : 0}%
                </span>
              </div>
              <Progress value={campaign.totalCalls > 0 ? progress : 0} className="h-1.5" />
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

      {/* Scripts Card */}
        <motion.div variants={item}>
          <Card className="mb-6">
            <CardHeader className="border-b pb-4 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Attack Scripts ({campaignScripts.length})
              </CardTitle>
              <Button variant="outline" size="sm" onClick={handleNewScript}>
                <Plus className="w-3.5 h-3.5" />
                New Script
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-6">Script</TableHead>
                    <TableHead>Attack Type</TableHead>
                    <TableHead>Difficulty</TableHead>
                    <TableHead>Objective</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaignScripts.map((script) => (
                    <TableRow
                      key={script.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => handleOpenScript(script)}
                    >
                      <TableCell className="pl-6">
                        <div>
                          <p className="font-medium text-sm">{script.name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                            {script.description}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs font-normal">
                          <Shield className="w-3 h-3 mr-1" />
                          {script.attackType}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={`${difficultyStyle(script.difficulty)} border text-xs`}>
                          {script.difficulty}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {script.objectives[0] || "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
                    <TableRow key={result.id} className="cursor-pointer hover:bg-muted/50" onClick={() => setSelectedCall(result)}>
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

      {/* Campaign Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Campaign Settings</DialogTitle>
            <DialogDescription>
              Edit the campaign details and configuration.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">Name</p>
              <Input
                value={campaignForm.name}
                onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })}
              />
            </div>

            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">Description</p>
              <textarea
                className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                rows={3}
                value={campaignForm.description}
                onChange={(e) => setCampaignForm({ ...campaignForm, description: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Attack Vector</p>
                <Select
                  value={campaignForm.attack_vector}
                  onValueChange={(v) => setCampaignForm({ ...campaignForm, attack_vector: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select attack vector" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Authority Impersonation">Authority Impersonation</SelectItem>
                    <SelectItem value="Financial Scam">Financial Scam</SelectItem>
                    <SelectItem value="Technical Support Scam">Technical Support Scam</SelectItem>
                    <SelectItem value="Prize/Reward">Prize/Reward</SelectItem>
                    <SelectItem value="Internal Authority">Internal Authority</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Status</p>
                <Select
                  value={campaignForm.status}
                  onValueChange={(v) => setCampaignForm({ ...campaignForm, status: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">
                Scheduled At <span className="text-muted-foreground/60">(optional)</span>
              </p>
              <Input
                type="datetime-local"
                value={campaignForm.scheduled_at ? campaignForm.scheduled_at.slice(0, 16) : ""}
                onChange={(e) => setCampaignForm({ ...campaignForm, scheduled_at: e.target.value ? new Date(e.target.value).toISOString() : "" })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveCampaign} disabled={savingCampaign || !campaignForm.name.trim()}>
              {savingCampaign ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Script Detail/Edit Dialog */}
      <Dialog open={!!editingScript} onOpenChange={(open) => !open && setEditingScript(null)}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{isNewScript ? "New Script" : "Script Details"}</DialogTitle>
            <DialogDescription>
              {isNewScript
                ? `Create a new attack script for ${campaign.name}.`
                : "View and edit the script configuration for this attack scenario."}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Name</p>
                <Input
                  value={scriptForm.name}
                  onChange={(e) => setScriptForm({ ...scriptForm, name: e.target.value })}
                />
              </div>
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Attack Type</p>
                <Select
                  value={scriptForm.attack_type}
                  onValueChange={(v) => setScriptForm({ ...scriptForm, attack_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Authority Impersonation">Authority Impersonation</SelectItem>
                    <SelectItem value="Financial Scam">Financial Scam</SelectItem>
                    <SelectItem value="Technical Support Scam">Technical Support Scam</SelectItem>
                    <SelectItem value="Prize/Reward">Prize/Reward</SelectItem>
                    <SelectItem value="Internal Authority">Internal Authority</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Difficulty</p>
                <Select
                  value={scriptForm.difficulty}
                  onValueChange={(v) => setScriptForm({ ...scriptForm, difficulty: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="easy">Easy</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="hard">Hard</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="block text-xs text-muted-foreground mb-1.5">Objective</p>
                <Input
                  value={scriptForm.objectives}
                  onChange={(e) => setScriptForm({ ...scriptForm, objectives: e.target.value })}
                  placeholder="e.g. get_vpn_password"
                />
              </div>
            </div>

            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">Description</p>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                rows={2}
                value={scriptForm.description}
                onChange={(e) => setScriptForm({ ...scriptForm, description: e.target.value })}
              />
            </div>

            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">
                Escalation Steps <span className="text-muted-foreground/60">(comma-separated)</span>
              </p>
              <textarea
                className="flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                rows={2}
                value={scriptForm.escalation_steps}
                onChange={(e) => setScriptForm({ ...scriptForm, escalation_steps: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setEditingScript(null); setIsNewScript(false); }}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveScript}
              disabled={saving || !scriptForm.name}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : isNewScript ? (
                "Create Script"
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Launch Campaign Dialog */}
      <Dialog open={showLaunchDialog} onOpenChange={setShowLaunchDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Launch Campaign</DialogTitle>
            <DialogDescription>
              Choose how scripts are assigned to employees, then select a target
              department.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Script mode toggle */}
            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">
                Script Mode
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setScriptMode("all")}
                  className={`rounded-md border px-3 py-2 text-sm text-left transition-colors ${
                    scriptMode === "all"
                      ? "border-foreground bg-foreground text-background"
                      : "border-input hover:bg-muted/50"
                  }`}
                >
                  <p className="font-medium">All Scripts</p>
                  <p className={`text-xs mt-0.5 ${scriptMode === "all" ? "text-background/70" : "text-muted-foreground"}`}>
                    Randomly assign from {campaignScripts.length} scripts
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => setScriptMode("single")}
                  className={`rounded-md border px-3 py-2 text-sm text-left transition-colors ${
                    scriptMode === "single"
                      ? "border-foreground bg-foreground text-background"
                      : "border-input hover:bg-muted/50"
                  }`}
                >
                  <p className="font-medium">Single Script</p>
                  <p className={`text-xs mt-0.5 ${scriptMode === "single" ? "text-background/70" : "text-muted-foreground"}`}>
                    Same script for every employee
                  </p>
                </button>
              </div>
            </div>

            {/* Single-script selectors (only shown in single mode) */}
            {scriptMode === "single" && (
              <>
                <div>
                  <p className="block text-xs text-muted-foreground mb-1.5">
                    Script
                  </p>
                  <Select
                    value={selectedScriptId}
                    onValueChange={setSelectedScriptId}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a script" />
                    </SelectTrigger>
                    <SelectContent>
                      {campaignScripts.map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.name}{" "}
                          <span className="text-muted-foreground">
                            ({s.difficulty})
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <p className="block text-xs text-muted-foreground mb-1.5">
                    Caller
                  </p>
                  <Select
                    value={selectedCallerId}
                    onValueChange={setSelectedCallerId}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a caller" />
                    </SelectTrigger>
                    <SelectContent>
                      {callers.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.personaName}{" "}
                          <span className="text-muted-foreground">
                            — {c.personaRole}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div>
              <p className="block text-xs text-muted-foreground mb-1.5">
                Department{" "}
                <span className="text-muted-foreground/60">(optional — all employees if blank)</span>
              </p>
              <Select
                value={selectedDepartment}
                onValueChange={setSelectedDepartment}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All departments</SelectItem>
                  {departments.map((d) => (
                    <SelectItem key={d.name} value={d.name}>
                      {d.name}{" "}
                      <span className="text-muted-foreground">
                        ({d.count} employees)
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowLaunchDialog(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleLaunch}
              disabled={
                launching ||
                (scriptMode === "single" && (!selectedScriptId || !selectedCallerId))
              }
            >
              {launching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Launching...
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  Launch Campaign
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Call Detail Dialog */}
      <Dialog open={!!selectedCall} onOpenChange={(open) => !open && setSelectedCall(null)}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedCall?.employeeName}</DialogTitle>
            <DialogDescription>
              {selectedCall?.campaignName} · {selectedCall?.startedAt}
            </DialogDescription>
          </DialogHeader>

          {selectedCall && (
            <div className="space-y-4">
              {/* Audio Player */}
              {selectedCall.recordingUrl && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Recording</p>
                  <audio controls className="w-full" src={selectedCall.recordingUrl} />
                </div>
              )}

              {/* Risk + Compliance */}
              <div className="flex items-center gap-6">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Risk Score</p>
                  <p className="text-xl font-medium" style={{ color: getRiskColor(selectedCall.riskScore) }}>
                    {selectedCall.riskScore}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Result</p>
                  <Badge
                    className="border-0 capitalize"
                    style={
                      selectedCall.employeeCompliance === "passed"
                        ? { backgroundColor: "#f0fdf4", color: "#22c55e" }
                        : selectedCall.employeeCompliance === "failed"
                        ? { backgroundColor: "#fef2f2", color: "#ef4444" }
                        : { backgroundColor: "#fffbeb", color: "#f59e0b" }
                    }
                  >
                    {selectedCall.employeeCompliance || "—"}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Duration</p>
                  <p className="text-sm">{selectedCall.duration}</p>
                </div>
              </div>

              {/* AI Summary */}
              {selectedCall.aiSummary && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">AI Summary</p>
                  <p className="text-sm text-foreground bg-muted/30 rounded p-3">{selectedCall.aiSummary}</p>
                </div>
              )}

              {/* Flags */}
              {selectedCall.flags && selectedCall.flags.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Flags</p>
                  <div className="flex flex-wrap gap-1">
                    {selectedCall.flags.map((flag, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {flag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Transcript */}
              {selectedCall.transcript && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">Transcript</p>
                  <div className="space-y-1 max-h-64 overflow-y-auto border rounded p-2">
                    {selectedCall.transcript.split('\n').filter(Boolean).map((line, i) => {
                      const isUser = line.startsWith('USER:');
                      return (
                        <div
                          key={i}
                          className={`text-xs p-2 rounded ${
                            isUser
                              ? 'bg-primary/10 text-foreground ml-8'
                              : 'bg-muted/30 text-muted-foreground mr-8'
                          }`}
                        >
                          {line}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
