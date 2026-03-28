const API_BASE = "/api";

export async function createSession(userId: string, sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/apps/green_agent/users/${userId}/sessions/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export interface AgentEvent {
  content?: {
    parts?: Array<{ text?: string }>;
    role?: string;
  };
  author?: string;
}

export type MessagePart =
  | { text: string }
  | { inline_data: { mime_type: string; data: string } };

export async function runAgent(
  userId: string,
  sessionId: string,
  parts: MessagePart[]
): Promise<AgentEvent[]> {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      app_name: "green_agent",
      user_id: userId,
      session_id: sessionId,
      new_message: { role: "user", parts },
    }),
  });
  if (!res.ok) {
    throw new Error(`Agent API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function extractAgentText(events: AgentEvent[]): string {
  const parts: string[] = [];
  for (const evt of events) {
    if (evt.content?.role === "model" && evt.content.parts) {
      for (const p of evt.content.parts) {
        if (p.text) parts.push(p.text);
      }
    }
  }
  return parts.join("\n");
}
