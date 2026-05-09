// Template di configurazione per l'estensione.
// Copia questo file in `config.js` (gitignored) e sostituisci i placeholder
// con i valori reali. NON committare mai `config.js` su GitHub.
//
// SUPABASE_FUNCTION_URL: URL pubblico della Edge Function meet-event,
//   es. "https://<project-ref>.supabase.co/functions/v1/meet-event"
// SHARED_SECRET: stesso valore di MEET_EVENT_SECRET nelle env Supabase
//   (Project Settings → Edge Functions → Manage secrets).
//   Per generarne uno nuovo:
//     python3 -c "import secrets; print(secrets.token_urlsafe(48))"

self.LEONE_CONFIG = Object.freeze({
  SUPABASE_FUNCTION_URL: "https://YOUR-PROJECT-REF.supabase.co/functions/v1/meet-event",
  SHARED_SECRET: "REPLACE_WITH_RANDOM_64_CHAR_STRING",
  HEARTBEAT_INTERVAL_MS: 60_000,
  MUTATION_DEBOUNCE_MS: 250,
});
