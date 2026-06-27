// Auto-generated from ARCHITECTURE.md §5 (DB schema) + ARCHITECTURE_UML.md §3 (class diagram)
// Match: backend Supabase schema + Pydantic contracts in backend/app/contracts/models.py

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type ProvisioningState =
  | "draft"
  | "compiling"
  | "connecting"
  | "provisioning"
  | "ingesting"
  | "ready"
  | "failed";

export type ConnectionStatus = "pending" | "connected" | "error";
export type MessageRole = "system" | "user" | "assistant";
export type MemoryKind = "fact" | "weakness" | "preference" | "scraped";

// ---------------------------------------------------------------------------
// DB Tables (Supabase) — backend/app/db/migrations/schema.sql
// ---------------------------------------------------------------------------

export type DbUser = {
  id: string;
  name: string | null;
  email: string | null;
  created_at: string;
};

export type DbProject = {
  id: string;
  user_id: string | null;
  name: string;
  goal: string | null;
  status: ProvisioningState;
  failed_stage: string | null;
  spec: Record<string, unknown> | null; // jsonb — ProjectSpec when parsed
  runtime_key: string | null;
  session_key: string | null;
  gateway_url: string | null;
  avatar_seed: string | null;
  created_at: string;
};

export type DbConnection = {
  id: string;
  user_id: string | null;
  app: string;
  composio_account_id: string | null;
  mcp_url: string | null;
  status: ConnectionStatus;
  scopes: string[];
  created_at: string;
};

export type DbProjectTool = {
  id: string;
  project_id: string | null;
  connection_id: string | null;
  allowed_tools: string[];
};

export type DbMessage = {
  id: string;
  project_id: string | null;
  role: string;
  content: string;
  created_at: string;
};

export type DbMemory = {
  id: string;
  project_id: string | null;
  kind: string | null;
  content: string | null;
  created_at: string;
};

// ---------------------------------------------------------------------------
// Contract Models (Pydantic <-> TypeScript)
// ---------------------------------------------------------------------------

export type TaskItem = {
  title: string;
  description: string;
};

export type ToolRequirement = {
  app: string;
  reason: string;
  needed_scopes: string[];
  tool_subset: string[];
};

export type ProjectSpec = {
  name: string;
  goal: string;
  persona: string;
  tasks: TaskItem[];
  tool_requirements: ToolRequirement[];
  success_criteria: string[];
  avatar_seed: string;
};

export type ArtifactBundle = {
  soul_md: string;
  user_md: string;
  memory_md: string;
  config_yaml: string;
  runtime_key: string;
  session_key: string;
  tool_requirements: ToolRequirement[];
};

export type Connection = {
  id: string;
  user_id: string;
  app: string;
  status: ConnectionStatus;
  mcp_url: string | null;
  available_tools: string[];
};

export type ProfileHandle = {
  project_id: string;
  gateway_url: string;
  gateway_key: string;
  session_key: string;
  runtime_key: string;
  status: ProvisioningState;
};

export type Project = {
  id: string;
  user_id: string;
  name: string;
  goal: string | null;
  status: ProvisioningState;
  failed_stage: string | null;
  spec: ProjectSpec | null;
  avatar_seed: string | null;
};

// ---------------------------------------------------------------------------
// SSE Events — runtime (chat) stream
// ---------------------------------------------------------------------------

export type Msg = {
  role: MessageRole;
  content: string;
};

export type RuntimeEvent =
  | { type: "delta"; text: string }
  | { type: "action"; label: string; detail?: string }
  | { type: "done" }
  | { type: "error"; message: string };

// ---------------------------------------------------------------------------
// SSE Events — shaping (spec-creation) stream
// ---------------------------------------------------------------------------

export type QuestionPayload = {
  field: string;
  prompt: string;
  options: string[];
};

export type ShapingEvent =
  | { type: "delta"; text: string }
  | { type: "question"; question: QuestionPayload }
  | { type: "spec_update"; spec_update: Record<string, unknown> }
  | { type: "proposal"; spec: ProjectSpec; suggested_apps: string[] }
  | { type: "done" };
