// background.js — Manifest V3 service worker
// Receives MEET_EVENT messages from content scripts and forwards them
// to the Supabase Edge Function. Tracks Meet tabs to ensure "left" is
// reported even if the tab is closed abruptly.

importScripts("config.js");

const CONFIG = self.LEONE_CONFIG;

// Map<tabId, { meet_link: string, in_call: boolean }>
const tabState = new Map();

async function postEvent(meetLink, action) {
  if (!CONFIG?.SUPABASE_FUNCTION_URL || !CONFIG?.SHARED_SECRET) {
    console.error("[Leone Live] Missing config — set SUPABASE_FUNCTION_URL and SHARED_SECRET in config.js");
    return { ok: false, error: "missing_config" };
  }

  try {
    const response = await fetch(CONFIG.SUPABASE_FUNCTION_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-meet-secret": CONFIG.SHARED_SECRET,
      },
      body: JSON.stringify({
        meet_link: meetLink,
        action,
        source: "extension",
      }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      console.warn("[Leone Live] webhook non-2xx", response.status, data);
      return { ok: false, status: response.status, data };
    }

    console.log("[Leone Live]", action, meetLink, "→", data?.status ?? data);
    updateBadge(action === "joined");
    return { ok: true, data };
  } catch (err) {
    console.error("[Leone Live] webhook error", err);
    return { ok: false, error: String(err) };
  }
}

function updateBadge(isLive) {
  try {
    chrome.action.setBadgeText({ text: isLive ? "LIVE" : "" });
    chrome.action.setBadgeBackgroundColor({ color: "#16a34a" });
  } catch (_) {
    /* not critical */
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "MEET_EVENT") return false;

  const tabId = sender?.tab?.id;
  const meetLink = message.meet_link;
  const action = message.action;

  if (!meetLink || !["joined", "left"].includes(action)) {
    sendResponse({ ok: false, error: "invalid_message" });
    return false;
  }

  if (tabId !== undefined) {
    if (action === "joined") {
      tabState.set(tabId, { meet_link: meetLink, in_call: true });
    } else {
      tabState.delete(tabId);
    }
  }

  postEvent(meetLink, action).then(sendResponse);
  return true; // keep channel open for async sendResponse
});

// If the tab is closed while still in call, content script's beforeunload
// might not have fired in time. We send "left" from here as redundancy.
chrome.tabs.onRemoved.addListener((tabId) => {
  const state = tabState.get(tabId);
  if (state?.in_call) {
    postEvent(state.meet_link, "left");
    tabState.delete(tabId);
  }
});

// Heartbeat — every minute, check for any tracked tabs that no longer exist
// (covers crash/forced close scenarios).
const HEARTBEAT_MS = CONFIG?.HEARTBEAT_INTERVAL_MS ?? 60_000;
setInterval(async () => {
  if (tabState.size === 0) return;

  const allTabs = await chrome.tabs.query({});
  const liveIds = new Set(allTabs.map((t) => t.id));

  for (const [tabId, state] of tabState.entries()) {
    if (!liveIds.has(tabId)) {
      console.log("[Leone Live] tab vanished, sending left", state.meet_link);
      postEvent(state.meet_link, "left");
      tabState.delete(tabId);
    }
  }
}, HEARTBEAT_MS);

console.log("[Leone Live] background ready");
