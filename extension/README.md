# Leone Live Advisor — Chrome Extension

Estensione Chrome che rileva automaticamente quando un advisor entra in
una consulenza Google Meet e aggiorna lo stato sulla dashboard.

## Come funziona

1. Si attiva su tutte le pagine `meet.google.com/*`
2. Osserva il DOM: appena compare il bottone "Abbandona chiamata"
   (significato: l'utente è davvero entrato nella call, non solo nella lobby)
   → manda `joined` al webhook Supabase
3. Quando il bottone scompare o la tab viene chiusa → manda `left`

## Setup pre-pubblicazione (sviluppatore)

1. Aprire `extension/config.js`
2. Sostituire i due placeholder:
   - `SUPABASE_FUNCTION_URL` → URL della Edge Function deployata
     (es. `https://abcdef.supabase.co/functions/v1/meet-event`)
   - `SHARED_SECRET` → stringa random di almeno 32 caratteri
     (questo stesso valore va settato come env `MEET_EVENT_SECRET` nel
     progetto Supabase, vedi README principale)

## Test in modalità sviluppatore (prima della pubblicazione)

1. Apri Chrome → barra indirizzi `chrome://extensions/`
2. Attiva "Modalità sviluppatore" (toggle in alto a destra)
3. Clicca "Carica estensione non pacchettizzata"
4. Seleziona la cartella `extension/` di questo progetto
5. L'estensione appare con icona 🎯
6. Apri uno dei link Meet seedati e entra nella call
7. Verifica nella dashboard che l'advisor diventa LIVE
8. Per debugging: `chrome://extensions/` → click "Service worker" sotto
   il box dell'estensione → si apre la DevTools del background, vedi i log

## Pubblicazione su Chrome Web Store

Prerequisiti:
- Account Google `tool@leonemasterschool.it` con $5 USD di credito
- File icon128.png (≥128×128, già generato in `icons/`)
- Screenshot dell'estensione in azione (1280×800, da fare prima del submit)
- Privacy policy URL (basta una pagina semplice — vedi sotto)

Step:
1. https://chrome.google.com/webstore/devconsole/ → registrati pagando
   la tassa di 5$ una tantum (richiede una carta)
2. "Nuovo elemento" → trascina lo zip della cartella `extension/`
   (genera con `cd extension && zip -r ../leone-live-advisor.zip . -x "*.DS_Store"`)
3. Compila la scheda:
   - Nome: **Leone Live Advisor**
   - Descrizione: vedi `extension/store-listing.md`
   - Categoria: Produttività
   - Lingua: Italiano
   - Visibilità: **Privato** (solo per gli account a cui dai accesso) o
     **Non in elenco** (chiunque con il link può installarla)
4. Privacy policy: pubblica una pagina pubblica con
   "Questa estensione invia il link Meet aperto e timestamp di
   join/leave a un backend interno di Leone Master School. Non raccoglie
   dati personali, contenuti audio/video, o cronologia di navigazione."
5. Submit → review Google (1-3 giorni di solito)
6. Una volta approvata, ricevi link store da girare al team

## Struttura

```
extension/
├── manifest.json         # Manifest V3
├── background.js         # Service worker — gestisce webhook calls
├── content.js            # DOM observer su meet.google.com
├── config.js             # URL webhook e shared secret (da personalizzare)
├── popup.html, popup.js  # UI minimale del popup estensione
├── icons/
│   ├── generate.py       # script per rigenerare le icone
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md             # questo file
```

## Debugging tips

- **L'estensione non rileva la call:** apri DevTools sulla pagina Meet,
  controlla la console del **content script** (è in un "world" isolato,
  ma `console.log` da content.js appare nella stessa console della pagina)
- **Webhook fallisce:** apri `chrome://extensions/` → service worker dell'estensione →
  guarda i log con `console.error("[Leone Live]")`
- **403 Unauthorized dal webhook:** secret mismatch tra `config.js` e
  `MEET_EVENT_SECRET` su Supabase
- **404 Advisor not found:** il link Meet aperto non è in `advisors.meet_link` →
  verifica/aggiorna seed
