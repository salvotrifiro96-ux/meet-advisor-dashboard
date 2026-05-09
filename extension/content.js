// content.js — runs on every meet.google.com page
// Detects when the user is *actually inside* a Meet call (not just on the lobby)
// by watching for the "Leave call" button to appear/disappear in the DOM.
// Sends MEET_EVENT messages to the background service worker.

(() => {
  "use strict";

  const MUTATION_DEBOUNCE_MS = 250;
  const POLL_INTERVAL_MS = 5000;

  const MEET_CODE_REGEX = /\/([a-z]{3}-[a-z]{4}-[a-z]{3})(?:\/?|\?|$)/i;

  // The "Leave call" button is the most reliable in-call signal across
  // Meet UI versions. We match aria-label across IT/EN locales and also
  // tooltip-based fallbacks.
  const LEAVE_BUTTON_SELECTORS = [
    'button[aria-label*="leave" i]',
    'button[aria-label*="abbandona" i]',
    'button[aria-label*="lascia la chiamata" i]',
    'button[aria-label*="esci dalla chiamata" i]',
    'button[aria-label*="termina chiamata" i]',
    'button[aria-label*="end call" i]',
    'button[data-tooltip-id*="leave" i]',
    'div[role="button"][aria-label*="leave" i]',
    'div[role="button"][aria-label*="abbandona" i]',
  ];

  let isInCall = false;
  let observer = null;
  let pollTimer = null;
  let debounceTimer = null;

  function getMeetCodeFromUrl() {
    const match = window.location.pathname.match(MEET_CODE_REGEX);
    return match ? match[1].toLowerCase() : null;
  }

  function getMeetLink() {
    const code = getMeetCodeFromUrl();
    return code ? `https://meet.google.com/${code}` : null;
  }

  function isLeaveButtonPresent() {
    for (const selector of LEAVE_BUTTON_SELECTORS) {
      try {
        if (document.querySelector(selector)) return true;
      } catch (_) {
        /* invalid selector on legacy browser, skip */
      }
    }
    return false;
  }

  function sendEvent(action) {
    const meetLink = getMeetLink();
    if (!meetLink) return;
    try {
      chrome.runtime.sendMessage(
        { type: "MEET_EVENT", action, meet_link: meetLink },
        () => {
          // ignore response; service worker logs errors
          if (chrome.runtime.lastError) {
            // background may be dormant; not fatal — heartbeat will retry
          }
        },
      );
    } catch (_) {
      /* extension context invalidated (e.g. updated) */
    }
  }

  function evaluateState() {
    const meetCode = getMeetCodeFromUrl();
    if (!meetCode) {
      // navigated away from a Meet code (e.g. /landing). Force "left" if needed.
      if (isInCall) {
        isInCall = false;
        sendEvent("left");
      }
      return;
    }

    const inCallNow = isLeaveButtonPresent();

    if (inCallNow && !isInCall) {
      isInCall = true;
      sendEvent("joined");
    } else if (!inCallNow && isInCall) {
      isInCall = false;
      sendEvent("left");
    }
  }

  function debouncedEvaluate() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(evaluateState, MUTATION_DEBOUNCE_MS);
  }

  function start() {
    if (observer) return;

    observer = new MutationObserver(debouncedEvaluate);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["aria-label", "data-tooltip", "data-tooltip-id"],
    });

    pollTimer = setInterval(evaluateState, POLL_INTERVAL_MS);
    evaluateState();
  }

  function stop() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    if (isInCall) {
      isInCall = false;
      sendEvent("left");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }

  // Final flush on tab close / navigation. May not always fire, hence
  // the background also tracks tab removal as a redundancy.
  window.addEventListener("beforeunload", () => {
    if (isInCall) {
      // Use sendBeacon-style fallback by triggering a synchronous message;
      // chrome.runtime.sendMessage is best-effort here.
      sendEvent("left");
    }
    stop();
  });

  // SPA navigation: Meet sometimes updates URL without full reload.
  // Re-evaluate on history changes.
  const pushState = history.pushState;
  history.pushState = function (...args) {
    pushState.apply(this, args);
    debouncedEvaluate();
  };
  window.addEventListener("popstate", debouncedEvaluate);
})();
