import { useState, useEffect } from "react";
import { Plus, Search, Edit, Trash2, FileText, Target, ArrowUpRight } from "lucide-react";
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
import type { Script, ScriptDifficulty } from "../types";
import { getScripts, createScript, updateScript, deleteScript } from "../services/api";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const difficultyColors: Record<ScriptDifficulty, string> = {
  easy: "bg-emerald-100 text-emerald-700",
  medium: "bg-amber-100 text-amber-700",
  hard: "bg-red-100 text-red-700",
};

const emptyFormData = {
  name: "",
  attackType: "",
  difficulty: "medium" as ScriptDifficulty,
  systemPrompt: "",
  description: "",
  objectives: [] as string[],
  escalationSteps: [] as string[],
};

export function Scripts() {
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({ ...emptyFormData });

  const loadScripts = () => {
    setLoading(true);
    getScripts()
      .then((data) => {
        setScripts(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadScripts();
  }, []);

  const openCreate = () => {
    setEditingId(null);
    setFormData({ ...emptyFormData });
    setShowModal(true);
  };

  const openEdit = (script: Script) => {
    setEditingId(script.id);
    setFormData({
      name: script.name,
      attackType: script.attackType,
      difficulty: script.difficulty,
      systemPrompt: script.systemPrompt,
      description: script.description,
      objectives: [...script.objectives],
      escalationSteps: [...script.escalationSteps],
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (editingId) {
        await updateScript(editingId, {
          name: formData.name,
          attack_type: formData.attackType || undefined,
          difficulty: formData.difficulty,
          system_prompt: formData.systemPrompt,
          description: formData.description || undefined,
          objectives: formData.objectives,
          escalation_steps: formData.escalationSteps,
        });
      } else {
        await createScript({
          name: formData.name,
          attack_type: formData.attackType || undefined,
          difficulty: formData.difficulty,
          system_prompt: formData.systemPrompt,
          description: formData.description || undefined,
          objectives: formData.objectives,
          escalation_steps: formData.escalationSteps,
        });
      }
      setShowModal(false);
      setEditingId(null);
      setFormData({ ...emptyFormData });
      loadScripts();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save script");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteScript(id);
      loadScripts();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete script");
    }
  };

  const addListItem = (field: "objectives" | "escalationSteps") => {
    setFormData({ ...formData, [field]: [...formData[field], ""] });
  };

  const updateListItem = (field: "objectives" | "escalationSteps", index: number, value: string) => {
    const updated = [...formData[field]];
    updated[index] = value;
    setFormData({ ...formData, [field]: updated });
  };

  const removeListItem = (field: "objectives" | "escalationSteps", index: number) => {
    const updated = formData[field].filter((_, i) => i !== index);
    setFormData({ ...formData, [field]: updated });
  };

  const filteredScripts = scripts.filter(
    (s) =>
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.attackType.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.difficulty.toLowerCase().includes(searchTerm.toLowerCase())
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
            Attack Scripts
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage vishing scripts and escalation scenarios
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="w-4 h-4" />
          New Script
        </Button>
      </motion.div>

      {/* Search */}
      <motion.div className="mb-6 relative max-w-sm" variants={item}>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search scripts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9"
        />
      </motion.div>

      {/* Scripts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredScripts.map((script) => (
          <motion.div key={script.id} variants={item}>
            <Card className="hover:shadow-md transition-shadow">
              <CardContent className="pt-5 pb-5">
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                    style={{ backgroundColor: "#fdfbe1", color: "#252a39" }}
                  >
                    <FileText className="w-4 h-4" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-1">
                      <div className="min-w-0">
                        <h3 className="text-sm font-medium truncate text-foreground">
                          {script.name}
                        </h3>
                        {script.description && (
                          <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                            {script.description}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 ml-2 shrink-0">
                        {script.isActive && (
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        )}
                        <button
                          className="text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                          onClick={() => openEdit(script)}
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className="text-muted-foreground/40 hover:text-red-400 transition-colors"
                          onClick={() => handleDelete(script.id)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 my-2">
                      {script.attackType && (
                        <Badge
                          variant="secondary"
                          className="text-xs font-normal"
                        >
                          {script.attackType}
                        </Badge>
                      )}
                      <Badge
                        className={`text-xs font-normal border-0 ${difficultyColors[script.difficulty] || difficultyColors.medium}`}
                      >
                        {script.difficulty}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-6 pt-3 border-t">
                      <div className="flex items-center gap-1.5">
                        <Target className="w-3 h-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {script.objectives.length} objective{script.objectives.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <ArrowUpRight className="w-3 h-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {script.escalationSteps.length} escalation step{script.escalationSteps.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Create/Edit Script Dialog */}
      <Dialog open={showModal} onOpenChange={(open) => { setShowModal(open); if (!open) setEditingId(null); }}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Script" : "New Attack Script"}</DialogTitle>
            <DialogDescription>
              {editingId ? "Update script details" : "Create a new vishing script for testing"}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Name
              </label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., IT Support Password Reset"
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Attack Type
              </label>
              <Select
                value={formData.attackType}
                onValueChange={(val) => setFormData({ ...formData, attackType: val })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an attack type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Technical Support Scam">Technical Support Scam</SelectItem>
                  <SelectItem value="Authority Impersonation">Authority Impersonation</SelectItem>
                  <SelectItem value="Urgency & Fear">Urgency &amp; Fear</SelectItem>
                  <SelectItem value="Internal Authority">Internal Authority</SelectItem>
                  <SelectItem value="Financial Scam">Financial Scam</SelectItem>
                  <SelectItem value="Prize/Reward">Prize/Reward</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Difficulty
              </label>
              <Select
                value={formData.difficulty}
                onValueChange={(val) => setFormData({ ...formData, difficulty: val as ScriptDifficulty })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select difficulty" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                System Prompt
              </label>
              <textarea
                value={formData.systemPrompt}
                onChange={(e) => setFormData({ ...formData, systemPrompt: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 bg-input-background resize-none"
                placeholder="The system prompt for the AI caller..."
              />
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 bg-input-background resize-none"
                placeholder="Brief description of this script..."
              />
            </div>

            {/* Objectives — dynamic list */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Objectives
              </label>
              <div className="space-y-2">
                {formData.objectives.map((obj, i) => (
                  <div key={i} className="flex gap-2">
                    <Input
                      value={obj}
                      onChange={(e) => updateListItem("objectives", i, e.target.value)}
                      placeholder={`Objective ${i + 1}`}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0 text-muted-foreground hover:text-red-400"
                      onClick={() => removeListItem("objectives", i)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={() => addListItem("objectives")}>
                  <Plus className="w-3 h-3 mr-1" />
                  Add Objective
                </Button>
              </div>
            </div>

            {/* Escalation Steps — dynamic list */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Escalation Steps
              </label>
              <div className="space-y-2">
                {formData.escalationSteps.map((step, i) => (
                  <div key={i} className="flex gap-2">
                    <Input
                      value={step}
                      onChange={(e) => updateListItem("escalationSteps", i, e.target.value)}
                      placeholder={`Step ${i + 1}`}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="shrink-0 text-muted-foreground hover:text-red-400"
                      onClick={() => removeListItem("escalationSteps", i)}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={() => addListItem("escalationSteps")}>
                  <Plus className="w-3 h-3 mr-1" />
                  Add Step
                </Button>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowModal(false); setEditingId(null); }}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!formData.name || !formData.systemPrompt}
            >
              {editingId ? "Save Changes" : "Create Script"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
