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

export async function runAgent(
  userId: string,
  sessionId: string,
  message: string
): Promise<AgentEvent[]> {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      appName: "green_agent",
      userId,
      sessionId,
      newMessage: { role: "user", parts: [{ text: message }] },
    }),
  });
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
