import { useState, useEffect, useRef, useMemo } from "react";
import { Search, Activity, History, ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
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
import { useAuth } from "../contexts/AuthContext";

// --- Types ---
interface CallItem {
  id: string;
  employeeName: string;
  callerName: string;
  campaignName: string;
  status: string;
  startedAt: string;
  duration: string;
  durationSeconds: number | null;
  riskScore: number;
  employeeCompliance: string;
  transcript: string;
  flags: string[];
  aiSummary: string;
}

// --- Helpers ---
const isLive = (status: string) =>
  status === "in-progress" || status === "ringing";

const statusBadgeStyle = (status: string) => {
  if (isLive(status)) return { backgroundColor: "#eff6ff", color: "#3b82f6" };
  if (status === "completed") return { backgroundColor: "#f0fdf4", color: "#22c55e" };
  return { backgroundColor: "#fef2f2", color: "#ef4444" };
};

const statusLabel = (status: string) => {
  if (status === "in-progress") return "In Progress";
  if (status === "ringing") return "Ringing";
  return status.charAt(0).toUpperCase() + status.slice(1);
};

const formatStartedAt = (iso: string) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
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

// --- Live Transcript via SSE ---
function LiveCallTranscript({ callId, token }: { callId: string; token: string }) {
  const [messages, setMessages] = useState<{ sender: "agent" | "user"; text: string }[]>([]);
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    const connect = async () => {
      try {
        const res = await fetch(`/api/monitor/stream/${callId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok || !res.body) return;
        if (!cancelled) setConnected(true);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!cancelled) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const payload = JSON.parse(line.slice(6));
              if (payload.type === "user_speech" && payload.data?.text) {
                setMessages((prev) => [...prev, { sender: "user", text: payload.data.text }]);
              } else if (payload.type === "agent_reply" && payload.data?.text) {
                setMessages((prev) => [...prev, { sender: "agent", text: payload.data.text }]);
              }
            } catch {
              /* ignore malformed lines */
            }
          }
        }
      } catch {
        /* ignore network errors */
      } finally {
        if (!cancelled) setConnected(false);
      }
    };

    connect();
    return () => {
      cancelled = true;
    };
  }, [callId, token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] px-2">
      {/* Connection status */}
      <div
        className={`flex items-center justify-between px-5 py-4 rounded-xl border mt-2 mb-4 mx-2 transition-colors duration-500 ${
          connected
            ? "bg-emerald-500/10 border-emerald-500/20"
            : "bg-amber-500/10 border-amber-500/20"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="relative flex h-3 w-3">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                connected ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                connected ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
          </div>
          <span
            className={`text-sm font-semibold tracking-wide ${
              connected
                ? "text-emerald-700 dark:text-emerald-400"
                : "text-amber-700 dark:text-amber-400"
            }`}
          >
            {connected ? "LIVE CONNECTION ACTIVE" : "CONNECTING TO FEED..."}
          </span>
        </div>
      </div>

      {/* Transcript scroll area */}
      <div className="flex-1 overflow-y-auto space-y-6 px-4 pb-8">
        {messages.length === 0 && connected && (
          <p className="text-sm text-center text-muted-foreground italic pt-4">
            Waiting for speech...
          </p>
        )}
        {messages.map((msg, i) => {
          const isUser = msg.sender === "user";
          return (
            <div key={i} className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
              <div className={`flex flex-col max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
                <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-1 px-1">
                  {isUser ? "Target" : "AI Agent"}
                </span>
                <div
                  className={`px-4 py-3 text-sm shadow-sm ${
                    isUser
                      ? "bg-[#252a39] text-white rounded-2xl rounded-tr-sm"
                      : "bg-muted/80 border border-black/5 text-foreground rounded-2xl rounded-tl-sm"
                  }`}
                >
                  <p className="leading-relaxed">{msg.text}</p>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

// --- Past Call Transcript ---
function PastCallTranscript({ call }: { call: CallItem }) {
  const messages = useMemo(() => {
    if (!call.transcript) return [];
    return call.transcript
      .split("\n")
      .filter((l) => l.trim())
      .map((line) => {
        if (line.startsWith("Agent:"))
          return { sender: "agent" as const, text: line.slice(6).trim() };
        if (line.startsWith("User:"))
          return { sender: "user" as const, text: line.slice(5).trim() };
        return null;
      })
      .filter((x): x is { sender: "agent" | "user"; text: string } => x !== null);
  }, [call.transcript]);

  return (
    <div className="flex flex-col h-[calc(100vh-160px)] px-2">
      <div className="flex flex-col gap-1 pb-4 mb-4 mt-2 px-2 border-b">
        <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
          <History className="size-4 text-muted-foreground" />
          Call Recording &amp; Transcript
        </h3>
        <p className="text-xs text-muted-foreground tracking-wide font-mono">
          CALL ID: {call.id}
        </p>
        {call.aiSummary && (
          <p className="text-xs text-muted-foreground mt-1 italic">{call.aiSummary}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 px-4 pb-8">
        {messages.length === 0 && (
          <p className="text-sm text-center text-muted-foreground italic pt-4">
            No transcript available.
          </p>
        )}
        {messages.map((msg, i) => {
          const isUser = msg.sender === "user";
          return (
            <div key={i} className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
              <div className={`flex flex-col max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
                <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mb-1 px-1">
                  {isUser ? "Target" : "AI Agent"}
                </span>
                <div
                  className={`px-4 py-3 text-sm shadow-sm ${
                    isUser
                      ? "bg-[#252a39] text-white rounded-2xl rounded-tr-sm"
                      : "bg-muted/80 border border-black/5 text-foreground rounded-2xl rounded-tl-sm"
                  }`}
                >
                  <p className="leading-relaxed">{msg.text}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// --- Main Page ---
export function CallMonitoring() {
  const { session } = useAuth();
  const token = session?.access_token ?? "";

  const [allCalls, setAllCalls] = useState<CallItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCall, setSelectedCall] = useState<CallItem | null>(null);

  // Fetch all calls, split into live/past
  useEffect(() => {
    if (!token) return;

    const fetchCalls = async () => {
      try {
        const res = await fetch("/api/calls/?limit=200", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data: CallItem[] = await res.json();
        setAllCalls(data);
      } catch {
        /* ignore */
      }
    };

    fetchCalls();
    const interval = setInterval(fetchCalls, 5000);
    return () => clearInterval(interval);
  }, [token]);

  const liveCalls = allCalls.filter((c) => isLive(c.status));
  const pastCalls = allCalls.filter((c) => !isLive(c.status));

  const filterCalls = (calls: CallItem[]) =>
    calls.filter(
      (c) =>
        c.employeeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.campaignName.toLowerCase().includes(searchTerm.toLowerCase())
    );

  const renderTable = (calls: CallItem[], showDuration: boolean) => (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="pl-6">Target</TableHead>
            <TableHead>Campaign</TableHead>
            <TableHead>Caller</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            {showDuration && <TableHead>Duration</TableHead>}
            {showDuration && <TableHead>Risk</TableHead>}
            <TableHead className="w-16" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {calls.length === 0 ? (
            <TableRow>
              <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                No calls found.
              </TableCell>
            </TableRow>
          ) : (
            calls.map((call) => (
              <TableRow
                key={call.id}
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setSelectedCall(call)}
              >
                <TableCell className="pl-6 font-medium text-foreground">
                  {call.employeeName || "—"}
                </TableCell>
                <TableCell className="max-w-36">
                  <p className="truncate text-muted-foreground">{call.campaignName || "—"}</p>
                </TableCell>
                <TableCell className="text-muted-foreground text-sm">
                  {call.callerName || "—"}
                </TableCell>
                <TableCell>
                  <Badge
                    className="capitalize border-0 font-medium"
                    style={statusBadgeStyle(call.status)}
                  >
                    {statusLabel(call.status)}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatStartedAt(call.startedAt)}
                </TableCell>
                {showDuration && (
                  <TableCell className="text-muted-foreground text-sm">
                    {call.duration || "—"}
                  </TableCell>
                )}
                {showDuration && (
                  <TableCell className="text-sm">
                    {call.riskScore > 0 ? (
                      <span
                        className={`font-medium ${
                          call.riskScore >= 70
                            ? "text-red-500"
                            : call.riskScore >= 40
                            ? "text-amber-500"
                            : "text-emerald-600"
                        }`}
                      >
                        {call.riskScore}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </TableCell>
                )}
                <TableCell>
                  <Button variant="ghost" size="sm" className="text-xs">
                    View
                    <ArrowRight className="size-3 ml-1" />
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );

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
          Call Monitoring &amp; Transcripts
        </h1>
        <p className="text-sm text-muted-foreground">
          Monitor ongoing vishing simulations live and review past transcripts.
        </p>
      </motion.div>

      {/* Workspace */}
      <motion.div variants={item}>
        <Tabs defaultValue="live" className="w-full">
          {/* Controls bar */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <TabsList className="bg-muted p-1">
              <TabsTrigger
                value="live"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm px-4"
              >
                <Activity className="size-4 mr-2 text-blue-500" />
                Live Calls
                {liveCalls.length > 0 && (
                  <span className="ml-2 bg-blue-100 text-blue-700 text-xs font-semibold px-1.5 py-0.5 rounded-full">
                    {liveCalls.length}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger
                value="past"
                className="data-[state=active]:bg-background data-[state=active]:shadow-sm px-4"
              >
                <History className="size-4 mr-2" />
                Past Calls
              </TabsTrigger>
            </TabsList>

            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search name or campaign..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
          </div>

          <TabsContent value="live" className="mt-0 outline-hidden">
            {renderTable(filterCalls(liveCalls), false)}
          </TabsContent>

          <TabsContent value="past" className="mt-0 outline-hidden">
            {renderTable(filterCalls(pastCalls), true)}
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Slide-over detail panel */}
      <Sheet open={!!selectedCall} onOpenChange={(open) => !open && setSelectedCall(null)}>
        <SheetContent className="sm:max-w-md w-[420px] border-l outline-hidden">
          {selectedCall && (
            <>
              <SheetHeader className="pb-4">
                <div className="flex items-center justify-between mt-2">
                  <Badge
                    className="capitalize border-0"
                    style={statusBadgeStyle(selectedCall.status)}
                  >
                    {statusLabel(selectedCall.status)}
                  </Badge>
                  {selectedCall.riskScore > 0 && (
                    <span className="text-sm font-medium">
                      Risk:{" "}
                      <span
                        className={
                          selectedCall.riskScore >= 70
                            ? "text-red-500"
                            : selectedCall.riskScore >= 40
                            ? "text-amber-500"
                            : "text-emerald-600"
                        }
                      >
                        {selectedCall.riskScore}
                      </span>
                    </span>
                  )}
                </div>
                <SheetTitle className="text-xl mt-2">
                  {selectedCall.employeeName || "Unknown"}
                </SheetTitle>
                <SheetDescription>
                  {selectedCall.callerName && `${selectedCall.callerName} • `}
                  {selectedCall.campaignName || "No campaign"}
                </SheetDescription>
                {selectedCall.employeeCompliance && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Compliance:{" "}
                    <span className="font-medium">
                      {selectedCall.employeeCompliance.replace(/_/g, " ")}
                    </span>
                  </p>
                )}
              </SheetHeader>

              <Separator className="mb-6 opacity-50" />

              {isLive(selectedCall.status) ? (
                <LiveCallTranscript callId={selectedCall.id} token={token} />
              ) : (
                <PastCallTranscript call={selectedCall} />
              )}
            </>
          )}
        </SheetContent>
      </Sheet>
    </motion.div>
  );
}
