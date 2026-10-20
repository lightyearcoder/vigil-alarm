# Il mio allarme non fa ciò che mi aspetto

Questa è una traduzione di [troubleshooting.md](troubleshooting.md), tradotta da Claude (un'IA) e non rivista da un madrelingua. Segnala gli errori aprendo una issue.

Cerca qui sotto ciò che vedi. Per ogni sintomo: le cause probabili, dove controllare e cosa fare.

**Guarda sempre prima:**

- **Panoramica** nel pannello: la scheda *Pronto all'uso?* nomina ciò che manca nelle impostazioni. *Attenzione* nomina i sensori con la batteria scarica o irraggiungibili. *Cosa sorveglia ogni modalità* mostra quali sensori partecipano a quale modalità.
- **Ultimo evento:** l'entità `sensor.vigil_alarm_last_event` e il registro degli eventi (`event.vigil_alarm_alarm_events`) dicono cosa è successo e perché qualcosa è stato rifiutato.
- **Attributi dell'allarme** (`alarm_control_panel.vigil_alarm`): `open_sensors`, `bypassed_sensors`, `faults`, `problems`, `refuse_reason`.

## L'allarme non si inserisce

| Cosa vedi | Causa | Cosa fare |
|---|---|---|
| `refuse_reason: sensor_open` | Un sensore sorvegliato è aperto (una finestra, per esempio). | Chiudilo, oppure scegli sul sensore cosa succede se è aperto all'inserimento (escludere, attendere la chiusura, rifiutare). |
| `refuse_reason: sensor_unavailable` | Un sensore è irraggiungibile (batteria scarica, fuori portata). | Vedi *Attenzione* per sapere quale. Riparalo o escludilo. |
| `refuse_reason: alarm_condition` | Un allarme di incendio, gas o antimanomissione è attivo. | Elimina la causa e disattiva prima. |
| `refuse_reason: not_disarmed` | L'allarme è già inserito o nel ritardo d'uscita. | Disattiva prima. |
| Un errore sul codice | Codice sbagliato, troppo corto, non consentito per quella modalità o bloccato (vedi sotto). | Controlla l'utente nella scheda *Utenti*. |

## L'allarme non scatta con una porta aperta o un movimento

1. **L'allarme è davvero inserito?** Durante il ritardo d'uscita (`arming`) non si sorveglia ancora nulla.
2. **Il sensore è in un gruppo di sensori?** Un sensore di intrusione senza gruppo non sorveglia nulla. Se *Cosa sorveglia ogni modalità* dice «nessun gruppo di sensori», crea i gruppi predefiniti (scheda *Pronto all'uso?*).
3. **Il gruppo è attivo in questa modalità?** *Interno* vale solo per Fuori casa, per esempio. In Casa un rilevatore di movimento non scatta mai.
4. **Il sensore è escluso?** Allora è elencato in `bypassed_sensors`. Un'esclusione termina alla disattivazione.
5. **Il tipo è «ritardato»?** Allora hai prima il ritardo d'ingresso (`pending`), e l'allarme scatta solo se non disattivi in tempo.
6. **C'è una regola di conferma?** Allora l'allarme scatta solo quando abbastanza sensori diversi scattano entro la finestra di tempo. Un singolo sensore dà solo l'avviso «senza conferma».
7. **Il sensore è irraggiungibile?** Allora non può scattare. Vedi *Attenzione*.
8. **È l'entità giusta?** In *Strumenti per sviluppatori → Stati* controlla che l'entità passi davvero a `on` quando la porta si apre.

## Nessuna notifica sul telefono

1. C'è un **canale di notifica**? Se no, *Pronto all'uso?* lo dice e propone il tuo telefono.
2. Sono attive le **categorie** giuste? Vengono inviati solo i messaggi di quelle categorie (allarme, ritardo d'ingresso, guasto, tecnico).
3. C'è un **ritardo**? Un canale di escalation con ritardo di 30 secondi notifica solo dopo 30 secondi, e non se prima disattivi o confermi.
4. Usa il **pulsante di test** del canale. Se il test non arriva, il problema è Home Assistant o l'app, non l'allarme: controlla il permesso di notifica dell'app sul telefono.
5. Il **servizio** è giusto? Deve essere un servizio `notify.` esistente.

## La sirena non suona

1. È configurata una sirena e suona per *questa causa* (intrusione, incendio, gas, antimanomissione, guasto)?
2. Prova l'azione `vigil_alarm.test_siren`. Se non suona, il problema è l'entità stessa (irraggiungibile, batteria scarica).
3. La sirena è stata **silenziata** con `vigil_alarm.silence`? Allora l'allarme resta attivo ma la sirena tace.
4. È trascorsa la **durata massima**? Dopo la sirena si ferma da sola.

## Il mio codice viene rifiutato

- **Troppo corto:** la lunghezza minima è in *Impostazioni* (da 4 a 12 caratteri).
- **Bloccato:** dopo alcuni codici errati Vigil blocca quel punto a gradini (per impostazione predefinita 5, poi 15, poi 60 minuti), anche per il codice giusto. Attendi un momento; il registro degli eventi mostra `code_locked`. Se mostra `code_locked_permanent`, la tastiera resta chiusa finché un amministratore preme *Revoca il blocco* in Pannelli. I valori sono in *Impostazioni*, *Blocco*.
- **Non consentito:** l'utente può usare solo certe modalità. Controlla *Modalità consentite*. Disattivare funziona sempre con un codice valido.

## Falsi allarmi

- Dai alle porte il tipo **ritardato** con un ritardo d'ingresso, così puoi disattivare in tempo.
- Lascia che un rilevatore di movimento sorvegli solo in Fuori casa (gruppo *Interno*).
- Usa una **regola di conferma**: un allarme solo se due rilevatori di movimento scattano entro un minuto.
- Per una notifica, controlla il registro degli eventi per vedere quale sensore era.

## Nessuna notifica di batteria o antimanomissione

- Il sensore ha bisogno di un **sensore di batteria**. *Pronto all'uso?* nomina i sensori che non ce l'hanno. Va bene anche un dispositivo che segnala solo «batteria scarica» (on/off).
- Se il dispositivo ha un **sensore antimanomissione**, indicalo sul sensore. La scheda nomina i sensori antimanomissione non collegati a nulla.

## Le entità hanno nomi diversi da quelli attesi

Gli identificativi delle entità di Vigil terminano sempre con il nome inglese, anche quando Home Assistant è impostato su un'altra lingua (per esempio `binary_sensor.vigil_alarm_intrusion_alarm`). Ciò che vedi nell'interfaccia segue la tua lingua. Controlla i nomi reali in *Impostazioni → Dispositivi e servizi → Vigil Alarm*. Se vieni da una versione più vecchia, aggiorna le tue automazioni e dashboard ai nuovi identificativi (vedi le note di rilascio).

## Il pannello è vuoto

Ricarica il browser forzando (Ctrl+F5) e controlla che l'integrazione sia in esecuzione in *Dispositivi e servizi*. Altrimenti guarda il registro (*Impostazioni → Sistema → Registri*, cerca `vigil`).

## Ancora non funziona?

Scarica la diagnostica (*Dispositivi e servizi → Vigil Alarm → ⋮ → Scarica la diagnostica*), che non contiene codici né nomi di persone, e segnalalo su GitHub (vedi la scheda *Info*).

## Continuo a ricevere un promemoria del test della sirena

Il promemoria si ripete finché non viene fatto un test. Tocca *Prova la sirena* nel messaggio, usa *Prova la sirena ora* nella scheda Panoramica, oppure chiama `vigil_alarm.test_siren`. Per fermare i promemoria, imposta l'intervallo in *Impostazioni* su 0.

## L'heartbeat fallisce

La scheda *Heartbeat* nella scheda Panoramica nomina il motivo: *nessuna connessione* (Home Assistant non raggiunge internet o l'indirizzo è sbagliato), *nessuna risposta entro 10 secondi*, o *HTTP 404* e simili (il servizio non conosce l'indirizzo; copialo di nuovo). Correggilo in *Impostazioni* e clicca *Prova ora*.
