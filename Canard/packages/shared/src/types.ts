type Buffer = Uint8Array;

export interface AgentTextRequest {
  sessionId?: string;
  text: string;
}

export interface AgentTextResponse {
  reply: string;
  sessionId: string;
}

export interface AgentTtsRequest {
  text: string;
  voiceId?: string;
}

export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface Message {
  role: MessageRole;
  content: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
}

export interface ToolCall {
  id: string;
  function: {
    name: string;
    arguments: string;
  };
}

export interface SttResult {
  text: string;
  confidence: number;
  language?: string;
}

export interface SttProvider {
  transcribe(audio: Buffer, options?: SttOptions): Promise<SttResult>;
}

export interface SttOptions {
  language?: string;
  model?: string;
}
