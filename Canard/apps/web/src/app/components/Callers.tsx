import { useState, useEffect } from "react";
import { Plus, Search, Edit, Trash2, Phone, Volume2 } from "lucide-react";
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
import { getCallers, createCaller, updateCaller, deleteCaller } from "../services/api";

// ElevenLabs voices — curated set for phone call personas
const ELEVENLABS_VOICES = [
  { id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel", description: "Calm, young female" },
  { id: "AZnzlk1XvdvUeBnXmlld", name: "Domi", description: "Strong, confident female" },
  { id: "EXAVITQu4vr4xnSDxMaL", name: "Sarah", description: "Soft, warm female" },
  { id: "ErXwobaYiN019PkySvjV", name: "Antoni", description: "Well-rounded male" },
  { id: "nPczCjzI2devNBz1zQrb", name: "Brian", description: "Deep, narrating male" },
  { id: "TxGEqnHWrfWFTfGW9XjX", name: "Josh", description: "Deep, authoritative male" },
  { id: "VR6AewLTigWG4xSOukaG", name: "Arnold", description: "Crisp, confident male" },
  { id: "pNInz6obpgDQGcFmaJgB", name: "Adam", description: "Deep, narrative male" },
  { id: "yoZ06aMxZJJ28mfd3POQ", name: "Sam", description: "Raspy, authentic male" },
  { id: "onwK4e9ZLuTAKqWW03F9", name: "Daniel", description: "Authoritative British male" },
  { id: "XB0fDUnXU5powFXDhCwa", name: "Charlotte", description: "Warm, Swedish-accented female" },
  { id: "Xb7hH8MSUJpSbSDYk0k2", name: "Alice", description: "Confident, middle-aged female" },
] as const;

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

const emptyFormData = {
  personaName: "",
  personaRole: "",
  personaCompany: "",
  phoneNumber: "",
  voiceId: "",
  personaPrompt: "",
};

export function Callers() {
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [callers, setCallers] = useState<Caller[]>([]);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({ ...emptyFormData });

  const loadCallers = () => {
    setLoading(true);
    getCallers()
      .then((data) => {
        setCallers(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadCallers();
  }, []);

  const openCreate = () => {
    setEditingId(null);
    setFormData({ ...emptyFormData });
    setShowModal(true);
  };

  const openEdit = (caller: Caller) => {
    setEditingId(caller.id);
    setFormData({
      personaName: caller.personaName,
      personaRole: caller.personaRole,
      personaCompany: caller.personaCompany,
      phoneNumber: caller.phoneNumber,
      voiceId: caller.voiceProfile?.voice_id || "",
      personaPrompt: caller.personaPrompt || "",
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      const voiceName = ELEVENLABS_VOICES.find((v) => v.id === formData.voiceId)?.name;
      const voiceProfile = formData.voiceId
        ? { voice_id: formData.voiceId, voice_name: voiceName }
        : undefined;
      if (editingId) {
        await updateCaller(editingId, {
          persona_name: formData.personaName,
          persona_role: formData.personaRole || undefined,
          persona_company: formData.personaCompany || undefined,
          phone_number: formData.phoneNumber || undefined,
          voice_profile: voiceProfile || {},
          persona_prompt: formData.personaPrompt || undefined,
        });
      } else {
        await createCaller({
          persona_name: formData.personaName,
          persona_role: formData.personaRole || undefined,
          persona_company: formData.personaCompany || undefined,
          phone_number: formData.phoneNumber || undefined,
          voice_profile: voiceProfile,
          persona_prompt: formData.personaPrompt || undefined,
        });
      }
      setShowModal(false);
      setEditingId(null);
      setFormData({ ...emptyFormData });
      loadCallers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save caller");
    }
  };

  const handleDeleteCaller = async (id: string) => {
    try {
      await deleteCaller(id);
      loadCallers();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete caller");
    }
  };

  const filteredCallers = callers.filter(
    (caller) =>
      caller.personaName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      caller.personaRole.toLowerCase().includes(searchTerm.toLowerCase()) ||
      caller.personaCompany.toLowerCase().includes(searchTerm.toLowerCase())
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
        <Button onClick={openCreate}>
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
                        <button
                          className="text-muted-foreground/40 hover:text-muted-foreground transition-colors"
                          onClick={() => openEdit(caller)}
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          className="text-muted-foreground/40 hover:text-red-400 transition-colors"
                          onClick={() => handleDeleteCaller(caller.id)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 my-2">
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3 h-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {caller.phoneNumber}
                        </span>
                      </div>
                      {caller.voiceProfile?.voice_name && (
                        <Badge variant="outline" className="text-xs font-normal gap-1">
                          <Volume2 className="w-2.5 h-2.5" />
                          {caller.voiceProfile.voice_name}
                        </Badge>
                      )}
                    </div>

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
      <Dialog open={showModal} onOpenChange={(open) => { setShowModal(open); if (!open) setEditingId(null); }}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit Caller Profile" : "New Caller Profile"}</DialogTitle>
            <DialogDescription>
              {editingId ? "Update persona details" : "Create a new vishing persona for testing"}
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
                Voice
              </label>
              <Select
                value={formData.voiceId}
                onValueChange={(val) => setFormData({ ...formData, voiceId: val })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a voice" />
                </SelectTrigger>
                <SelectContent>
                  {ELEVENLABS_VOICES.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.name} — {v.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Character & Speaking Style
              </label>
              <textarea
                className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-y"
                value={formData.personaPrompt}
                onChange={(e) => setFormData({ ...formData, personaPrompt: e.target.value })}
                placeholder="Describe how this persona speaks, their tone, pace, and characteristic phrases..."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowModal(false); setEditingId(null); }}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!formData.personaName || !formData.personaRole}
            >
              {editingId ? "Save Changes" : "Create Profile"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
