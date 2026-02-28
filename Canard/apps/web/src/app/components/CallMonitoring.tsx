import { useState, useEffect } from "react";
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

// --- Mock Data & Types ---
interface MonitoringCall {
  id: string;
  targetName: string;
  targetPhone: string;
  status: "in_progress" | "completed" | "failed";
  startedAt: string;
  duration?: string;
  campaignName: string;
  riskScore?: number;
}

const mockCalls: MonitoringCall[] = [
  {
    id: "call_live_1",
    targetName: "Sarah Jenkins",
    targetPhone: "+1 (555) 019-2831",
    status: "in_progress",
    startedAt: "Just now",
    campaignName: "Urgent IT Update Scenario",
  },
  {
    id: "call_live_2",
    targetName: "Michael Chen",
    targetPhone: "+1 (555) 012-4910",
    status: "in_progress",
    startedAt: "2m ago",
    campaignName: "HR Compliance Check",
  },
  {
    id: "call_past_1",
    targetName: "David Rodriguez",
    targetPhone: "+1 (555) 091-8823",
    status: "completed",
    startedAt: "Oct 24, 2026 14:30",
    duration: "4m 12s",
    campaignName: "Urgent IT Update Scenario",
    riskScore: 85,
  },
  {
    id: "call_past_2",
    targetName: "Emma Watson",
    targetPhone: "+1 (555) 043-1199",
    status: "failed",
    startedAt: "Oct 24, 2026 11:15",
    duration: "0m 45s",
    campaignName: "CEO Fraud Simulation",
    riskScore: 0,
  },
  {
    id: "call_past_3",
    targetName: "James Wilson",
    targetPhone: "+1 (555) 088-2234",
    status: "completed",
    startedAt: "Oct 23, 2026 09:45",
    duration: "6m 30s",
    campaignName: "HR Compliance Check",
    riskScore: 40,
  }
];

const statusBadgeStyle = (status: string) => {
  switch (status) {
    case "completed":
      return { backgroundColor: "#f0fdf4", color: "#22c55e" };
    case "in_progress":
      return { backgroundColor: "#eff6ff", color: "#3b82f6" };
    case "failed":
      return { backgroundColor: "#fef2f2", color: "#ef4444" };
    default:
      return { backgroundColor: "#f4f4f4", color: "#9ca3af" };
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

// --- Sub-components ---
/**
 * WebSocket Live Call View
 * Manages the WebSocket connection lifecycle to prevent memory leaks.
 */
function LiveCallTranscript({ callId }: { callId: string }) {
  const [messages, setMessages] = useState<{ sender: "ai" | "employee"; text: string }[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Determine the WS protocol based on current origin (mocking the connection url)
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/api/v1/calls/${callId}/stream`;
    
    // Create the WebSocket instance
    // Note: In a real app we would use this. For the mock, we simulate it.
    // const ws = new WebSocket(wsUrl);
    
    let isMounted = true;
    let mockInterval: number;

    // Simulate WS Connection delay
    const connectTimer = setTimeout(() => {
      if (!isMounted) return;
      setIsConnected(true);
      
      // Simulate incoming WebSocket messages
      const initialDialogue: { sender: "ai" | "employee"; text: string }[] = [
        { sender: "ai", text: "Hello, am I speaking with the target?" },
        { sender: "employee", text: "Yes, this is them. Who is calling?" },
        { sender: "ai", text: "This is IT Support. We need you to verify your credentials immediately due to a security breach." }
      ];
      
      let msgIndex = 0;
      mockInterval = window.setInterval(() => {
        if (!isMounted) return;
        if (msgIndex < initialDialogue.length) {
          const nextMsg = initialDialogue[msgIndex];
          if (nextMsg) {
             setMessages(prev => [...prev, nextMsg]);
          }
          msgIndex++;
        } else {
          // Stop simulation when done
          clearInterval(mockInterval);
        }
      }, 2000);
    }, 1500);

    // CLEANUP: Unmount lifecycle.
    // Very important to close WebSocket explicitly to prevent memory leaks and zombie connections.
    return () => {
      isMounted = false;
      clearTimeout(connectTimer);
      clearInterval(mockInterval);
      /*
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
      */
      console.log(`[WebSocket] Closed connection gracefully for call: ${callId} on unmount.`);
    };
  }, [callId]);

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      {/* Connection State Header */}
      <div className="flex items-center gap-2 pb-4 border-b">
        <div className="relative flex h-3 w-3">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isConnected ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
          <span className={`relative inline-flex rounded-full h-3 w-3 ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
        </div>
        <span className="text-sm font-medium text-muted-foreground">
          {isConnected ? "Live Feed Active" : "Connecting to live feed..."}
        </span>
      </div>

      {/* Transcript Scroll Area */}
      <div className="flex-1 overflow-y-auto pt-6 space-y-4 pr-2">
        {messages.length === 0 && isConnected && (
          <p className="text-sm text-center text-muted-foreground italic">Waiting for audio...</p>
        )}
        
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.sender === 'employee' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
              msg.sender === 'employee' 
                ? 'bg-[#252a39] text-white rounded-tr-sm' 
                : 'bg-muted text-foreground rounded-tl-sm'
            }`}>
              <p className="text-xs opacity-70 mb-1">{msg.sender === 'employee' ? 'Target' : 'AI Agent'}</p>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Static Past Call View
 * Renders a fixed array of messages.
 */
function PastCallTranscript({ callId }: { callId: string }) {
  // Mock static transcript data based on past call
  const mockTranscript = [
    { sender: "ai", text: "Hi, I'm calling from corporate IT. Is this David?" },
    { sender: "employee", text: "Yes, speaking." },
    { sender: "ai", text: "Great. We're doing a mandatory password rotation. I need your current password to bypass the 2FA prompt." },
    { sender: "employee", text: "Uh, I'm pretty sure IT policies prohibit sharing passwords over the phone." },
    { sender: "ai", text: "This is an emergency override from the CTO's office. You need to provide it now or you'll be locked out." },
    { sender: "employee", text: "I'll have to verify this with my manager first. Goodbye." }
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      <div className="pb-4 border-b">
        <h3 className="font-medium text-foreground">Call Recording & Transcript</h3>
        <p className="text-xs text-muted-foreground">Call ID: {callId}</p>
      </div>
      
      <div className="flex-1 overflow-y-auto pt-6 space-y-4 pr-2">
        {mockTranscript.map((msg, i) => (
          <div key={i} className={`flex ${msg.sender === 'employee' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
              msg.sender === 'employee' 
                ? 'bg-[#252a39] text-white rounded-tr-sm' 
                : 'bg-muted text-foreground rounded-tl-sm'
            }`}>
              <p className="text-xs opacity-70 mb-1">{msg.sender === 'employee' ? 'Employee' : 'AI Agent'}</p>
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Page Component ---
export function CallMonitoring() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCall, setSelectedCall] = useState<MonitoringCall | null>(null);

  const filterCalls = (calls: MonitoringCall[], isLive: boolean) => 
    calls.filter(c => {
      const isStatusMatch = isLive ? c.status === "in_progress" : c.status !== "in_progress";
      const isSearchMatch = c.targetName.toLowerCase().includes(searchTerm.toLowerCase()) || 
                            c.targetPhone.includes(searchTerm);
      return isStatusMatch && isSearchMatch;
    });

  const renderTable = (filteredCalls: MonitoringCall[]) => (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="pl-6">Target</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>Campaign</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            {filteredCalls.some(c => c.duration) && <TableHead>Duration</TableHead>}
            <TableHead className="w-16" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredCalls.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                No calls found.
              </TableCell>
            </TableRow>
          ) : (
            filteredCalls.map((call) => (
              <TableRow key={call.id} className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={() => setSelectedCall(call)}>
                <TableCell className="pl-6 font-medium text-foreground">
                  {call.targetName}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {call.targetPhone}
                </TableCell>
                <TableCell className="max-w-36">
                  <p className="truncate text-muted-foreground">{call.campaignName}</p>
                </TableCell>
                <TableCell>
                  <Badge
                    className="capitalize border-0 font-medium"
                    style={statusBadgeStyle(call.status)}
                  >
                    {call.status.replace("_", " ")}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {call.startedAt}
                </TableCell>
                {call.duration && (
                  <TableCell className="text-muted-foreground text-sm">
                    {call.duration}
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
        <h1 className="text-2xl font-medium mb-1 text-foreground">Call Monitoring & Transcripts</h1>
        <p className="text-sm text-muted-foreground">
          Monitor ongoing vishing simulations live and review past transcripts.
        </p>
      </motion.div>

      {/* Workspace */}
      <motion.div variants={item}>
        <Tabs defaultValue="live" className="w-full">
          {/* Controls Bar */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <TabsList className="bg-muted p-1">
              <TabsTrigger value="live" className="data-[state=active]:bg-background data-[state=active]:shadow-sm px-4">
                <Activity className="size-4 mr-2 text-blue-500" />
                Live Calls
              </TabsTrigger>
              <TabsTrigger value="past" className="data-[state=active]:bg-background data-[state=active]:shadow-sm px-4">
                <History className="size-4 mr-2" />
                Past Calls
              </TabsTrigger>
            </TabsList>

            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search name or phone..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
          </div>

          <TabsContent value="live" className="mt-0 outline-hidden">
            {renderTable(filterCalls(mockCalls, true))}
          </TabsContent>

          <TabsContent value="past" className="mt-0 outline-hidden">
            {renderTable(filterCalls(mockCalls, false))}
          </TabsContent>
        </Tabs>
      </motion.div>

      {/* Slide-over Detail Panel */}
      <Sheet open={!!selectedCall} onOpenChange={(open) => !open && setSelectedCall(null)}>
        <SheetContent className="sm:max-w-md w-[400px] border-l outline-hidden">
          {selectedCall && (
            <>
              <SheetHeader className="pb-4">
                <div className="flex items-center justify-between mt-2">
                  <Badge
                    className="capitalize border-0"
                    style={statusBadgeStyle(selectedCall.status)}
                  >
                    {selectedCall.status.replace("_", " ")}
                  </Badge>
                  {selectedCall.riskScore !== undefined && (
                    <span className="text-sm font-medium">Risk: {selectedCall.riskScore}%</span>
                  )}
                </div>
                <SheetTitle className="text-xl mt-2">{selectedCall.targetName}</SheetTitle>
                <SheetDescription>
                  {selectedCall.targetPhone} • {selectedCall.campaignName}
                </SheetDescription>
              </SheetHeader>

              <Separator className="mb-6 opacity-50" />

              {/* Dynamic Content based on status */}
              {selectedCall.status === "in_progress" ? (
                <LiveCallTranscript callId={selectedCall.id} />
              ) : (
                <PastCallTranscript callId={selectedCall.id} />
              )}
            </>
          )}
        </SheetContent>
      </Sheet>
    </motion.div>
  );
}
