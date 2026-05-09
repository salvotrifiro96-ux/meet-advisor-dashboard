// deno-lint-ignore-file no-explicit-any
// Supabase Edge Function: meet-event
// Riceve eventi joined/left dall'estensione Chrome e aggiorna lo stato
// degli advisor in tempo reale.
//
// Deploy:
//   supabase functions deploy meet-event --no-verify-jwt
//
// Env vars richieste su Supabase (Project Settings → Edge Functions → Secrets):
//   MEET_EVENT_SECRET    - stesso secret embedded nell'estensione
//   SUPABASE_URL         - autopopolato da Supabase
//   SUPABASE_SERVICE_ROLE_KEY - autopopolato da Supabase

import { serve } from "https://deno.land/std@0.224.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.43.0";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const SHARED_SECRET = Deno.env.get("MEET_EVENT_SECRET") ?? "";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type, x-meet-secret",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

interface EventPayload {
  meet_link: string;
  action: "joined" | "left";
  source?: string;
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

function normalizeMeetLink(raw: string): string {
  // Accept full URL or just the code, normalize to https://meet.google.com/<code>
  const trimmed = raw.trim().replace(/\/$/, "");
  const codeMatch = trimmed.match(/([a-z]{3}-[a-z]{4}-[a-z]{3})/i);
  if (!codeMatch) return trimmed;
  return `https://meet.google.com/${codeMatch[1].toLowerCase()}`;
}

serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: CORS_HEADERS, status: 204 });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  if (!SHARED_SECRET) {
    return jsonResponse({ error: "Server misconfigured: missing secret" }, 500);
  }

  const providedSecret = req.headers.get("x-meet-secret") ?? "";
  if (providedSecret !== SHARED_SECRET) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  let payload: EventPayload;
  try {
    payload = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  if (!payload?.meet_link || !["joined", "left"].includes(payload?.action)) {
    return jsonResponse({ error: "Invalid payload" }, 400);
  }

  const normalizedLink = normalizeMeetLink(payload.meet_link);
  const source = payload.source ?? "extension";

  const { data: advisorRows, error: lookupErr } = await supabase
    .from("advisors")
    .select("id, name, is_live, session_started_at")
    .eq("meet_link", normalizedLink)
    .limit(1);

  if (lookupErr) {
    return jsonResponse({ error: "DB lookup failed", detail: lookupErr.message }, 500);
  }

  if (!advisorRows || advisorRows.length === 0) {
    return jsonResponse(
      { error: "Advisor not found for meet_link", meet_link: normalizedLink },
      404,
    );
  }

  const advisor = advisorRows[0] as {
    id: number;
    name: string;
    is_live: boolean;
    session_started_at: string | null;
  };
  const nowIso = new Date().toISOString();

  if (payload.action === "joined") {
    if (advisor.is_live) {
      return jsonResponse({
        status: "already_live",
        advisor: advisor.name,
        session_started_at: advisor.session_started_at,
      });
    }

    const { error: insertErr } = await supabase
      .from("consultation_sessions")
      .insert({
        advisor_id: advisor.id,
        started_at: nowIso,
        source,
      });

    if (insertErr) {
      return jsonResponse({ error: "Insert failed", detail: insertErr.message }, 500);
    }

    const { error: updateErr } = await supabase
      .from("advisors")
      .update({
        is_live: true,
        session_started_at: nowIso,
        last_event_source: source,
      })
      .eq("id", advisor.id);

    if (updateErr) {
      return jsonResponse({ error: "Update failed", detail: updateErr.message }, 500);
    }

    return jsonResponse({
      status: "started",
      advisor: advisor.name,
      session_started_at: nowIso,
    });
  }

  // action === "left"
  if (!advisor.is_live) {
    return jsonResponse({ status: "already_idle", advisor: advisor.name });
  }

  const { data: openSessions } = await supabase
    .from("consultation_sessions")
    .select("id, started_at")
    .eq("advisor_id", advisor.id)
    .is("ended_at", null)
    .order("started_at", { ascending: false })
    .limit(1);

  if (openSessions && openSessions.length > 0) {
    const session = openSessions[0] as { id: number; started_at: string };
    const startedMs = new Date(session.started_at).getTime();
    const durationSeconds = Math.max(
      0,
      Math.floor((Date.now() - startedMs) / 1000),
    );

    await supabase
      .from("consultation_sessions")
      .update({ ended_at: nowIso, duration_seconds: durationSeconds })
      .eq("id", session.id);
  }

  await supabase
    .from("advisors")
    .update({
      is_live: false,
      session_started_at: null,
      last_event_source: source,
    })
    .eq("id", advisor.id);

  return jsonResponse({ status: "stopped", advisor: advisor.name });
});
