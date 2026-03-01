import { useState, useEffect, useMemo, useCallback } from "react";
import { Link } from "react-router";
import { Plus, Search, Play, Pause, Trash2, Rocket, Loader2 } from "lucide-react";
import { motion } from "motion/react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Progress } from "./ui/progress";
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
import type { Campaign, Script, Caller, Employee } from "../types";
import {
  getCampaigns,
  createCampaign,
  updateCampaign,
  deleteCampaign,
  getCampaignScripts,
  getCallers,
  getEmployees,
  launchCampaign,
} from "../services/api";

const statusStyle = (status: string) => {
  switch (status) {
    case "running":
      return "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-50";
    case "active":
      return "bg-[#fdfbe1] text-foreground border-[#fdfbe1] hover:bg-[#fdfbe1]";
    case "paused":
      return "bg-orange-50 text-orange-700 border-orange-50 hover:bg-orange-50";
    case "completed":
      return "bg-muted text-muted-foreground border-muted hover:bg-muted";
    case "draft":
      return "bg-blue-50 text-indigo-600 border-blue-50 hover:bg-blue-50";
    default:
      return "";
  }
};

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export function Campaigns() {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    attackVector: "",
    scheduledAt: "",
  });

  // Launch dialog state
  const [showLaunchDialog, setShowLaunchDialog] = useState(false);
  const [launchCampaignId, setLaunchCampaignId] = useState<string | null>(null);
  const [launchScripts, setLaunchScripts] = useState<Script[]>([]);
  const [callers, setCallers] = useState<Caller[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [scriptMode, setScriptMode] = useState<"single" | "all">("all");
  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [selectedCallerId, setSelectedCallerId] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [launching, setLaunching] = useState(false);

  const departments = useMemo(() => {
    const deptMap = new Map<string, number>();
    for (const e of employees) {
      if (e.department) {
        deptMap.set(e.department, (deptMap.get(e.department) || 0) + 1);
      }
    }
    return Array.from(deptMap.entries()).map(([name, count]) => ({ name, count }));
  }, [employees]);

  const handleOpenLaunchDialog = async (campaign: Campaign) => {
    setLaunchCampaignId(campaign.id);
    setShowLaunchDialog(true);
    const [scripts, c, e] = await Promise.all([
      getCampaignScripts(campaign.id),
      getCallers(),
      getEmployees(),
    ]);
    setLaunchScripts(scripts);
    setCallers(c.filter((x) => x.isActive));
    setEmployees(e.filter((x) => x.isActive));
  };

  const handleLaunch = async () => {
    if (!launchCampaignId) return;
    if (scriptMode === "single" && (!selectedScriptId || !selectedCallerId)) return;
    setLaunching(true);
    try {
      await launchCampaign(launchCampaignId, {
        script_id: scriptMode === "single" ? selectedScriptId : undefined,
        caller_id: scriptMode === "single" ? selectedCallerId : undefined,
        department: selectedDepartment && selectedDepartment !== "__all__" ? selectedDepartment : undefined,
      });
      setShowLaunchDialog(false);
      setLaunchCampaignId(null);
      setScriptMode("all");
      setSelectedScriptId("");
      setSelectedCallerId("");
      setSelectedDepartment("");
      loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to launch campaign");
    } finally {
      setLaunching(false);
    }
  };

  const loadCampaigns = useCallback(() => {
    setLoading(true);
    getCampaigns()
      .then((data) => {
        setCampaigns(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleCreateCampaign = async () => {
    try {
      await createCampaign({
        name: formData.name,
        description: formData.description || undefined,
        attack_vector: formData.attackVector || undefined,
      });
      setShowModal(false);
      setFormData({ name: "", description: "", attackVector: "", scheduledAt: "" });
      loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create campaign");
    }
  };

  const handleToggleStatus = async (campaign: Campaign) => {
    const newStatus = campaign.status === "active" || campaign.status === "in_progress"
      ? "paused"
      : "in_progress";
    try {
      await updateCampaign(campaign.id, { status: newStatus });
      loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to update campaign");
    }
  };

  const handleDeleteCampaign = async (id: string) => {
    try {
      await deleteCampaign(id);
      loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete campaign");
    }
  };

  const filteredCampaigns = campaigns.filter((campaign) => {
    const matchesSearch =
      campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      campaign.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      filterStatus === "all" || campaign.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Header */}
      <motion.div
        className="mb-8 flex items-center justify-between"
        variants={item}
      >
        <div>
          <h1 className="text-2xl font-medium mb-1 text-foreground">
            Campaigns
          </h1>
          <p className="text-sm text-muted-foreground">
            Create and manage vishing test campaigns
          </p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4" />
          New Campaign
        </Button>
      </motion.div>

      {/* Search and Filter */}
      <motion.div className="mb-6 flex gap-3" variants={item}>
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search campaigns..."
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
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </motion.div>

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredCampaigns.map((campaign) => (
          <motion.div key={campaign.id} variants={item}>
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-5 pb-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0 mr-3">
                    <Link
                      to={`/campaigns/${campaign.id}`}
                      className="text-sm font-medium hover:opacity-70 transition-opacity block truncate text-foreground"
                    >
                      {campaign.name}
                    </Link>
                    <p className="text-xs mt-0.5 truncate text-muted-foreground">
                      {campaign.description}
                    </p>
                  </div>
                  <Badge className={`${statusStyle(campaign.status)} border`}>
                    {campaign.status}
                  </Badge>
                </div>

                <div className="flex items-center gap-2 mb-4">
                  <Badge variant="outline" className="text-xs font-normal">
                    {campaign.attackVector}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    · Scheduled{" "}
                    {new Date(campaign.scheduledAt).toLocaleDateString()}
                  </span>
                </div>

                {campaign.status !== "draft" && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="text-foreground">
                        {campaign.completedCalls}/{campaign.totalCalls} calls
                      </span>
                    </div>
                    <Progress
                      value={
                        (campaign.completedCalls / campaign.totalCalls) * 100
                      }
                      className="h-1.5"
                    />
                  </div>
                )}

                {campaign.avgRiskScore > 0 && (
                  <div className="mb-4 flex items-center justify-between px-3 py-2 rounded-lg bg-muted/50">
                    <span className="text-xs text-muted-foreground">
                      Avg Risk Score
                    </span>
                    <span
                      className="text-sm font-medium"
                      style={{
                        color:
                          campaign.avgRiskScore >= 70
                            ? "#ef4444"
                            : campaign.avgRiskScore >= 50
                              ? "#f59e0b"
                              : "#22c55e",
                      }}
                    >
                      {campaign.avgRiskScore}%
                    </span>
                  </div>
                )}

                <div className="flex gap-2 pt-4 border-t">
                  {(campaign.status === "draft" || campaign.status === "paused") && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleOpenLaunchDialog(campaign)}
                    >
                      <Play className="w-3.5 h-3.5" /> Launch
                    </Button>
                  )}
                  {campaign.status === "running" && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      disabled
                    >
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Running...
                    </Button>
                  )}
                  {(campaign.status === "active" || campaign.status === "completed") && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      disabled={campaign.status === "completed"}
                      onClick={() => handleToggleStatus(campaign)}
                    >
                      <Pause className="w-3.5 h-3.5" /> {campaign.status === "completed" ? "Completed" : "Pause"}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleDeleteCampaign(campaign.id)}
                  >
                    <Trash2 className="w-3.5 h-3.5 text-muted-foreground" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Create Campaign Dialog */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>New Campaign</DialogTitle>
            <DialogDescription>
              Create a new vishing test campaign
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Campaign Name
              </label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="e.g., IT Support Impersonation"
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 bg-input-background resize-none"
                placeholder="Describe the campaign objectives..."
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Attack Vector
              </label>
              <Select
                value={formData.attackVector}
                onValueChange={(val) =>
                  setFormData({ ...formData, attackVector: val })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an attack vector" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Technical Support Scam">
                    Technical Support Scam
                  </SelectItem>
                  <SelectItem value="Authority Impersonation">
                    Authority Impersonation
                  </SelectItem>
                  <SelectItem value="Urgency & Fear">
                    Urgency & Fear
                  </SelectItem>
                  <SelectItem value="Internal Authority">
                    Internal Authority
                  </SelectItem>
                  <SelectItem value="Financial Scam">Financial Scam</SelectItem>
                  <SelectItem value="Prize/Reward">Prize/Reward</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Scheduled Start
              </label>
              <Input
                type="datetime-local"
                value={formData.scheduledAt}
                onChange={(e) =>
                  setFormData({ ...formData, scheduledAt: e.target.value })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateCampaign}
              disabled={!formData.name || !formData.attackVector}
            >
              Create Campaign
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
              <label className="block text-xs text-muted-foreground mb-1.5">
                Script Mode
              </label>
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
                    Randomly assign from {launchScripts.length} scripts
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

            {/* Single-script selectors */}
            {scriptMode === "single" && (
              <>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">
                    Script
                  </label>
                  <Select value={selectedScriptId} onValueChange={setSelectedScriptId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a script" />
                    </SelectTrigger>
                    <SelectContent>
                      {launchScripts.map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.name}{" "}
                          <span className="text-muted-foreground">({s.difficulty})</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-xs text-muted-foreground mb-1.5">
                    Caller
                  </label>
                  <Select value={selectedCallerId} onValueChange={setSelectedCallerId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a caller" />
                    </SelectTrigger>
                    <SelectContent>
                      {callers.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.personaName}{" "}
                          <span className="text-muted-foreground">— {c.personaRole}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Department{" "}
                <span className="text-muted-foreground/60">(optional — all employees if blank)</span>
              </label>
              <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
                <SelectTrigger>
                  <SelectValue placeholder="All departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All departments</SelectItem>
                  {departments.map((d) => (
                    <SelectItem key={d.name} value={d.name}>
                      {d.name}{" "}
                      <span className="text-muted-foreground">({d.count} employees)</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLaunchDialog(false)}>
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
    </motion.div>
  );
}
