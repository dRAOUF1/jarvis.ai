import type {
  DbProject,
  DbMessage,
  DbMemory,
  Connection,
  ProjectSpec,
  ProfileHandle,
} from "./types.gen";
import type { CatalogApp } from "./api";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_PROJECTS: DbProject[] = [
  {
    id: "mock-sports-coach",
    user_id: "demo-user",
    name: "Sports Coach",
    goal: "Track and improve running performance using Strava data",
    status: "ready",
    failed_stage: null,
    spec: {
      name: "Sports Coach",
      goal: "Track and improve running performance",
      persona: "Motivating and data-driven coach",
      tasks: [
        { title: "Post-run analysis", description: "Break down each run" },
        { title: "Weekly summary", description: "Review training load" },
      ],
      tool_requirements: [
        {
          app: "strava",
          reason: "Activity tracking",
          needed_scopes: ["read"],
          tool_subset: ["get_activities"],
        },
      ],
      success_criteria: ["Personalized feedback after every run"],
      avatar_seed: "sports-coach",
    } as unknown as import("./types.gen").DbProject["spec"],
    runtime_key: "slot-a",
    session_key: "agent:mock-sports-coach:user:demo-user",
    gateway_url: "http://localhost:8080",
    avatar_seed: "sports-coach",
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "mock-inbox-triager",
    user_id: "demo-user",
    name: "Inbox Triager",
    goal: "Prioritize and summarize emails so I focus on what matters",
    status: "provisioning",
    failed_stage: null,
    spec: null,
    runtime_key: null,
    session_key: null,
    gateway_url: null,
    avatar_seed: "inbox-triager",
    created_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: "mock-journal",
    user_id: "demo-user",
    name: "Daily Journal",
    goal: "Help me reflect and capture thoughts daily",
    status: "draft",
    failed_stage: null,
    spec: null,
    runtime_key: null,
    session_key: null,
    gateway_url: null,
    avatar_seed: "daily-journal",
    created_at: new Date(Date.now() - 900000).toISOString(),
  },
];

const MOCK_CATALOG: CatalogApp[] = [
  { app: "strava", display_name: "Strava", description: "Track running, cycling, and other athletic activities", icon: "🏃", default_scopes: ["read:activities"] },
  { app: "gmail", display_name: "Gmail", description: "Read and send emails from your Gmail inbox", icon: "📧", default_scopes: ["gmail.readonly", "gmail.send"] },
  { app: "apple_health", display_name: "Apple Health", description: "Access health and fitness data including steps, sleep, and heart rate", icon: "❤️", default_scopes: ["health.read"] },
  { app: "github", display_name: "GitHub", description: "Manage repositories, issues, pull requests, and code", icon: "🐙", default_scopes: ["repo", "issues"] },
  { app: "notion", display_name: "Notion", description: "Read and write to Notion pages, databases, and notes", icon: "📝", default_scopes: ["read_content", "update_content"] },
  { app: "slack", display_name: "Slack", description: "Send messages and read channels in your Slack workspace", icon: "💬", default_scopes: ["channels:read", "chat:write"] },
  { app: "google_calendar", display_name: "Google Calendar", description: "Read and create events on your Google Calendar", icon: "📅", default_scopes: ["calendar.readonly"] },
  { app: "spotify", display_name: "Spotify", description: "Control playback, browse playlists, and discover music", icon: "🎵", default_scopes: ["user-read-playback-state"] },
];

const MOCK_CONNECTIONS: Connection[] = [
  {
    id: "mock-conn-strava",
    user_id: "demo-user",
    app: "strava",
    status: "connected",
    mcp_url: "http://localhost:9000/mcp/strava",
    available_tools: ["get_activities", "get_activity_detail", "get_athlete_stats"],
  },
];

const MOCK_MEMORY: DbMemory[] = [
  { id: "m1", project_id: "mock-sports-coach", kind: "scraped", content: "User runs 3x per week, typically 5-10km sessions at 5:00-5:09/km pace", created_at: new Date().toISOString() },
  { id: "m2", project_id: "mock-sports-coach", kind: "fact", content: "Longest recent run: 10.1km, 5 days ago", created_at: new Date().toISOString() },
  { id: "m3", project_id: "mock-sports-coach", kind: "preference", content: "Prefers morning runs before work", created_at: new Date().toISOString() },
  { id: "m4", project_id: "mock-sports-coach", kind: "scraped", content: "Also cycles occasionally — 32km ride 8 days ago", created_at: new Date().toISOString() },
  { id: "m5", project_id: "mock-sports-coach", kind: "fact", content: "Weekly mileage avg: ~22km across running and cycling", created_at: new Date().toISOString() },
];

// ---------------------------------------------------------------------------
// Status progression (mock provisioning states advancing over ~6s)
// ---------------------------------------------------------------------------

const STAGE_STARTS = new Map<string, number>();
const STAGES = ["compiling", "connecting", "provisioning", "ingesting", "ready"] as const;

function getMockStatus(id: string): string {
  if (!STAGE_STARTS.has(id)) STAGE_STARTS.set(id, Date.now());
  const elapsed = Date.now() - STAGE_STARTS.get(id)!;
  if (elapsed < 1200) return "compiling";
  if (elapsed < 2400) return "connecting";
  if (elapsed < 3800) return "provisioning";
  if (elapsed < 5200) return "ingesting";
  return "ready";
}

// ---------------------------------------------------------------------------
// SSE stream helpers
// ---------------------------------------------------------------------------

async function* mockShapeStreamGenerator(
  message: string,
  _history: { role: string; content: string }[]
) {
  const delay = (ms: number) =>
    new Promise((r) => setTimeout(r, ms));

  // Initial greeting
  const intro = "Great idea! A sports coach agent sounds awesome. Let me ask a couple of quick questions to get this just right.";
  for (const word of intro.split(" ")) {
    await delay(25);
    yield `data: ${JSON.stringify({ type: "delta", text: word + " " })}\n\n`;
  }

  // Question event
  await delay(100);
  yield `data: ${JSON.stringify({
    type: "question",
    question: {
      field: "goal",
      prompt: "Which sport or activity are you primarily tracking?",
      options: ["Running", "Cycling", "Cross-fit", "Mixed / other"],
    },
  })}\n\n`;

  await delay(200);

  // Spec updates
  yield `data: ${JSON.stringify({
    type: "spec_update",
    spec_update: { name: "Sports Coach", goal: "Track and improve athletic performance" },
  })}\n\n`;

  await delay(150);

  yield `data: ${JSON.stringify({
    type: "spec_update",
    spec_update: {
      persona: "Motivating and data-driven, speaks plainly and celebrates wins",
      tasks: [
        { title: "Post-run breakdown", description: "Analyze pace, heart rate, and effort after each activity" },
        { title: "Weekly training review", description: "Summarize mileage, trends, and recovery needs" },
        { title: "PR tracking", description: "Celebrate personal records and milestone achievements" },
      ],
    },
  })}\n\n`;

  await delay(300);

  // Proposal
  yield `data: ${JSON.stringify({
    type: "proposal",
    spec: {
      name: "Sports Coach",
      goal: "Track and improve athletic performance using real activity data",
      persona: "Motivating and data-driven, speaks plainly and celebrates wins. Delivers specific, metrics-backed feedback.",
      tasks: [
        { title: "Post-run breakdown", description: "Analyze pace, heart rate, and effort after each activity" },
        { title: "Weekly training review", description: "Summarize mileage, trends, and recovery needs" },
        { title: "PR tracking", description: "Celebrate personal records and milestone achievements" },
        { title: "Workout suggestions", description: "Recommend next sessions based on your fitness level" },
      ],
      tool_requirements: [
        { app: "strava", reason: "Core activity data source", needed_scopes: ["activity:read_all"], tool_subset: ["get_activities", "get_activity_detail"] },
      ],
      success_criteria: [
        "Personalized coaching summary after every Strava sync",
        "Weekly mileage alerts with recovery recommendations",
      ],
      avatar_seed: "sports-coach-🏃",
    },
    suggested_apps: ["strava", "apple_health"],
  })}\n\n`;

  await delay(50);
  yield `data: ${JSON.stringify({ type: "done" })}\n\n`;
}

async function* mockChatStreamGenerator(id: string, message: string) {
  const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

  // Action event first
  await delay(400);
  yield `data: ${JSON.stringify({
    type: "action",
    label: "Fetched last run",
    detail: "12.4km · 53:20 · avg 4:18/km",
  })}\n\n`;

  await delay(200);

  const reply = `Based on your recent Strava data, here's what I see:

**Last run (yesterday):** 12.4km in 53:20 — solid 4:18/km average pace. That's within your comfortable aerobic zone.

**This week:** You're at 28km total, which is tracking about 15% above last week. Keep an eye on that — the 10% rule suggests easing up slightly to avoid overtraining.

**Recommendation:** Schedule an easy 5-6km recovery run tomorrow at 5:30-5:45/km. Your legs need the flush, not the grind.

What aspect would you like to dig into — pace trends, heart rate zones, or upcoming race prep?`;

  const words = reply.split(/(\s+)/);
  for (const chunk of words) {
    await delay(18);
    yield `data: ${JSON.stringify({ type: "delta", text: chunk })}\n\n`;
  }

  await delay(100);
  yield `data: ${JSON.stringify({ type: "action", label: "Response complete", detail: null })}\n\n`;
  yield `data: ${JSON.stringify({ type: "done" })}\n\n`;
}

function generatorToResponse(
  gen: AsyncGenerator<string>
): Response {
  const stream = new ReadableStream({
    async start(controller) {
      for await (const chunk of gen) {
        controller.enqueue(new TextEncoder().encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream" },
  });
}

// ---------------------------------------------------------------------------
// Mock API surface (matches realApi shape)
// ---------------------------------------------------------------------------

export const mockApi = {
  async listProjects() {
    await new Promise((r) => setTimeout(r, 200));
    return { projects: MOCK_PROJECTS };
  },

  async getProject(id: string) {
    await new Promise((r) => setTimeout(r, 100));
    const project = MOCK_PROJECTS.find((p) => p.id === id) ?? MOCK_PROJECTS[0];
    return { project };
  },

  async createProject(spec: ProjectSpec, connectionIds: string[] = []) {
    await new Promise((r) => setTimeout(r, 500));
    const id = `mock-new-${Date.now()}`;
    STAGE_STARTS.set(id, Date.now());
    const project: DbProject = {
      id,
      user_id: "demo-user",
      name: spec.name,
      goal: spec.goal,
      status: "compiling",
      failed_stage: null,
      spec: spec as unknown as DbProject["spec"],
      runtime_key: "slot-a",
      session_key: `agent:${id}:user:demo-user`,
      gateway_url: "http://localhost:8080",
      avatar_seed: spec.avatar_seed,
      created_at: new Date().toISOString(),
    };
    MOCK_PROJECTS.unshift(project);
    const handle: ProfileHandle = {
      project_id: id,
      gateway_url: "http://localhost:8080",
      gateway_key: "mock-key",
      session_key: project.session_key!,
      runtime_key: "slot-a",
      status: "compiling",
    };
    return { project, handle };
  },

  async getStatus(id: string) {
    await new Promise((r) => setTimeout(r, 100));
    const status = getMockStatus(id);
    // Update MOCK_PROJECTS in-place
    const p = MOCK_PROJECTS.find((x) => x.id === id);
    if (p) p.status = status as DbProject["status"];
    return { status, failed_stage: null };
  },

  async getMessages(id: string): Promise<{ messages: DbMessage[] }> {
    await new Promise((r) => setTimeout(r, 100));
    return { messages: [] };
  },

  async getMemory(id: string): Promise<{ memory: DbMemory[] }> {
    await new Promise((r) => setTimeout(r, 100));
    return { memory: MOCK_MEMORY.filter((m) => m.project_id === id || m.project_id === "mock-sports-coach") };
  },

  async getCatalog(): Promise<CatalogApp[]> {
    await new Promise((r) => setTimeout(r, 100));
    return MOCK_CATALOG;
  },

  async listConnections(): Promise<Connection[]> {
    await new Promise((r) => setTimeout(r, 100));
    return MOCK_CONNECTIONS;
  },

  async connect(app: string) {
    await new Promise((r) => setTimeout(r, 700));
    const existing = MOCK_CONNECTIONS.find((c) => c.app === app);
    if (existing) {
      existing.status = "connected";
      return { connection: existing, redirect_url: null };
    }
    const conn: Connection = {
      id: `mock-conn-${app}-${Date.now()}`,
      user_id: "demo-user",
      app,
      status: "connected",
      mcp_url: `http://localhost:9000/mcp/${app}`,
      available_tools: ["read", "list"],
    };
    MOCK_CONNECTIONS.push(conn);
    return { connection: conn, redirect_url: null };
  },

  shapeStream(
    message: string,
    history: { role: string; content: string }[]
  ): Promise<Response> {
    return Promise.resolve(
      generatorToResponse(mockShapeStreamGenerator(message, history))
    );
  },

  chatStream(id: string, message: string): Promise<Response> {
    return Promise.resolve(
      generatorToResponse(mockChatStreamGenerator(id, message))
    );
  },
};
