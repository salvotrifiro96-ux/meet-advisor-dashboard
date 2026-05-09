# Chrome Web Store — Scheda Pubblicazione

Bozza dei testi da incollare nel Developer Dashboard al momento della pubblicazione.

## Nome
Leone Live Advisor

## Descrizione breve (max 132 caratteri)
Tracking automatico delle consulenze Google Meet per advisor di Leone Master School.

## Descrizione lunga
Leone Live Advisor è uno strumento interno per il team commerciale di Leone Master School.

L'estensione rileva automaticamente quando un advisor è dentro una consulenza Google Meet e aggiorna lo stato sulla dashboard interna del team. Non richiede alcuna azione da parte dell'advisor: si attiva solo sulle pagine meet.google.com e marca lo stato come "live" o "idle" in base alla presenza in call.

**Funzionalità:**
- Rilevamento automatico ingresso/uscita da Google Meet
- Nessuna configurazione richiesta per l'utente finale
- Comunicazione cifrata (HTTPS) con backend interno
- Niente raccolta di dati audio/video, contenuti chat, o cronologia

**Privacy:**
L'estensione invia esclusivamente l'URL della call Meet aperta e i timestamp di ingresso/uscita al backend interno di Leone Master School. Nessun dato personale, contenuto della call, o navigazione esterna viene raccolta.

## Categoria
Produttività

## Lingua
Italiano

## Privacy Policy URL
https://leonemasterschool.it/privacy-extension (da pubblicare)

## Single purpose justification
Marcare automaticamente lo stato live/idle degli advisor sulla dashboard interna durante consulenze su Google Meet.

## Permission justifications

- **storage**: salvare configurazione locale (tab tracking)
- **tabs**: rilevare la chiusura di una tab Meet per emettere l'evento "left" anche se l'utente chiude bruscamente
- **host_permissions meet.google.com**: l'estensione opera esclusivamente sulle pagine Meet
- **host_permissions *.supabase.co**: invio degli eventi al backend interno (Edge Function)

## Visibility
Non in elenco / Privato (link condiviso solo con il team)
