/**
 * Thin fetch wrapper around the existing FastAPI backend (app/routers/*.py
 * in the main repo — untouched by this rewrite, only the frontend is
 * being replaced). Auth is a JWT Bearer token, not a cookie session (see
 * app/routers/auth.py's OAuth2PasswordBearer), so plain `fetch` calls
 * from the browser work fine cross-origin even with the backend's
 * `allow_origins=["*"]` CORS config — no `credentials: "include"` needed
 * anywhere here, which is what would have made the wildcard-origin CORS
 * setup actually fail in the browser.
 *
 * Base URL: defaults to the relative path "/api/v1", assuming this app is
 * served behind the same reverse proxy/domain that already proxies
 * /api/* to the FastAPI container (the standard setup for a domain like
 * fire-engine.maqaree.com fronting multiple docker services). Override
 * with NEXT_PUBLIC_API_URL at build time if the API lives on a different
 * host/port.
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "/api/v1";

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown, message?: string) {
    super(message || (typeof detail === "string" ? detail : `API error ${status}`));
    this.status = status;
    this.detail = detail;
  }
}

type RequestOpts = {
  token?: string | null;
  json?: unknown;
  form?: Record<string, string>;
  formData?: FormData;
  params?: Record<string, string | number | boolean | undefined>;
  method?: string;
};

function buildUrl(path: string, params?: RequestOpts["params"]) {
  const url = new URL(API_BASE + path, typeof window !== "undefined" ? window.location.origin : "http://localhost");
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
  }
  // Return relative (path + search) when API_BASE is relative, so requests
  // still go through the current origin's reverse proxy.
  return API_BASE.startsWith("http") ? url.toString() : url.pathname + url.search;
}

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;

  let body: BodyInit | undefined;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = new URLSearchParams(opts.form).toString();
  } else if (opts.formData) {
    body = opts.formData; // let the browser set the multipart boundary
  }

  const res = await fetch(buildUrl(path, opts.params), {
    method: opts.method || (body ? "POST" : "GET"),
    headers,
    body,
  });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text().catch(() => null);
    }
    const message =
      detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : undefined;
    throw new ApiError(res.status, detail, message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------
export type LoginResponse = {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
};

export function login(username: string, password: string) {
  // FastAPI's OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
  return request<LoginResponse>("/auth/login", { method: "POST", form: { username, password } });
}

export function me(token: string) {
  return request<LoginResponse>("/auth/me", { token });
}

export type UserRecord = {
  id: number;
  username: string;
  email: string;
  role: "engineer" | "auditor" | "admin" | string;
};

export function listUsers(token: string) {
  return request<UserRecord[]>("/auth/users", { token });
}

export function createUser(
  token: string,
  data: { username: string; email: string; password: string; role: string }
) {
  return request<UserRecord>("/auth/users", { method: "POST", token, json: data });
}

export function updateUser(
  token: string,
  userId: number,
  data: { role?: string; new_password?: string }
) {
  return request<UserRecord>(`/auth/users/${userId}`, { method: "PATCH", token, json: data });
}

export function deleteUser(token: string, userId: number) {
  return request<{ status: string }>(`/auth/users/${userId}`, { method: "DELETE", token });
}

// ---------------------------------------------------------------------
// Saved sessions / archive
// ---------------------------------------------------------------------
export type SavedSession = {
  session_id: string;
  filename: string;
  created_at: string;
  data: BoqAnalysis;
};

export function getMySessions(token: string) {
  return request<SavedSession[]>("/auth/sessions/my-sessions", { token });
}

export function renameSession(token: string, sessionId: string, filename: string) {
  return request<{ status: string; filename: string }>(`/auth/sessions/${sessionId}`, {
    method: "PATCH",
    token,
    json: { filename },
  });
}

export function deleteSession(token: string, sessionId: string) {
  return request<{ status: string }>(`/auth/sessions/${sessionId}`, { method: "DELETE", token });
}

export function sessionPdfUrl(sessionId: string) {
  return buildUrl(`/auth/sessions/${sessionId}/pdf`);
}

/** POST /auth/sessions/save is an upsert keyed on session_id (see
 * app/routers/auth.py) — calling it again for a session_id that already
 * exists just overwrites that session's stored `data` (and `filename`,
 * and `pdf_bytes` if a `file` is given). Used both for the original
 * "Save to Archive" action (analyze/page.tsx, always passes `file`) and
 * for persisting a chat-table merge back into an already-archived
 * session's BOQ (archive/page.tsx, `file` omitted — the previously
 * uploaded PDF on the record is left untouched). */
export async function saveSessionData(
  token: string,
  sessionId: string,
  filename: string,
  data: BoqAnalysis,
  file?: File
) {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("filename", filename);
  form.append("data", JSON.stringify(data));
  if (file) form.append("file", file);
  const res = await fetch((process.env.NEXT_PUBLIC_API_URL || "/api/v1") + "/auth/sessions/save", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
}

// ---------------------------------------------------------------------
// BOQ extraction (streaming NDJSON)
// ---------------------------------------------------------------------
export type BoqComponent = {
  name: string;
  count: number;
  confidence: string;
  supplier_type?: string;
  unit_cost_sar?: number;
  total_cost_sar?: number;
  erp_item_code?: string;
  erp_item_name?: string;
  erp_moving_avg_cost?: number;
  erp_selling_price?: number;
};

export type BoqAnalysis = {
  system_type: string;
  components: BoqComponent[];
  flagged_unclear_areas: string[];
  usage_summary?: {
    provider: string;
    model: string | null;
    total_input_tokens: number;
    total_output_tokens: number;
    total_cost_usd: number;
  };
};

export type ExtractProgressEvent =
  | { status: "progress"; current_page: number; total_pages: number }
  | {
      status: "completed";
      data: { session_id: string | null; filename: string; total_pages: number; analysis: BoqAnalysis };
    };

/** Consumes the NDJSON stream from POST /extract/pdf-boq, calling
 * onEvent for every line as it arrives (one "progress" event per page,
 * then one final "completed" event) — mirrors exactly how the Streamlit
 * version consumed `res.iter_lines()`. */
export async function extractBoq(
  token: string,
  file: File,
  opts: {
    sessionId: string;
    provider: string;
    reportType: string;
    model?: string;
    onEvent: (e: ExtractProgressEvent) => void;
    signal?: AbortSignal;
  }
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", opts.sessionId);

  const params: Record<string, string> = { provider: opts.provider, report_type: opts.reportType };
  if (opts.model) params.model = opts.model;

  const res = await fetch(buildUrl("/extract/pdf-boq", params), {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
    signal: opts.signal,
  });

  if (!res.ok || !res.body) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newlineIdx: number;
    while ((newlineIdx = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, newlineIdx).trim();
      buffer = buffer.slice(newlineIdx + 1);
      if (line) opts.onEvent(JSON.parse(line) as ExtractProgressEvent);
    }
  }
  const rest = buffer.trim();
  if (rest) opts.onEvent(JSON.parse(rest) as ExtractProgressEvent);
}

// ---------------------------------------------------------------------
// Chat (per-session Q&A about a drawing)
// ---------------------------------------------------------------------
export type ChatMessage = { role: "user" | "assistant"; content: string; created_at?: string };

export function getChatHistory(token: string, sessionId: string) {
  return request<ChatMessage[]>(`/chat/${sessionId}/history`, { token });
}

export function askAboutDrawing(
  token: string,
  sessionId: string,
  question: string,
  expectTable = false
) {
  // NOTE: the backend (app/routers/chat.py) answers in one shot today —
  // it is not a token-streaming endpoint. The "thinking..." live-status
  // UX requested for this screen is implemented client-side (see the
  // chat page) as a progressive reveal once the full answer arrives;
  // true token-by-token streaming would need chat_service.ask() itself
  // changed to stream from Anthropic, which is a backend change, not
  // just a frontend one.
  //
  // expectTable asks the backend (see claude_chat_service.py's
  // TABLE_FORMAT_SUFFIX) to have the model append a machine-parsable
  // ```json block to its answer — set true for the fixed security/fire
  // BOQ prompts (see drawing-chat.tsx), left false for normal free-form
  // questions. The returned `answer` text is unchanged either way; the
  // table (if any) is extracted from it client-side via
  // lib/chat-table.ts, the same code path used to redraw it from
  // history after a reload.
  return request<{ answer: string; usage: unknown }>(`/chat/${sessionId}/ask`, {
    method: "POST",
    token,
    json: { question, expect_table: expectTable },
  });
}

// ---------------------------------------------------------------------
// Reference library (RAG) — promoting an approved analysis into the
// examples pool app/services/reference_library_service.py pulls from
// when building the "house style" reference block for future extractions.
// ---------------------------------------------------------------------
export function saveReferenceExample(
  token: string,
  data: { session_id: string; report_type: string; tag: string }
) {
  return request<{ status: string; id: number; tag: string }>("/library/save", {
    method: "POST",
    token,
    json: data,
  });
}

export type ReferenceExample = {
  id: number;
  report_type: string;
  tag: string;
  session_id: string;
  created_at: string;
  component_count: number;
};

export function listReferenceExamples(token: string, reportType?: string) {
  return request<ReferenceExample[]>("/library/examples", {
    token,
    params: reportType ? { report_type: reportType } : undefined,
  });
}

export function deleteReferenceExample(token: string, exampleId: number) {
  return request<{ status: string }>(`/library/examples/${exampleId}`, {
    method: "DELETE",
    token,
  });
}

// ---------------------------------------------------------------------
// Projects page — stage 1 of the estimation workflow: extract the
// fire-protection SCOPE from a project's PTS as a flat table (one row per
// Area + Type of system required as per PTS), matching the estimation
// engineer's reference sheet. See app/routers/projects.py.
// ---------------------------------------------------------------------
export type ScopeRow = { area: string; system: string };

export type ApiUsage = {
  provider: string;
  model: string | null;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
};

export type ProjectSpecData = {
  scope: ScopeRow[];
  // True if the model's reply hit the output-length limit. A flag, not a
  // message, so the warning is shown in the user's selected UI language.
  truncated?: boolean;
  // How many approved reference scope tables (RAG) guided this extraction.
  reference_examples_used?: number;
  api_usage?: ApiUsage;
};

export type ProjectSpecSummary = {
  id: number;
  filename: string;
  created_at: string;
  data: ProjectSpecData;
  has_pdf: boolean;
  // Set when this table was approved into the reference library (RAG).
  approved_tag: string | null;
};

/** POST /projects/extract — reads the PTS and returns the scope table.
 * Not auto-saved. */
export function extractProjectSpec(token: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ filename: string; data: ProjectSpecData }>("/projects/extract", {
    method: "POST",
    token,
    formData: form,
  });
}

/** POST /projects/save — saves a new scope table (and the PTS PDF). */
export function saveProjectSpec(token: string, filename: string, data: ProjectSpecData, file?: File) {
  const form = new FormData();
  form.append("filename", filename);
  form.append("data", JSON.stringify(data));
  if (file) form.append("file", file);
  return request<{ status: string; id: number }>("/projects/save", {
    method: "POST",
    token,
    formData: form,
  });
}

/** PATCH /projects/{id} — saves edits to an already-saved table (also
 * updates its reference-library copy if it was approved). */
export function updateProjectSpec(token: string, specId: number, scope: ScopeRow[], filename?: string) {
  return request<{ status: string; id: number }>(`/projects/${specId}`, {
    method: "PATCH",
    token,
    json: { scope, filename },
  });
}

/** POST /projects/{id}/approve — adds the saved, accepted table to the
 * reference library (RAG) that guides future extractions. */
export function approveProjectSpec(token: string, specId: number, tag: string) {
  return request<{ status: string; id: number; tag: string }>(`/projects/${specId}/approve`, {
    method: "POST",
    token,
    json: { tag },
  });
}

export function getMyProjectSpecs(token: string) {
  return request<ProjectSpecSummary[]>("/projects/my-specs", { token });
}

export function deleteProjectSpec(token: string, specId: number) {
  return request<{ status: string }>(`/projects/${specId}`, { method: "DELETE", token });
}

export function projectSpecPdfUrl(specId: number) {
  return buildUrl(`/projects/${specId}/pdf`);
}

/** POST /projects/export-xlsx — downloads the current (possibly edited)
 * table as an Excel file in the reference-sheet layout. */
export async function downloadScopeXlsx(token: string, filename: string, scope: ScopeRow[]) {
  const res = await fetch(buildUrl("/projects/export-xlsx"), {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ filename, scope }),
  });
  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename.replace(/\.pdf$/i, "")} - Scope.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
