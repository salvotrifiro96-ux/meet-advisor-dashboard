// Centralized config for the extension.
// Replace these placeholders with the real values BEFORE publishing
// the extension on Chrome Web Store.
//
// SUPABASE_FUNCTION_URL: l'URL pubblico della Edge Function meet-event,
//   tipo "https://<project-ref>.supabase.co/functions/v1/meet-event"
// SHARED_SECRET: stesso valore configurato nelle env Supabase come
//   MEET_EVENT_SECRET. Embedderlo qui è accettabile per il nostro modello
//   di rischio (10 dipendenti fidati). Per maggiore sicurezza,
//   ruotalo periodicamente.

self.LEONE_CONFIG = Object.freeze({
  SUPABASE_FUNCTION_URL: "https://fmzunwsrpgdexlwmkruy.supabase.co/functions/v1/meet-event",
  SHARED_SECRET: "ZhI2PWIARLvkMpyJwfuQjibv0XoojZwcnhhnKRHr445XV1DRbV58NeC3IcSvdzpB",
  HEARTBEAT_INTERVAL_MS: 60_000,
  MUTATION_DEBOUNCE_MS: 250,
});
