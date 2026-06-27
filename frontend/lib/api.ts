import type {
  DbProject,
  DbMessage,
  DbMemory,
  Connection,
  ProjectSpec,
  ProfileHandle,
  ShapingEvent,
  RuntimeEvent,
} from "./types.gen";

export interface CatalogApp {
  app: string;
  display_name: string;
  description: string;
  icon: string;
  default_scopes: string[];
}

const BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000")
    : "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const realApi = {
  async listProjects(): Promise<{ projects: DbProject[] }> {
    return req("/projects");
  },

  async getProject(id: string): Promise<{ project: DbProject }> {
    return req(`/projects/${id}`);
  },

  async createProject(
    spec: ProjectSpec,
    connectionIds: string[] = []
  ): Promise<{ project: DbProject; handle: ProfileHandle }> {
    return req("/projects", {
      method: "POST",
      body: JSON.stringify({ spec, connection_ids: connectionIds }),
    });
  },

  async getStatus(
    id: string
  ): Promise<{ status: string; failed_stage: string | null }> {
    return req(`/projects/${id}/status`);
  },

  async getMessages(id: string): Promise<{ messages: DbMessage[] }> {
    return req(`/projects/${id}/messages`);
  },

  async getMemory(id: string): Promise<{ memory: DbMemory[] }> {
    return req(`/projects/${id}/memory`);
  },

  async getCatalog(): Promise<CatalogApp[]> {
    const data = await req<{ apps: Record<string, unknown>[] }>("/catalog");
    return (data.apps ?? []).map((a) => ({
      app: (a.app ?? a.id ?? "") as string,
      display_name: (a.display_name ?? a.name ?? "") as string,
      description: (a.description ?? "") as string,
      icon: (a.icon ?? "") as string,
      default_scopes: (a.default_scopes ?? []) as string[],
    }));
  },

  async listConnections(): Promise<Connection[]> {
    const data = await req<{ connections: Connection[] }>("/connections");
    return data.connections ?? [];
  },

  async connect(
    app: string
  ): Promise<{ connection: Connection; redirect_url: string | null }> {
    return req("/connections", {
      method: "POST",
      body: JSON.stringify({ app }),
    });
  },

  shapeStream(
    message: string,
    history: { role: string; content: string }[]
  ): Promise<Response> {
    return fetch(`${BASE}/projects/shape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
  },

  chatStream(id: string, message: string): Promise<Response> {
    return fetch(`${BASE}/projects/${id}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  },
};

// Re-export types for consumers
export type { ShapingEvent, RuntimeEvent };

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

// Dynamic mock import to avoid bundling mock data in prod
let _mockApi: typeof realApi | null = null;

async function getMockApi(): Promise<typeof realApi> {
  if (!_mockApi) {
    const m = await import("./mockApi");
    _mockApi = m.mockApi;
  }
  return _mockApi;
}

// Synchronous proxy: if USE_MOCK, delegate to mockApi at call time
function createProxy(): typeof realApi {
  const handler: ProxyHandler<typeof realApi> = {
    get(_target, prop: string) {
      if (!USE_MOCK) return (realApi as Record<string, unknown>)[prop];
      return async (...args: unknown[]) => {
        const mock = await getMockApi();
        const fn = (mock as Record<string, unknown>)[prop];
        if (typeof fn === "function") return (fn as (...a: unknown[]) => unknown)(...args);
        return fn;
      };
    },
  };
  return new Proxy(realApi, handler);
}

export const api = createProxy();
