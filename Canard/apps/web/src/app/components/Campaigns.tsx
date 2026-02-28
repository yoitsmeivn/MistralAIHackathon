import { useState, useEffect } from "react";
import { Link } from "react-router";
import { Plus, Search, Play, Pause, Trash2 } from "lucide-react";
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
import type { Campaign } from "../types";
import { getCampaigns } from "../services/api";

const statusStyle = (status: string) => {
  switch (status) {
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

  useEffect(() => {
    getCampaigns().then((data) => {
      setCampaigns(data);
      setLoading(false);
    });
  }, []);

  const handleCreateCampaign = () => {
    const newCampaign: Campaign = {
      id: String(campaigns.length + 1),
      name: formData.name,
      description: formData.description,
      attackVector: formData.attackVector,
      status: "draft",
      scheduledAt: formData.scheduledAt,
      totalCalls: 0,
      completedCalls: 0,
      avgRiskScore: 0,
      createdAt: new Date().toISOString(),
    };
    setCampaigns([...campaigns, newCampaign]);
    setShowModal(false);
    setFormData({ name: "", description: "", attackVector: "", scheduledAt: "" });
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
                  <Button variant="outline" size="sm" className="flex-1">
                    {campaign.status === "active" ? (
                      <>
                        <Pause className="w-3.5 h-3.5" /> Pause
                      </>
                    ) : (
                      <>
                        <Play className="w-3.5 h-3.5" /> Start
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="icon" className="h-8 w-8">
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
    </motion.div>
  );
}
