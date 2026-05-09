# Meet Advisor Dashboard

Dashboard Streamlit + estensione Chrome per monitorare in tempo reale lo stato
dei 10 advisor di Leone Master School durante le consulenze su Google Meet.

- **Verde lampeggiante** = advisor live in consulenza
- **Grigio** = advisor idle
- **Timer hh:mm:ss** che scorre dall'inizio della consulenza
- **Badge AUTO / MANUAL** indica se la sessione è partita via estensione Chrome o cliccando il bottone
- **Statistiche giornaliere** (numero consulenze, durata media, tempo totale)
- **Storico sessioni** persistente su Supabase

## Architettura

```
Chrome estensione  ──POST──▶  Supabase Edge Function  ──▶  Postgres
(installata sul                 (meet-event)                 │
 browser advisor                                              ▼
 sincronizzato                                          Streamlit dashboard
 advisorleonegroup)                                     (refresh ogni 1s)
```

L'estensione rileva quando l'advisor entra/esce davvero da una call
(non basta avere la tab aperta — controlla che sia presente il bottone
"Abbandona chiamata" nel DOM, indicatore affidabile dell'essere in call).

I bottoni manuali Start/Stop nella dashboard restano come **fallback** —
funzionano sempre, anche se l'estensione non è installata o si rompe.

## Setup completo (~30 minuti la prima volta)

### Step 1 — Crea il progetto Supabase

1. Vai su https://supabase.com → **New project** (free tier)
2. Nome: `meet-advisor-dashboard`, regione: Frankfurt
3. Salva la **Database password** (non serve qui ma utile per il futuro)

### Step 2 — Esegui lo schema

1. Project → **SQL Editor** → **+ New query**
2. Copia incolla l'intero contenuto di `schema.sql`
3. Clicca **Run** in basso a destra
4. Verifica: **Table editor** → vedi `advisors` con 10 righe

### Step 3 — Recupera le credenziali

1. **Project Settings** (icona ingranaggio) → **API**
2. Copia:
   - **Project URL** → ti servirà come `SUPABASE_URL`
   - **Project API keys → anon / public** → `SUPABASE_KEY`
   - **Project API keys → service_role** → ti servirà SOLO per la Edge Function (NON va nei secrets della dashboard)

### Step 4 — Configura i secrets della dashboard

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Apri .streamlit/secrets.toml e incolla SUPABASE_URL, SUPABASE_KEY, APP_PASSWORD
```

### Step 5 — Installa e lancia la dashboard

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

L'app si apre su http://localhost:8501. Login con la password (`faraone.92`).

A questo punto la dashboard funziona già con il flusso **manuale**
(bottoni Start/Stop). Se vuoi solo questo, fermati qui.

---

## Step 6 — (Opzionale) Setup automatico via estensione Chrome

Solo se vuoi che lo stato si aggiorni da solo quando l'advisor entra/esce
da Meet. Richiede:
- **Supabase CLI** installata localmente
- **Account Chrome Web Store** (5$ una tantum) per il deploy finale

### 6a — Genera lo shared secret

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copia l'output. Lo userai in due posti: Edge Function e estensione.

### 6b — Configura l'env della Edge Function su Supabase

1. Project → **Project Settings** → **Edge Functions** → **Manage secrets**
2. Aggiungi secret: nome `MEET_EVENT_SECRET`, valore = output dello step 6a
3. (`SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` sono autopopolati, non li imposti tu)

### 6c — Installa Supabase CLI

```bash
brew install supabase/tap/supabase
```

### 6d — Linka il progetto e deploya la function

```bash
cd /Users/salvotrifiro/leone-agents/meet-advisor-dashboard
supabase login                              # apre browser per OAuth
supabase link --project-ref <PROJECT_REF>   # ref visibile in URL del progetto Supabase
supabase functions deploy meet-event --no-verify-jwt
```

L'output mostra l'URL pubblico, tipo
`https://abcdefgh.supabase.co/functions/v1/meet-event`. Copialo.

Test rapido (sostituisci URL e secret):

```bash
curl -X POST https://abcdefgh.supabase.co/functions/v1/meet-event \
  -H "Content-Type: application/json" \
  -H "x-meet-secret: IL_TUO_SECRET" \
  -d '{"meet_link": "https://meet.google.com/yrd-rzhe-dkr", "action": "joined"}'
```

Risposta attesa: `{"status": "started", "advisor": "Marvin Alessandrin", ...}`.

### 6e — Configura l'estensione

1. Apri `extension/config.js`
2. Sostituisci `SUPABASE_FUNCTION_URL` con l'URL ottenuto al 6d
3. Sostituisci `SHARED_SECRET` con il valore generato al 6a (lo stesso che è su Supabase)

### 6f — Test in modalità sviluppatore

1. Chrome → `chrome://extensions/` → attiva "Modalità sviluppatore"
2. "Carica estensione non pacchettizzata" → seleziona la cartella `extension/`
3. Apri uno dei link Meet del seed (es. quello di Marvin) ed entra nella call
4. Sulla dashboard Streamlit l'advisor diventa LIVE con badge **AUTO**
5. Esci dalla call → torna IDLE

Se non funziona:
- Apri `chrome://extensions/` → click "Service worker" sotto l'estensione → vedi log
- Verifica che `config.js` abbia URL e secret corretti
- Controlla `Project → Edge Functions → meet-event → Logs` su Supabase

### 6g — Pubblicazione su Chrome Web Store

Vedi `extension/README.md` per la guida completa.

---

## Deploy della dashboard su Streamlit Cloud

1. Push del repo su GitHub
2. https://share.streamlit.io → **New app** → seleziona il repo
3. **Main file path:** `app.py`
4. **Advanced settings → Secrets:** incolla
   ```toml
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_KEY = "eyJxxx..."
   APP_PASSWORD = "faraone.92"
   ```
5. Deploy. URL pubblico tipo `https://meet-advisor-dashboard.streamlit.app`

## Struttura del repo

```
meet-advisor-dashboard/
├── app.py                  # UI Streamlit (login + tabella + admin panel)
├── db/
│   ├── client.py           # Connessione Supabase
│   ├── queries.py          # CRUD: advisors, sessioni, stats
│   └── format.py           # Formatter di timer e durate (testato)
├── schema.sql              # Schema Postgres + seed dei 10 advisor
├── supabase/
│   ├── config.toml         # Config Supabase CLI
│   └── functions/
│       └── meet-event/
│           ├── index.ts    # Edge Function (Deno) — webhook estensione
│           └── deno.json
├── extension/
│   ├── manifest.json       # Manifest V3
│   ├── background.js       # Service worker
│   ├── content.js          # DOM observer su Meet
│   ├── config.js           # URL webhook + shared secret (da personalizzare)
│   ├── popup.html, popup.js
│   ├── icons/              # PNG 16/48/128
│   └── README.md           # Guida pubblicazione Chrome Web Store
├── tests/test_format.py
└── requirements.txt
```

## Modificare advisor (post-deploy)

Esegui SQL via Supabase **SQL Editor**:

```sql
-- Aggiungere
INSERT INTO advisors (name, meet_link, display_order) VALUES
  ('Nuovo Advisor', 'https://meet.google.com/xxx-xxxx-xxx', 11);

-- Aggiornare un link
UPDATE advisors SET meet_link = 'https://meet.google.com/new-link'
WHERE name = 'Asma Bouchrit';

-- Cambiare ordine
UPDATE advisors SET display_order = 5 WHERE name = 'Cristian Testa';
```

L'estensione rileva automaticamente i cambi (controlla il DB ad ogni evento).

## Test

```bash
.venv/bin/python -m pytest -v
```
