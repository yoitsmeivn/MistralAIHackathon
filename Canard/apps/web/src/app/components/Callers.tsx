import { useState, useEffect } from "react";
import { Plus, Search, Edit, Trash2, Phone } from "lucide-react";
import { motion } from "motion/react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
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
import type { Caller } from "../types";
import { getCallers } from "../services/api";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const getInitials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

export function Callers() {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [callers, setCallers] = useState<Caller[]>([]);
  const [loading, setLoading] = useState(true);

  const [formData, setFormData] = useState({
    personaName: "",
    personaRole: "",
    personaCompany: "",
    phoneNumber: "",
    attackType: "",
    description: "",
  });

  useEffect(() => {
    getCallers().then((data) => {
      setCallers(data);
      setLoading(false);
    });
  }, []);

  const handleCreateCaller = () => {
    const newCaller: Caller = {
      id: String(callers.length + 1),
      ...formData,
      isActive: true,
      totalCalls: 0,
      avgSuccessRate: 0,
    };
    setCallers([...callers, newCaller]);
    setShowModal(false);
    setFormData({
      personaName: "",
      personaRole: "",
      personaCompany: "",
      phoneNumber: "",
      attackType: "",
      description: "",
    });
  };

  const filteredCallers = callers.filter(
    (caller) =>
      caller.personaName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      caller.personaRole.toLowerCase().includes(searchTerm.toLowerCase()) ||
      caller.attackType.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            Caller Profiles
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage vishing personas for security testing
          </p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="w-4 h-4" />
          New Profile
        </Button>
      </motion.div>

      {/* Search */}
      <motion.div className="mb-6 relative max-w-sm" variants={item}>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search profiles..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9"
        />
      </motion.div>

      {/* Callers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredCallers.map((caller) => (
          <motion.div key={caller.id} variants={item}>
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-5 pb-5">
                <div className="flex items-start gap-4">
                  {/* Avatar */}
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 text-sm font-medium"
                    style={{ backgroundColor: "#fdfbe1", color: "#252a39" }}
                  >
                    {getInitials(caller.personaName)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-1">
                      <div className="min-w-0">
                        <h3 className="text-sm font-medium truncate text-foreground">
                          {caller.personaName}
                        </h3>
                        <p className="text-xs text-muted-foreground">
                          {caller.personaRole}
                        </p>
                        <p className="text-xs text-muted-foreground/60">
                          {caller.personaCompany}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5 ml-2 shrink-0">
                        {caller.isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        )}
                        <button className="text-muted-foreground/40 hover:text-muted-foreground transition-colors">
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button className="text-muted-foreground/40 hover:text-red-400 transition-colors">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 my-2">
                      <Phone className="w-3 h-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        {caller.phoneNumber}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 mb-3">
                      <Badge
                        variant="secondary"
                        className="text-xs font-normal"
                      >
                        {caller.attackType}
                      </Badge>
                    </div>

                    <p className="text-xs text-muted-foreground mb-4 line-clamp-2">
                      {caller.description}
                    </p>

                    <div className="flex items-center gap-6 pt-3 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground mb-0.5">
                          Total Calls
                        </p>
                        <p className="text-sm font-medium text-foreground">
                          {caller.totalCalls}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-0.5">
                          Success Rate
                        </p>
                        <p
                          className="text-sm font-medium"
                          style={{
                            color:
                              caller.avgSuccessRate >= 70
                                ? "#ef4444"
                                : caller.avgSuccessRate >= 50
                                  ? "#f59e0b"
                                  : "#22c55e",
                          }}
                        >
                          {caller.avgSuccessRate}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Create Caller Dialog */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>New Caller Profile</DialogTitle>
            <DialogDescription>
              Create a new vishing persona for testing
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {[
              {
                label: "Persona Name",
                field: "personaName",
                placeholder: "e.g., John Mitchell",
              },
              {
                label: "Persona Role",
                field: "personaRole",
                placeholder: "e.g., IT Support Technician",
              },
              {
                label: "Persona Company",
                field: "personaCompany",
                placeholder: "e.g., TechSupport Solutions",
              },
              {
                label: "Phone Number",
                field: "phoneNumber",
                placeholder: "+1 (555) 123-4567",
              },
            ].map(({ label, field, placeholder }) => (
              <div key={field}>
                <label className="block text-xs text-muted-foreground mb-1.5">
                  {label}
                </label>
                <Input
                  value={formData[field as keyof typeof formData]}
                  onChange={(e) =>
                    setFormData({ ...formData, [field]: e.target.value })
                  }
                  placeholder={placeholder}
                />
              </div>
            ))}

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Attack Type
              </label>
              <Select
                value={formData.attackType}
                onValueChange={(val) =>
                  setFormData({ ...formData, attackType: val })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an attack type" />
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
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 bg-input-background resize-none"
                placeholder="Describe the persona's approach and tactics..."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateCaller}
              disabled={
                !formData.personaName ||
                !formData.personaRole ||
                !formData.attackType
              }
            >
              Create Profile
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
