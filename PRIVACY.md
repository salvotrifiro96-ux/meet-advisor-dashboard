# Privacy Policy — Leone Live Advisor

**Ultimo aggiornamento: 9 maggio 2026**

Questa Privacy Policy descrive come l'estensione Chrome **Leone Live Advisor**
(di seguito "l'Estensione") gestisce le informazioni quando viene utilizzata da
membri del team commerciale di **Leone Master School S.r.l.** (di seguito "noi",
"nostro", "Leone Master School").

L'Estensione è uno strumento interno aziendale, non destinato al pubblico
generale.

## 1. Quali dati vengono raccolti

L'Estensione si attiva **esclusivamente** sulle pagine del dominio
`https://meet.google.com/`. Su queste pagine raccoglie e trasmette al backend
interno di Leone Master School i seguenti dati tecnici:

- **URL della call Meet aperta** (es. `https://meet.google.com/abc-defg-hij`)
- **Timestamp di ingresso e uscita** dalla call (rilevati osservando la presenza
  del bottone "Abbandona chiamata" nel DOM della pagina Meet)

L'Estensione **non** raccoglie e **non** trasmette:

- Audio, video, o contenuti chat delle call Meet
- Dati personali identificativi (nome, email, foto profilo)
- Cronologia di navigazione su altri siti
- Cookies o credenziali di terze parti
- Dati relativi a tab, schede o pagine non-Meet

## 2. Dove vengono inviati i dati

I dati vengono trasmessi tramite richiesta HTTPS a una **Edge Function ospitata
su Supabase** (infrastruttura interna di Leone Master School), e archiviati in
un database **PostgreSQL** anch'esso su Supabase, situato in **Unione Europea
(Francoforte, Germania)**.

L'accesso ai dati è limitato a:
- Il management commerciale di Leone Master School
- Il personale tecnico autorizzato per manutenzione

I dati non vengono condivisi con terze parti, né venduti, né utilizzati per
scopi pubblicitari.

## 3. Finalità del trattamento

Tracciare in tempo reale l'attività di consulenza degli advisor commerciali
(stato live/idle e durata delle consulenze) per fini operativi e di
coordinamento interno.

## 4. Periodo di conservazione

Lo storico delle sessioni viene conservato per scopi di reportistica interna.
Gli interessati possono richiedere la cancellazione dei propri dati scrivendo a
[tool@leonemasterschool.it](mailto:tool@leonemasterschool.it).

## 5. Permessi richiesti dall'Estensione

| Permesso | Finalità |
|---|---|
| `host_permissions` su `meet.google.com` | Osservare il DOM della pagina Meet per rilevare presenza in call |
| `host_permissions` su `*.supabase.co` | Inviare gli eventi di join/leave al backend interno |
| `tabs` | Rilevare la chiusura di una tab Meet per emettere correttamente l'evento "leave" |
| `storage` | Memorizzare configurazione locale dell'estensione (tracking tab attive) |

L'Estensione **non richiede** permessi di lettura su pagine diverse da
`meet.google.com`.

## 6. Diritti dell'utente (GDPR)

Gli utenti dell'Estensione (membri del team commerciale Leone Master School)
hanno diritto a:

- Accesso ai propri dati
- Rettifica e cancellazione
- Portabilità
- Opposizione al trattamento

Per esercitare questi diritti, scrivere a
[tool@leonemasterschool.it](mailto:tool@leonemasterschool.it).

## 7. Modifiche a questa policy

Eventuali modifiche verranno notificate via email agli utenti dell'Estensione
e pubblicate in questa stessa pagina.

## 8. Titolare del trattamento

**Leone Master School S.r.l.**
Email: tool@leonemasterschool.it
