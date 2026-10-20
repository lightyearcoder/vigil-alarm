/* Vigil card: the alarm on a dashboard, mostly for a tablet on the wall.
 *
 * Add it to a dashboard as:  type: custom:vigil-card
 *
 * It is a dumb terminal, like the ESPHome panel. It asks Vigil which panel of the register belongs to the
 * logged-in Home Assistant user, and then follows that panel's profile (the sensor Vigil makes for it): the
 * modes it may arm in, whether it may disarm or bypass, whether it may show the sensors, the language.
 * It only reads. What the tablet may really do is enforced by Vigil on the server, whatever this card shows.
 * Narrow (a phone): one column. Wide (a tablet, 640 px and up): the state on the left, the modes or the keypad on the right.
 *
 * Optional setting:  idle_timeout: 30   (seconds without touch before a half typed code is forgotten)
 *
 * The logic mirrors esphome/vigil_alarm/vigil_panel.h; keep the two in step.
 */
(() => {
  if (customElements.get("vigil-card")) return;

  const TEXTS = {
    nl: {
      disarmed: "Uitgeschakeld", armed_home: "Thuis", armed_away: "Weg", armed_night: "Nacht", armed_vacation: "Vakantie", armed_custom_bypass: "Aangepast", arming: "Inschakelen",
      pending: "Binnenkomst", triggered: "ALARM", offline: "Geen verbinding",
      home: "Thuis", away: "Weg", night: "Nacht", vacation: "Vakantie", custom: "Aangepast", disarm: "Uitschakelen",
      home_sub: "Iemand is thuis", away_sub: "Iedereen vertrekt", night_sub: "Naar bed", vacation_sub: "Langere tijd weg", custom_sub: "Eigen keuze", countdown: "Nog {n} seconden",
      arm_home: "Thuis inschakelen", arm_away: "Weg inschakelen", arm_night: "Nacht inschakelen", arm_vacation: "Vakantie inschakelen", arm_custom: "Aangepast inschakelen",
      bypass: "Omzeilen", unbypass: "Herstellen", bypass_title: "Omzeilen: ", unbypass_title: "Herstellen: ",
      unlock_title: "Sensoren bekijken", admin_code: "Installateurscode", hint_user: "Voer uw gebruikerscode in", hint_admin: "Voer de installateurscode in", sensors: "Sensoren", sensors_open: "open",
      all_closed: "Alles dicht", open: "Open: ", problems: "Storingen: ", leave_in: "Verlaat het huis: ",
      enter_in: "Schakel uit binnen: ", by: "Door ", by_unknown: "Door: onbekend", via: "Via ", practice: "Oefenmodus: geen sirene, geen meldingen", last_alarm: "Laatste alarm: ", bypassed_now: "Omzeild: ", false_alarm: " (vals alarm)", no_sensors: "Geen sensoren", back: "Terug", cancel: "Annuleren",
      blocked: "Geblokkeerd", blocked_sub: "Dit paneel is geblokkeerd in Vigil",
      refuse_alarm_condition: "Inschakelen kan niet: {s} staat open", refuse_sensor_unavailable: "Inschakelen kan niet: {s} reageert niet", refuse_sensor_open: "Inschakelen kan niet: {s} staat open", refuse_not_disarmed: "Het alarm staat al aan", force: "Omzeilen en inschakelen",
      not_linked: "Niet gekoppeld",
      not_linked_sub: "Voeg dit Home Assistant-account toe in Vigil onder Panelen. Account: ",
      err_invalid_code: "Ongeldige code", err_code_required: "Voer een code in", err_locked_pre: "Te veel foute codes. Probeer het over ", err_locked_post: " min opnieuw", err_locked: "Te veel foute codes. Even wachten", err_locked_permanent: "Te veel foute codes. Vergrendeld totdat een beheerder dit in Vigil opheft", err_bypass_tamper: "U mag sabotage niet omzeilen of terugzetten", err_bypass: "U mag sensoren niet omzeilen of terugzetten", err_blocked: "Dit paneel is geblokkeerd", err_not_allowed: "Dit paneel mag dit niet", err_no_installer_code: "Stel eerst een installateurscode in Vigil in", err_not_bypassable: "Deze sensor kan niet worden omzeild",
      old_profile: "Update Vigil of de kaart", no_admin_code: "Stel eerst een installateurscode in Vigil in",
      st_closed: "dicht", st_open: "open", st_waiting: "wacht", st_bypassed: "omzeild",
      st_bypassed_at_arm: "omzeild bij inschakelen", st_unavailable: "storing",
      cause_intrusion: "Inbraak", cause_fire: "Brand", cause_gas: "Gas", cause_tamper: "Sabotage", cause_alarm24: "24-uursalarm", cause_silent24: "Stil alarm", cause_water: "Water",
      cause_fault: "Sensorstoring", ok: "OK", delete: "Wis", code: "Code",
      all: "Alles", mixed: "Gemengd", only_this: "alleen deze partitie", default_tag: "standaard",
    },
    en: {
      disarmed: "Disarmed", armed_home: "Home", armed_away: "Away", armed_night: "Night", armed_vacation: "Vacation", armed_custom_bypass: "Custom", arming: "Arming",
      pending: "Entry", triggered: "ALARM", offline: "No connection",
      home: "Home", away: "Away", night: "Night", vacation: "Vacation", custom: "Custom", disarm: "Disarm",
      home_sub: "Someone is home", away_sub: "Everyone is leaving", night_sub: "Going to bed", vacation_sub: "Away for a longer time", custom_sub: "Your own choice", countdown: "{n} seconds left",
      arm_home: "Arm home", arm_away: "Arm away", arm_night: "Arm night", arm_vacation: "Arm vacation", arm_custom: "Arm custom",
      bypass: "Bypass", unbypass: "Restore", bypass_title: "Bypass: ", unbypass_title: "Restore: ",
      unlock_title: "View sensors", admin_code: "Installer code", hint_user: "Enter your user code", hint_admin: "Enter the installer code", sensors: "Sensors", sensors_open: "open",
      all_closed: "All closed", open: "Open: ", problems: "Problems: ", leave_in: "Leave within: ",
      enter_in: "Disarm within: ", by: "By ", by_unknown: "By: unknown", via: "Via ", practice: "Practice mode: no siren, no messages", last_alarm: "Last alarm: ", bypassed_now: "Bypassed: ", false_alarm: " (false alarm)", no_sensors: "No sensors", back: "Back", cancel: "Cancel",
      blocked: "Blocked", blocked_sub: "This panel is blocked in Vigil",
      refuse_alarm_condition: "Cannot arm: {s} is open", refuse_sensor_unavailable: "Cannot arm: {s} does not respond", refuse_sensor_open: "Cannot arm: {s} is open", refuse_not_disarmed: "The alarm is already on", force: "Bypass and arm",
      not_linked: "Not linked",
      not_linked_sub: "Add this Home Assistant account in Vigil under Panels. Account: ",
      err_invalid_code: "Invalid code", err_code_required: "A code is required", err_locked_pre: "Too many wrong codes. Try again in ", err_locked_post: " min", err_locked: "Too many wrong codes. Wait a moment", err_locked_permanent: "Too many wrong codes. Locked until an administrator unlocks it in Vigil", err_bypass_tamper: "You may not bypass or restore tamper", err_bypass: "You may not bypass or restore sensors", err_blocked: "This panel is blocked", err_not_allowed: "This panel may not do this", err_no_installer_code: "Set an installer code in Vigil first", err_not_bypassable: "This sensor cannot be bypassed",
      old_profile: "Update Vigil or the card", no_admin_code: "Set an installer code in Vigil first",
      st_closed: "closed", st_open: "open", st_waiting: "waiting", st_bypassed: "bypassed",
      st_bypassed_at_arm: "bypassed at arming", st_unavailable: "fault",
      cause_intrusion: "Intrusion", cause_fire: "Fire", cause_gas: "Gas", cause_tamper: "Tamper", cause_alarm24: "24-hour alarm", cause_silent24: "Silent alarm", cause_water: "Water",
      all: "All", mixed: "Mixed", only_this: "only this partition", default_tag: "default",
      cause_fault: "Sensor fault", ok: "OK", delete: "Delete", code: "Code",
    },
    de: {
      disarmed: "Unscharf", armed_home: "Zuhause", armed_away: "Abwesend", armed_night: "Nacht", armed_vacation: "Urlaub", armed_custom_bypass: "Benutzerdef.", arming: "Wird scharf",
      pending: "Eintritt", triggered: "ALARM", offline: "Keine Verbindung",
      home: "Zuhause", away: "Abwesend", night: "Nacht", vacation: "Urlaub", custom: "Benutzerdef.", disarm: "Unscharf schalten",
      home_sub: "Jemand ist zuhause", away_sub: "Alle gehen weg", night_sub: "Schlafen gehen", vacation_sub: "Länger weg", custom_sub: "Eigene Wahl", countdown: "Noch {n} Sekunden",
      arm_home: "Zuhause scharf schalten", arm_away: "Abwesend scharf schalten", arm_night: "Nacht scharf schalten", arm_vacation: "Urlaub scharf schalten", arm_custom: "Benutzerdef. scharf schalten",
      bypass: "Überbrücken", unbypass: "Wiederherstellen", bypass_title: "Überbrücken: ", unbypass_title: "Wiederherstellen: ",
      unlock_title: "Sensoren ansehen", admin_code: "Installateurcode", hint_user: "Benutzercode eingeben", hint_admin: "Installateurcode eingeben", sensors: "Sensoren", sensors_open: "offen",
      all_closed: "Alles geschlossen", open: "Offen: ", problems: "Störungen: ", leave_in: "Haus verlassen innerhalb: ",
      enter_in: "Unscharf schalten innerhalb: ", by: "Durch ", by_unknown: "Durch: unbekannt", via: "Über ", practice: "Übungsmodus: keine Sirene, keine Meldungen", last_alarm: "Letzter Alarm: ", bypassed_now: "Überbrückt: ", false_alarm: " (Fehlalarm)", no_sensors: "Keine Sensoren", back: "Zurück", cancel: "Abbrechen",
      blocked: "Gesperrt", blocked_sub: "Dieses Bedienteil ist in Vigil gesperrt",
      refuse_alarm_condition: "Scharfschalten nicht möglich: {s} ist offen", refuse_sensor_unavailable: "Scharfschalten nicht möglich: {s} antwortet nicht", refuse_sensor_open: "Scharfschalten nicht möglich: {s} ist offen", refuse_not_disarmed: "Die Alarmanlage ist bereits scharf", force: "Überbrücken und scharf schalten",
      not_linked: "Nicht verknüpft",
      not_linked_sub: "Füge dieses Home-Assistant-Konto in Vigil unter Bedienteile hinzu. Konto: ",
      err_invalid_code: "Ungültiger Code", err_code_required: "Code erforderlich", err_locked_pre: "Zu viele falsche Codes. Erneut versuchen in ", err_locked_post: " Min", err_locked: "Zu viele falsche Codes. Bitte kurz warten", err_locked_permanent: "Zu viele falsche Codes. Gesperrt, bis ein Administrator in Vigil entsperrt", err_bypass_tamper: "Sabotage darf nicht überbrückt oder wiederhergestellt werden", err_bypass: "Sensoren dürfen nicht überbrückt oder wiederhergestellt werden", err_blocked: "Dieses Bedienteil ist gesperrt", err_not_allowed: "Dieses Bedienteil darf das nicht", err_no_installer_code: "Lege zuerst in Vigil einen Installateurcode fest", err_not_bypassable: "Dieser Sensor kann nicht überbrückt werden",
      old_profile: "Vigil oder die Karte aktualisieren", no_admin_code: "Lege zuerst in Vigil einen Installateurcode fest",
      st_closed: "geschlossen", st_open: "offen", st_waiting: "wartet", st_bypassed: "überbrückt",
      st_bypassed_at_arm: "beim Scharfschalten überbrückt", st_unavailable: "Störung",
      all: "Alle", mixed: "Gemischt", only_this: "nur diese Partition", default_tag: "Standard",
      cause_intrusion: "Einbruch", cause_fire: "Feuer", cause_gas: "Gas", cause_tamper: "Sabotage", cause_alarm24: "24-Stunden-Alarm", cause_silent24: "Stiller Alarm", cause_water: "Wasser",
      cause_fault: "Sensorstörung", ok: "OK", delete: "Löschen", code: "Code",
    },
    fr: {
      disarmed: "Désactivé", armed_home: "Maison", armed_away: "Absent", armed_night: "Nuit", armed_vacation: "Vacances", armed_custom_bypass: "Personnalisé", arming: "Activation",
      pending: "Entrée", triggered: "ALARME", offline: "Pas de connexion",
      home: "Maison", away: "Absent", night: "Nuit", vacation: "Vacances", custom: "Personnalisé", disarm: "Désactiver",
      home_sub: "Quelqu'un est à la maison", away_sub: "Tout le monde part", night_sub: "On va se coucher", vacation_sub: "Absent longtemps", custom_sub: "Votre choix", countdown: "Encore {n} secondes",
      arm_home: "Activer Maison", arm_away: "Activer Absent", arm_night: "Activer Nuit", arm_vacation: "Activer Vacances", arm_custom: "Activer Personnalisé",
      bypass: "Inhiber", unbypass: "Rétablir", bypass_title: "Inhiber : ", unbypass_title: "Rétablir : ",
      unlock_title: "Voir les capteurs", admin_code: "Code installateur", hint_user: "Saisissez votre code utilisateur", hint_admin: "Saisissez le code installateur", sensors: "Capteurs", sensors_open: "ouvert",
      all_closed: "Tout est fermé", open: "Ouvert : ", problems: "Défauts : ", leave_in: "Quittez la maison dans : ",
      enter_in: "Désactivez dans : ", by: "Par ", by_unknown: "Par : inconnu", via: "Via ", practice: "Mode d'entraînement : pas de sirène, pas de messages", last_alarm: "Dernière alarme : ", bypassed_now: "Inhibé : ", false_alarm: " (fausse alarme)", no_sensors: "Aucun capteur", back: "Retour", cancel: "Annuler",
      blocked: "Bloqué", blocked_sub: "Ce clavier est bloqué dans Vigil",
      refuse_alarm_condition: "Activation impossible : {s} est ouvert", refuse_sensor_unavailable: "Activation impossible : {s} ne répond pas", refuse_sensor_open: "Activation impossible : {s} est ouvert", refuse_not_disarmed: "L'alarme est déjà activée", force: "Inhiber et activer",
      not_linked: "Non associé",
      not_linked_sub: "Ajoutez ce compte Home Assistant dans Vigil sous Claviers. Compte : ",
      err_invalid_code: "Code invalide", err_code_required: "Un code est requis", err_locked_pre: "Trop de codes erronés. Réessayez dans ", err_locked_post: " min", err_locked: "Trop de codes erronés. Patientez un instant", err_locked_permanent: "Trop de codes erronés. Verrouillé jusqu'à ce qu'un administrateur le déverrouille dans Vigil", err_bypass_tamper: "Vous ne pouvez pas inhiber ou rétablir le sabotage", err_bypass: "Vous ne pouvez pas inhiber ou rétablir les capteurs", err_blocked: "Ce clavier est bloqué", err_not_allowed: "Ce clavier n'a pas le droit de faire cela", err_no_installer_code: "Définissez d'abord un code installateur dans Vigil", err_not_bypassable: "Ce capteur ne peut pas être inhibé",
      old_profile: "Mettez à jour Vigil ou la carte", no_admin_code: "Définissez d'abord un code installateur dans Vigil",
      st_closed: "fermé", st_open: "ouvert", st_waiting: "en attente", st_bypassed: "inhibé",
      all: "Tout", mixed: "Mixte", only_this: "uniquement cette partition", default_tag: "par défaut",
      st_bypassed_at_arm: "inhibé à l'activation", st_unavailable: "défaut",
      cause_intrusion: "Intrusion", cause_fire: "Incendie", cause_gas: "Gaz", cause_tamper: "Sabotage", cause_alarm24: "Alarme 24 h", cause_silent24: "Alarme silencieuse", cause_water: "Eau",
      cause_fault: "Défaut de capteur", ok: "OK", delete: "Effacer", code: "Code",
    },
    it: {
      disarmed: "Disinserito", armed_home: "Casa", armed_away: "Fuori casa", armed_night: "Notte", armed_vacation: "Vacanza", armed_custom_bypass: "Personalizzato", arming: "Inserimento",
      pending: "Ingresso", triggered: "ALLARME", offline: "Nessuna connessione",
      home: "Casa", away: "Fuori casa", night: "Notte", vacation: "Vacanza", custom: "Personalizzato", disarm: "Disinserisci",
      home_sub: "Qualcuno è in casa", away_sub: "Escono tutti", night_sub: "Si va a letto", vacation_sub: "Via per un periodo lungo", custom_sub: "La tua scelta", countdown: "Ancora {n} secondi",
      arm_home: "Inserisci Casa", arm_away: "Inserisci Fuori casa", arm_night: "Inserisci Notte", arm_vacation: "Inserisci Vacanza", arm_custom: "Inserisci Personalizzato",
      bypass: "Escludi", unbypass: "Ripristina", bypass_title: "Escludi: ", unbypass_title: "Ripristina: ",
      unlock_title: "Vedi sensori", admin_code: "Codice installatore", hint_user: "Inserisci il tuo codice utente", hint_admin: "Inserisci il codice installatore", sensors: "Sensori", sensors_open: "aperto",
      all_closed: "Tutto chiuso", open: "Aperto: ", problems: "Guasti: ", leave_in: "Esci di casa entro: ",
      enter_in: "Disinserisci entro: ", by: "Da ", by_unknown: "Da: sconosciuto", via: "Tramite ", practice: "Modalità prova: nessuna sirena, nessuna notifica", last_alarm: "Ultimo allarme: ", bypassed_now: "Escluso: ", false_alarm: " (falso allarme)", no_sensors: "Nessun sensore", back: "Indietro", cancel: "Annulla",
      blocked: "Bloccato", blocked_sub: "Questo pannello è bloccato in Vigil",
      refuse_alarm_condition: "Impossibile inserire: {s} è aperto", refuse_sensor_unavailable: "Impossibile inserire: {s} non risponde", refuse_sensor_open: "Impossibile inserire: {s} è aperto", refuse_not_disarmed: "L'allarme è già inserito", force: "Escludi e inserisci",
      not_linked: "Non collegato",
      not_linked_sub: "Aggiungi questo account Home Assistant in Vigil sotto Pannelli. Account: ",
      err_invalid_code: "Codice non valido", err_code_required: "È richiesto un codice", err_locked_pre: "Troppi codici errati. Riprova tra ", err_locked_post: " min", err_locked: "Troppi codici errati. Attendi un momento", err_locked_permanent: "Troppi codici errati. Bloccato finché un amministratore non lo sblocca in Vigil", err_bypass_tamper: "Non puoi escludere o ripristinare la manomissione", err_bypass: "Non puoi escludere o ripristinare i sensori", err_blocked: "Questo pannello è bloccato", err_not_allowed: "Questo pannello non può farlo", err_no_installer_code: "Imposta prima un codice installatore in Vigil", err_not_bypassable: "Questo sensore non può essere escluso",
      old_profile: "Aggiorna Vigil o la scheda", no_admin_code: "Imposta prima un codice installatore in Vigil",
      all: "Tutto", mixed: "Misto", only_this: "solo questa partizione", default_tag: "predefinita",
      st_closed: "chiuso", st_open: "aperto", st_waiting: "in attesa", st_bypassed: "escluso",
      st_bypassed_at_arm: "escluso all'inserimento", st_unavailable: "guasto",
      cause_intrusion: "Intrusione", cause_fire: "Incendio", cause_gas: "Gas", cause_tamper: "Manomissione", cause_alarm24: "Allarme 24 ore", cause_silent24: "Allarme silenzioso", cause_water: "Acqua",
      cause_fault: "Guasto sensore", ok: "OK", delete: "Cancella", code: "Codice",
    },
    es: {
      disarmed: "Desactivada", armed_home: "En casa", armed_away: "Fuera", armed_night: "Noche", armed_vacation: "Vacaciones", armed_custom_bypass: "Personalizado", arming: "Activando",
      pending: "Entrada", triggered: "ALARMA", offline: "Sin conexión",
      home: "En casa", away: "Fuera", night: "Noche", vacation: "Vacaciones", custom: "Personalizado", disarm: "Desactivar",
      home_sub: "Hay alguien en casa", away_sub: "Todos se van", night_sub: "A dormir", vacation_sub: "Fuera por mucho tiempo", custom_sub: "A tu elección", countdown: "Quedan {n} segundos",
      arm_home: "Activar En casa", arm_away: "Activar Fuera", arm_night: "Activar Noche", arm_vacation: "Activar Vacaciones", arm_custom: "Activar Personalizado",
      bypass: "Anular", unbypass: "Restablecer", bypass_title: "Anular: ", unbypass_title: "Restablecer: ",
      unlock_title: "Ver sensores", admin_code: "Código de instalador", hint_user: "Introduce tu código de usuario", hint_admin: "Introduce el código de instalador", sensors: "Sensores", sensors_open: "abierto",
      all_closed: "Todo cerrado", open: "Abierto: ", problems: "Averías: ", leave_in: "Sal de casa antes de: ",
      enter_in: "Desactiva antes de: ", by: "Por ", by_unknown: "Por: desconocido", via: "Mediante ", practice: "Modo de prueba: sin sirena, sin avisos", last_alarm: "Última alarma: ", bypassed_now: "Anulado: ", false_alarm: " (falsa alarma)", no_sensors: "Sin sensores", back: "Atrás", cancel: "Cancelar",
      blocked: "Bloqueado", blocked_sub: "Este panel está bloqueado en Vigil",
      refuse_alarm_condition: "No se puede activar: {s} está abierto", refuse_sensor_unavailable: "No se puede activar: {s} no responde", refuse_sensor_open: "No se puede activar: {s} está abierto", refuse_not_disarmed: "La alarma ya está activada", force: "Anular y activar",
      not_linked: "Sin vincular",
      not_linked_sub: "Añade esta cuenta de Home Assistant en Vigil, en Paneles. Cuenta: ",
      err_invalid_code: "Código no válido", err_code_required: "Se necesita un código", err_locked_pre: "Demasiados códigos erróneos. Inténtalo de nuevo en ", err_locked_post: " min", err_locked: "Demasiados códigos erróneos. Espera un momento", err_locked_permanent: "Demasiados códigos erróneos. Bloqueado hasta que un administrador lo desbloquee en Vigil", err_bypass_tamper: "No puedes anular ni restablecer el sabotaje", err_bypass: "No puedes anular ni restablecer sensores", err_blocked: "Este panel está bloqueado", err_not_allowed: "Este panel no puede hacer esto", err_no_installer_code: "Define primero un código de instalador en Vigil", err_not_bypassable: "Este sensor no se puede anular",
      all: "Todo", mixed: "Mixto", only_this: "solo esta partición", default_tag: "predeterminada",
      old_profile: "Actualiza Vigil o la tarjeta", no_admin_code: "Define primero un código de instalador en Vigil",
      st_closed: "cerrado", st_open: "abierto", st_waiting: "en espera", st_bypassed: "anulado",
      st_bypassed_at_arm: "anulado al activar", st_unavailable: "avería",
      cause_intrusion: "Intrusión", cause_fire: "Incendio", cause_gas: "Gas", cause_tamper: "Sabotaje", cause_alarm24: "Alarma 24 h", cause_silent24: "Alarma silenciosa", cause_water: "Agua",
      cause_fault: "Avería de sensor", ok: "OK", delete: "Borrar", code: "Código",
    },
  };
  const PROFILE_VERSION = 1;
  // One colour per situation; the same set is used by the ESPHome panel (vigil_panel.h). Modes have their own colour.
  const COLORS = {
    none: "#8A94A6", disarmed: "#4CCB8F", notready: "#F2B84B", armed_home: "#5B9BF0", armed_away: "#FF8A5B",
    armed_night: "#9A8CF2", armed_vacation: "#4FC3C9", armed_custom_bypass: "#D58BDD", arming: "#F2B84B", pending: "#FF9F43", triggered: "#F0605D",
  };
  const MODE_COLORS = { home: "#5B9BF0", away: "#FF8A5B", night: "#9A8CF2", vacation: "#4FC3C9", custom: "#D58BDD" };
  const ICONS = {
    shield: '<path d="M12 3l7 3v5c0 5-3.2 8.2-7 10-3.8-1.8-7-5-7-10V6z"/>',
    check: '<path d="M9 12l2.2 2.2L15.5 10"/>',
    alert: '<path d="M12 8v4M12 15.5h.01"/>',
    siren: '<path d="M7 18v-5a5 5 0 0110 0v5"/><path d="M5 18h14M12 3v2M4.5 6.5l1.4 1.4M19.5 6.5l-1.4 1.4"/>',
    exit: '<path d="M10 4H5v16h5"/><path d="M15 8l4 4-4 4M19 12H9"/>',
    home: '<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>',
    moon: '<path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z"/>',
    unlock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 017.5-2"/>',
    grid: '<rect x="4" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    back: '<path d="M15 6l-6 6 6 6"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
    erase: '<path d="M9 6h11v12H9l-5-6z"/><path d="M12.5 9.5l5 5M17.5 9.5l-5 5"/>',
    tick: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  };
  const icon = (name, size = 24, extra = "") =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true" ${extra}>${ICONS[name] || ""}</svg>`;
  const RING = 364.4;  // circumference of the ring (radius 58)
  // Phrases from Home Assistant's own answer (translations/<language>.json, exceptions); one list per language, in the order
  // en, nl, de, fr, it, es. The first row that matches wins, so the more specific phrases come first (a test checks the phrases).
  const ERROR_ROWS = [
    [["until an administrator", "totdat een beheerder", "bis ein Administrator", "jusqu'à ce qu'un administrateur", "finché un amministratore", "hasta que un administrador"], "err_locked_permanent"],
    [["Too many wrong codes", "Te veel foute codes", "Zu viele falsche Codes", "Trop de codes erronés", "Troppi codici errati", "Demasiados códigos erróneos"], "err_locked"],
    [["Invalid code", "Ongeldige code", "Ungültiger Code", "Code invalide", "Codice non valido", "Código no válido"], "err_invalid_code"],
    [["A code is required", "Een code is vereist", "Ein Code ist erforderlich", "Un code est requis", "È richiesto un codice", "Se necesita un código"], "err_code_required"],
    [["right to bypass tamper", "recht om sabotage te omzeilen", "Sabotage überbrücken", "droit d'inhiber le sabotage", "diritto di escludere la manomissione", "derecho de anular sabotaje"], "err_bypass_tamper"],
    [["right to bypass", "recht om te omzeilen", "Überbrückungsrecht", "droit d'inhiber", "diritto di esclusione", "derecho de anular"], "err_bypass"],
    [["is blocked", "is geblokkeerd", "ist gesperrt", "est bloqué", "è bloccato", "está bloqueado"], "err_blocked"],
    [["may not do this", "mag dit niet", "darf das nicht", "n'a pas le droit de faire cela", "non può farlo", "no puede hacer esto"], "err_not_allowed"],
    [["no installer code", "geen installateurscode", "keinen Installateurcode", "pas de code installateur", "non ha un codice installatore", "no tiene código de instalador"], "err_no_installer_code"],
    [["cannot be bypassed", "kan niet worden omzeild", "kann nicht überbrückt werden", "ne peut pas être inhibé", "non può essere escluso", "no se puede anular"], "err_not_bypassable"],
  ];
  const ADMIN_ACTIONS = [];  // the sensor list opens with any user code (or the installer code); the card has no info page
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const clean = (v) => (v === null || v === undefined || v === "None" || v === "unknown" || v === "unavailable" ? "" : String(v));

  class VigilCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._ui = { keypad: null, view: "main", unlocked: false, message: "", busy: false };
      this._key = "";
      this._info = null; // the answer of Vigil: which panel is this user
      this._failed = false;
      this._config = {};
    }

    setConfig(config) {
      this._config = config || {};
    }
    getCardSize() {
      return 8;
    }
    static getStubConfig() {
      return {};
    }

    connectedCallback() {
      this._hello();
      this._helloTimer = setInterval(() => this._hello(), 60000);
      this._tick = setInterval(() => this._countdown(), 1000);
      this.addEventListener("pointerdown", () => this._touch());
      // A real keyboard works on the keypad too (a tablet with a keyboard, or a computer).
      this._onKey = (ev) => this._keyPressed(ev);
      window.addEventListener("keydown", this._onKey);
      this._touch();
    }
    disconnectedCallback() {
      window.removeEventListener("keydown", this._onKey);
      clearInterval(this._helloTimer);
      clearInterval(this._tick);
      clearTimeout(this._idle);
      clearTimeout(this._back);
      clearTimeout(this._msgTimer);
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._info && !this._asked) this._hello();
      const key = this._snapshotKey();
      if (key === this._key) return;
      this._key = key;
      if (!this._p() || this._p().unlocked === false) this._ui.unlocked = false;
      this._route();
      this._render();
    }

    // ----------------------------------------------------------- talking to Vigil
    async _hello() {
      if (!this._hass) return;
      this._asked = true;
      try {
        const info = await this._hass.callWS({ type: "vigil_alarm/tablet" });
        this._info = info;
        this._failed = false;
      } catch (err) {
        this._failed = true;
      }
      this._key = "";
      this.hass = this._hass;
    }

    // ------------------------------------------------------------- partitions
    // The partitions this tablet may use (Vigil sends them), and the choice "all" when it may use more than one.
    _parts() {
      return (this._info && Array.isArray(this._info.partitions) ? this._info.partitions : []).filter((x) => x && x.alarm);
    }
    _multi() { return this._parts().length > 1; }
    _hasAll() { return this._multi() && !!(this._info && this._info.all_entity); }
    // The partition this tablet starts on and returns to: its default (an id or "all"), else the first.
    _default() {
      const d = this._info && this._info.default_partition;
      const parts = this._parts();
      return d === "all" ? (this._hasAll() ? "all" : parts[0] && parts[0].id) : parts.some((x) => x.id === d) ? d : parts[0] && parts[0].id;
    }
    // Back to the default after the time set in Vigil without touch; not while an alarm is going.
    _armReturn() {
      clearTimeout(this._back);
      const seconds = Number(this._info && this._info.return_seconds) || 0;
      if (!this._multi() || !seconds || !this._ui.partition || this._ui.partition === this._default()) return;
      this._back = setTimeout(() => {
        const a = this._alarm();
        const busy = this._parts().some((x) => ["triggered", "pending", "arming"].includes((this._hass && this._hass.states[x.alarm] || {}).state)) ||
          (a && ["triggered", "pending", "arming"].includes(a.state));
        if (busy || this._ui.keypad) { this._armReturn(); return; }
        this._ui.partition = null;
        this._ui.view = "main";
        this._key = "";
        this._render();
      }, seconds * 1000);
    }
    // The partition on screen: the choice of the person if it still exists, else the first.
    _sel() {
      const parts = this._parts();
      const want = this._ui.partition || this._default();
      if (want === "all" && this._hasAll()) {
        const modes = ["home", "away", "night", "vacation", "custom"].filter((m) => parts.some((x) => (x.modes || []).includes(m)));
        return { id: "all", name: this.tr("all"), alarm: this._info.all_entity, modes };
      }
      return parts.find((x) => x.id === want) || parts[0] || null;
    }
    // The texts and counts of what is on screen: of one partition, or added up for "all".
    _pp() {
      const p = this._p();
      const sel = this._sel();
      if (!p || !Array.isArray(p.partitions) || !sel) return null;
      const mine = sel.id === "all" ? p.partitions : p.partitions.filter((x) => x.id === sel.id);
      if (!mine.length) return null;
      const text = (k) => mine.map((x) => clean(x[k])).filter(Boolean).join(", ");
      const count = (k) => mine.reduce((n, x) => n + (Number(x[k]) || 0), 0);
      return { open_count: count("open_count"), faults_count: count("faults_count"), open_sensors_text: text("open_sensors_text"),
        faults_text: text("faults_text"), open_now_text: text("open_now_text"), bypassed_text: text("bypassed_text") };
    }
    // One value of the profile, from the partition on screen when Vigil sends them per partition.
    _pv(key) {
      const pp = this._pp();
      const p = this._p();
      return pp && pp[key] !== undefined ? pp[key] : p ? p[key] : undefined;
    }
    _partitionArg() {
      const sel = this._sel();
      return this._multi() && sel ? { partition: sel.id } : {};
    }
    _alarm() {
      const sel = this._sel();
      const id = (sel && sel.alarm) || (this._info && this._info.alarm_entity);
      return id && this._hass ? this._hass.states[id] : null;
    }
    _profile() {
      const id = this._info && this._info.profile_entity;
      return id && this._hass ? this._hass.states[id] : null;
    }
    _p() {
      const s = this._profile();
      return s ? s.attributes : null;
    }
    _snapshotKey() {
      const a = this._alarm();
      const p = this._profile();
      const others = this._hass ? this._parts().map((x) => (this._hass.states[x.alarm] || {}).state) : [];
      return JSON.stringify([this._info, this._failed, this._ui.partition, others, a && [a.state, a.attributes], p && [p.state, p.attributes],
        this._hass && this._hass.language]);
    }

    // -------------------------------------------------------------------- texts
    _lang() {
      const p = this._p();
      const l = String((p && p.language) || (this._hass && this._hass.language) || "en").toLowerCase().slice(0, 2);
      return TEXTS[l] ? l : "en";
    }
    tr(key) {
      return (TEXTS[this._lang()] || TEXTS.en)[key] || key;
    }

    // ---------------------------------------------------------------- the logic
    _stateKnown() {
      const a = this._alarm();
      return !!a && !this._failed && !["unknown", "unavailable", ""].includes(a.state);
    }
    _linked() {
      const p = this._p();
      return !!p && Number(p.profile_version) === PROFILE_VERSION;
    }
    _usable() {
      const p = this._p();
      return !!this._info && this._info.linked && this._stateKnown() && this._linked() && !p.blocked;
    }
    _unlockedNow() {
      const p = this._p();
      return this._ui.unlocked && !!p && !!p.unlocked;
    }
    _sensorsVisible() {
      const p = this._p();
      return !!p && (p.sensor_list === "always" || (p.sensor_list === "code" && this._unlockedNow()));
    }
    _detailsVisible() {
      const p = this._p();
      return !!p && (p.sensor_list === "always" || this._unlockedNow());
    }
    _showSensorsButton() {
      const p = this._p();
      return this._usable() && p.sensor_list !== "never";
    }
    _rows() {
      const p = this._p();
      const sel = this._sel();
      // More than one partition: the list of all of them, narrowed to the partition on screen (safety sensors are in all).
      const many = this._multi() && p && p.sensors_all;
      return String((many ? p.sensors_all : p && p.sensors) || "")
        .split("\n")
        .map((line) => line.split("|"))
        .filter((f) => f.length >= 4)
        .map((f) => ({ name: f[0], entity: f[1], status: f[2], bypassable: f[3] === "1", partition: f[4] || "" }))
        .filter((r) => !many || !sel || sel.id === "all" || !r.partition || r.partition === sel.id);
    }
    _openTotal() {
      const rows = this._rows();
      if (rows.length) return rows.filter((r) => r.status === "open" || r.status === "waiting").length;
      return Number(this._pv("open_count") || 0);
    }
    _bypassAllowed() {
      return this._usable() && !!this._p().can_bypass;
    }
    _needsCode(action) {
      if (["disarm", "unlock", "bypass", "unbypass"].includes(action)) return true;
      const p = this._p();
      return !p || p.code_arm_required !== false;
    }
    _secondsLeft() {
      const a = this._alarm();
      const at = a && a.attributes;
      if (!at || !at.delay_end) { this._delayKey = null; return -1; }
      // Count from the seconds left on this device's own clock, so a clock that is off does not show.
      if (this._delayKey !== at.delay_end) {
        this._delayKey = at.delay_end;
        const left = Number(at.delay_left);
        this._delayLocal = Number.isFinite(left) ? Date.now() / 1000 + left : Number(at.delay_end);
        this._delayTotal = Math.max(1, this._delayLocal - Date.now() / 1000);
      }
      return Math.max(0, Math.ceil(this._delayLocal - Date.now() / 1000));
    }
    _title() {
      if (this._info && !this._info.linked && !this._failed) return this.tr("not_linked");
      if (!this._info || this._failed || !this._stateKnown()) return this.tr("offline");
      if (!this._p()) return this.tr("not_linked");
      if (!this._linked()) return this.tr("not_linked");
      if (this._p().blocked) return this.tr("blocked");
      const a = this._alarm();
      const sel = this._multi() ? this._sel() : null;
      const own = sel ? sel.name + ": " : "";
      if (a.attributes && a.attributes.mixed === true) return own + this.tr("mixed");
      const s = a.state;
      return own + (TEXTS.en[s] ? this.tr(s) : s);
    }
    // What the ring shows: one of the keys of COLORS.
    _kind() {
      if (!this._usable()) return "none";
      const state = this._alarm().state;
      if (state === "disarmed" && this._openTotal() > 0) return "notready";
      return COLORS[state] ? state : "none";
    }
    _color() {
      return COLORS[this._kind()];
    }
    _fraction() {
      const left = this._secondsLeft();
      return left < 0 ? 1 : Math.min(1, left / (this._delayTotal || left || 1));
    }
    _sub() {
      if (this._ui.message) return this._ui.message;
      if (this._info && !this._info.linked) return this.tr("not_linked_sub") + (this._info.user || "");
      if (!this._stateKnown()) return "";
      if (!this._p()) return "";
      if (!this._linked()) return this.tr("old_profile");
      const p = this._p();
      if (p.blocked) return this.tr("blocked_sub");
      const a = this._alarm();
      const s = a.state;
      const at = a.attributes;
      const out = [];
      const add = (t) => t && out.push(t);
      const left = this._secondsLeft();
      const armed = ["armed_home", "armed_away", "armed_night", "armed_vacation", "armed_custom_bypass"].includes(s);
      if (s === "disarmed") {
        if (Number(this._pv("open_count")) > 0) add(this.tr("open") + this._pv("open_count"));
        else add(this.tr("all_closed"));
        if (this._detailsVisible()) add(this._lastAlarm(at));
        // Disarmed and still bypassed: that is a permanent bypass, which must not be forgotten.
        const left_out = Array.isArray(at.bypassed_sensors) ? at.bypassed_sensors.map(clean).filter(Boolean) : [];
        if (left_out.length && this._detailsVisible()) add(this.tr("bypassed_now") + left_out.join(", "));
        if (clean(this._pv("faults_text"))) add(this.tr("problems") + clean(this._pv("faults_text")));
        else if (Number(this._pv("faults_count")) > 0 || Number(p.problems_count) > 0) {
          add(this.tr("problems") + (Number(this._pv("faults_count")) > 0 ? this._pv("faults_count") : p.problems_count));
        }
      } else if (armed) {
        if (this._detailsVisible()) {
          if (clean(at.changed_by)) add(this.tr("by") + clean(at.changed_by));
          else if (clean(at.changed_via)) add(this.tr("by_unknown"));
          if (clean(at.changed_via)) add(this.tr("via") + clean(at.changed_via));
          if (clean(this._pv("open_sensors_text"))) add(this.tr("open") + clean(this._pv("open_sensors_text")));
        }
      } else if (s === "arming") {
        const m = clean(at.mode);
        if (TEXTS.en[m]) add(this.tr(m));
        if (left >= 0) add(this.tr("leave_in") + left + " s");
        if (clean(this._pv("open_sensors_text"))) add(this.tr("open") + clean(this._pv("open_sensors_text")));
      } else if (s === "pending") {
        if (left >= 0) add(this.tr("enter_in") + left + " s");
        if (this._detailsVisible()) add(clean(at.cause_sensor));
      } else if (s === "triggered") {
        const c = clean(at.cause);
        if (c) add(TEXTS.en["cause_" + c] ? this.tr("cause_" + c) : c);
        if (this._detailsVisible()) add(clean(at.cause_sensor));
      }
      if (at.practice === true) out.unshift(this.tr("practice"));
      return out.join("\n");
    }
    // "Last alarm: 14:03 Front door → Hall → Living room": the path the intruder took, from the alarm memory.
    _lastAlarm(at) {
      const m = at && at.last_alarm;
      if (!m || !m.time) return "";
      const time = new Date(m.time * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      const path = Array.isArray(m.path) ? m.path.map(clean).filter(Boolean).join(" → ") : "";
      return this.tr("last_alarm") + time + (path ? " " + path : clean(m.sensor) ? " " + clean(m.sensor) : "") + (m.cancelled ? this.tr("false_alarm") : "");
    }
    _modeButtons() {
      const p = this._p();
      const a = this._alarm();
      // "All" with some partitions armed and some not still arms the ones that are not.
      if (!this._usable() || (a.state !== "disarmed" && !(a.attributes && a.attributes.mixed === true))) return [];
      const sel = this._sel();
      if (this._multi() && sel) return ["home", "away", "night", "vacation", "custom"].filter((m) => (sel.modes || []).includes(m));
      const mask = Number(p.modes_mask) || 0;
      return [["home", 1], ["away", 2], ["night", 4], ["vacation", 8], ["custom", 16]].filter(([, bit]) => mask & bit).map(([m]) => m);
    }
    _showDisarm() {
      return this._usable() && this._alarm().state !== "disarmed" && !!this._p().can_disarm;
    }
    _sensorsButtonText() {
      const open = this._openTotal();
      return this.tr("sensors") + (open > 0 ? `  (${open} ${this.tr("sensors_open")})` : "");
    }

    // --------------------------------------------------------------------- keypad
    _touch() {
      this._armReturn();
      clearTimeout(this._idle);
      const seconds = Number(this._config.idle_timeout) || 30;
      this._idle = setTimeout(() => {
        // Nobody touched the card: forget the code and go back to the main page. Is someone still supposed to
        // disarm, then the keypad comes back by itself.
        this._ui.keypad = null;
        this._ui.view = "main";
        this._ui.unlocked = false;
        this._route();
        this._render();
      }, seconds * 1000);
    }
    _openKeypad(action, extra = {}) {
      this._ui.keypad = { action, code: "", error: "", ...extra };
      this._render();
    }
    _closeKeypad() {
      this._ui.keypad = null;
      this._render();
    }
    // The keypad never opens by itself: whoever sees the alarm presses Disarm. It does close when it has become pointless.
    _route() {
      const k = this._ui.keypad;
      if (!k) return;
      const a = this._stateKnown() ? this._alarm() : null;
      const s = a ? a.state : "";
      const mixed = !!(a && a.attributes && a.attributes.mixed === true);  // "all": some armed, some not
      if (k.action === "disarm" && s === "disarmed") this._ui.keypad = null;
      else if (k.action.startsWith("arm_") && s !== "disarmed" && !mixed) this._ui.keypad = null;
    }
    _start(action, extra = {}) {
      if (ADMIN_ACTIONS.includes(action) && !this._p().has_admin_code) {
        this._flash(this.tr("no_admin_code"));
        return;
      }
      if (this._needsCode(action) || extra.force) this._openKeypad(action, extra);
      else this._run(action, "", extra);
    }
    _flash(text) {
      this._ui.message = text;
      clearTimeout(this._msgTimer);
      this._msgTimer = setTimeout(() => {
        this._ui.message = "";
        this._ui.force = null;
        this._render();
      }, 8000);
      this._render();
    }
    async _run(action, code, extra = {}) {
      const source = this._info.panel_id;
      const call = (service, data) => this._hass.callService("vigil_alarm", service, data);
      const withCode = (data) => (code ? { ...data, code } : data);
      this._ui.busy = true;
      try {
        if (action.startsWith("arm_")) await call("arm", withCode({ mode: action.slice(4), source, ...this._partitionArg(), ...(extra.force ? { bypass_open: true } : {}) }));
        else if (action === "disarm") await call("disarm", { code, source, ...this._partitionArg() });
        else if (action === "bypass") await call("bypass", { sensor: extra.entity, code, source });
        else if (action === "unbypass") await call("unbypass", { sensor: extra.entity, code, source });
        else if (action === "unlock") await call("unlock_panel", { code, source, scope: "sensors" });
        this._ui.busy = false;
        this._done(action);
      } catch (err) {
        this._ui.busy = false;
        const raw = (err && (err.message || err.error)) || String(err);
        const refused = action.startsWith("arm_") ? this._refusal(raw) : null;
        if (refused) {
          // Not a wrong code: something stops arming. Say what, and offer to bypass it and arm if that is allowed.
          this._ui.keypad = null;
          this._ui.force = !extra.force && refused.reason !== "not_disarmed" && this._bypassAllowed() ? { action } : null;
          this._flash(refused.text);
          return;
        }
        const text = this._localError(raw);
        if (this._ui.keypad) {
          this._ui.keypad.code = "";
          this._ui.keypad.error = text;
          this._render();
        } else this._flash(text);
      }
    }
    // "Arming refused: alarm_condition (Front door)." in the language of the panel.
    _refusal(raw) {
      const m = raw.match(/(?:Arming refused|Inschakelen geweigerd|Scharfschalten abgelehnt|Activation refusée|Inserimento rifiutato|Activación rechazada)\s?: (\w+) \(([^)]*)\)/);
      if (!m || !this.tr("refuse_" + m[1])) return null;
      return { reason: m[1], text: this.tr("refuse_" + m[1]).replace("{s}", m[2] || "?") };
    }
    // Home Assistant answers in its own language; Vigil's known refusals are shown in the language of the panel.
    // The phrases must keep matching translations/*.json (a test checks that).
    _localError(raw) {
      for (const [phrases, key] of ERROR_ROWS) {
        if (!phrases.some((x) => raw.includes(x))) continue;
        if (key !== "err_locked") return this.tr(key);
        const m = raw.match(/\d+/);
        return m ? this.tr("err_locked_pre") + m[0] + this.tr("err_locked_post") : this.tr("err_locked");
      }
      return raw;
    }
    _done(action) {
      this._ui.message = "";
      this._ui.force = null;
      this._ui.keypad = null;
      if (action === "unlock") {
        this._ui.unlocked = true;
        this._ui.view = "sensors";
      }
      this._render();
    }
    // Digits type the code, Backspace deletes, Enter confirms, Escape closes the keypad. Only while the keypad is open,
    // and never when you are typing in a field somewhere else on the dashboard.
    _keyPressed(ev) {
      if (!this._ui.keypad || ev.ctrlKey || ev.metaKey || ev.altKey || ev.defaultPrevented) return;
      const typing = ev.composedPath().some((n) => n.tagName && (/^(INPUT|TEXTAREA|SELECT)$/.test(n.tagName) || n.isContentEditable));
      if (typing) return;
      if (/^[0-9]$/.test(ev.key)) this._digit(ev.key);
      else if (ev.key === "Backspace" || ev.key === "Delete") this._backspace();
      else if (ev.key === "Enter") this._submit();
      else if (ev.key === "Escape") this._closeKeypad();
      else return;
      ev.preventDefault();
      this._touch();
    }
    _digit(d) {
      const k = this._ui.keypad;
      if (!k || k.code.length >= 12) return;
      k.code += d;
      this._renderCode();
    }
    _backspace() {
      const k = this._ui.keypad;
      if (!k) return;
      k.code = k.code.slice(0, -1);
      this._renderCode();
    }
    _submit() {
      const k = this._ui.keypad;
      if (!k || !k.code || this._ui.busy) return;
      const { action, code, entity, force } = k;
      k.error = "";
      this._run(action, code, { entity, force });
    }

    _keypadTitle(k) {
      switch (k.action) {
        case "arm_home": case "arm_away": case "arm_night": case "arm_vacation": case "arm_custom": case "disarm": return this.tr(k.action);
        case "bypass": return this.tr("bypass_title") + (k.name || "");
        case "unbypass": return this.tr("unbypass_title") + (k.name || "");
        case "unlock": return this.tr("unlock_title");
      }
      return "";
    }

    // ------------------------------------------------------------------ rendering
    _countdown() {
      const a = this._alarm();
      if (a && (a.state === "arming" || a.state === "pending")) {
        const root = this.shadowRoot;
        const sub = root.querySelector(".subs");
        if (sub) sub.innerHTML = this._subHtml();
        const left = this._secondsLeft();
        const num = root.querySelector(".ring-num");
        if (num && left >= 0) num.textContent = String(left);
        const arc = root.querySelector(".ring-arc");
        if (arc) arc.setAttribute("stroke-dasharray", `${(RING * this._fraction()).toFixed(1)} ${RING}`);
      }
    }
    _renderCode() {
      const k = this._ui.keypad;
      const el = this.shadowRoot.querySelector(".dots");
      if (el && k) el.innerHTML = this._dotsHtml(k);
    }

    _render() {
      const root = this.shadowRoot;
      const keypad = this._ui.keypad;
      const sensorsView = this._ui.view === "sensors" && this._sensorsVisible() && this._usable();
      if (this._ui.view === "sensors" && !sensorsView) this._ui.view = "main";
      const kind = this._kind();
      const c = COLORS[kind];
      const name = this._info && this._info.name ? esc(this._info.name) : "";
      const header = `<header class="top"><img class="logo" src="/vigil_alarm_static/logo.png" alt=""><span class="brand">Vigil Alarm</span><span class="pname">${name}</span></header>${keypad || sensorsView ? "" : this._partsHtml()}`;
      let body;
      if (sensorsView && !keypad) body = this._sensorsHtml();
      else body = `<div class="grid ${keypad ? "has-keypad" : ""}">
        <section class="status">${this._ringHtml(kind, c)}<div class="title">${esc(this._title())}</div><div class="subs">${this._subHtml()}</div></section>
        <section class="side">${keypad ? this._keypadHtml(keypad) : this._sideHtml()}</section></div>`;
      root.innerHTML = `<style>${STYLE}</style><ha-card class="k-${kind}" style="--c:${c}">${header}${body}</ha-card>`;
      root.querySelectorAll("[data-act]").forEach((el) =>
        el.addEventListener("click", (ev) => this._click(el, ev)));
    }

    // More than one partition: a button for each, coloured by its state, and "All" when the tablet may use more than one.
    _partsHtml() {
      if (!this._hass) return "";
      const sel = this._sel();
      if (!this._multi()) {
        // One partition on this tablet, but the house has more: say which one it is.
        const only = this._parts()[0];
        if (!only || !(Number(this._info && this._info.partition_total) > 1)) return "";
        const st = (this._hass.states[only.alarm] || {}).state;
        return `<div class="one" style="--c:${COLORS[st] || COLORS.none}"><span class="cdot"></span><b>${esc(only.name)}</b><span>${esc(this.tr("only_this"))}</span></div>`;
      }
      const dflt = this._default();
      const chip = (id, label, state) => `<button class="chip ${sel && sel.id === id ? "on" : ""}" style="--c:${COLORS[state] || COLORS.none}" data-act="part" data-id="${esc(id)}"><span class="cdot"></span>${esc(label)}${id === dflt ? `<small>${esc(this.tr("default_tag"))}</small>` : ""}</button>`;
      const items = this._parts().map((x) => chip(x.id, x.name, (this._hass.states[x.alarm] || {}).state));
      if (this._hasAll()) {
        const a = this._hass.states[this._info.all_entity] || {};
        items.push(chip("all", this.tr("all"), a.attributes && a.attributes.mixed === true ? "notready" : a.state));
      }
      return `<div class="chips">${items.join("")}</div>`;
    }

    _ringHtml(kind, c) {
      const counting = kind === "arming" || kind === "pending";
      const left = this._secondsLeft();
      let inner;
      if (counting && left >= 0) {
        inner = `<text class="ring-num" x="66" y="66" text-anchor="middle" dominant-baseline="central">${left}</text>`;
      } else {
        const a = this._alarm();
        const state = this._usable() && a ? a.state : "";
        const glyph = kind === "triggered" ? "siren" : kind === "notready" ? "shield" : state === "armed_home" ? "home"
          : state === "armed_away" ? "exit" : state === "armed_night" ? "moon" : state === "armed_vacation" ? "exit" : state === "armed_custom_bypass" ? "grid" : "shield";
        const extra = kind === "disarmed" ? ICONS.check : kind === "notready" ? ICONS.alert : "";
        inner = `<g transform="translate(33 33) scale(2.75)" class="ring-icon">${ICONS[glyph]}${extra}</g>`;
      }
      const dash = counting && left >= 0 ? `${(RING * this._fraction()).toFixed(1)} ${RING}` : `${RING} ${RING}`;
      const label = counting && left >= 0 ? this.tr("countdown").replace("{n}", left) : this._title();
      return `<svg class="ring" viewBox="0 0 132 132" role="img" aria-label="${esc(label)}">
        <circle class="ring-track" cx="66" cy="66" r="58"/>
        <circle class="ring-arc" cx="66" cy="66" r="58" transform="rotate(-90 66 66)" stroke-dasharray="${dash}"/>
        <circle class="ring-core" cx="66" cy="66" r="46"/>${inner}</svg>`;
    }

    // The first line of the text under the title is the one that matters; the rest is detail.
    _subHtml() {
      const lines = this._sub().split("\n").filter((l) => l);
      return lines.map((l, i) => `<div class="${i === 0 ? "s1" : "s2"}">${esc(l)}</div>`).join("");
    }

    _sideHtml() {
      const modes = this._modeButtons().map((m) => `<button class="mode" style="--m:${MODE_COLORS[m]}" data-act="arm" data-mode="${m}">
          <span class="dot">${icon(m === "away" || m === "vacation" ? "exit" : m === "home" ? "home" : m === "custom" ? "grid" : "moon", 26)}</span>
          <span class="mt"><span class="mn">${esc(this.tr(m))}</span><span class="ms">${esc(this.tr(m + "_sub"))}</span></span>
          ${icon("chevron", 22, 'class="chev"')}</button>`).join("");
      const disarm = this._showDisarm()
        ? `<button class="disarm" data-act="disarm">${icon("unlock", 28)}<span>${esc(this.tr("disarm"))}</span></button>` : "";
      const force = this._ui.force && this._bypassAllowed()
        ? `<button class="force" data-act="force">${icon("exit", 24)}<span>${esc(this.tr("force"))}</span></button>` : "";
      const sensors = this._showSensorsButton()
        ? `<button class="sensors" data-act="sensors"><span class="dot s">${icon("grid", 22)}</span><span class="mn">${esc(this.tr("sensors"))}</span>${this._openTotal() > 0 ? `<span class="badge">${this._openTotal()}</span>` : ""}${icon("chevron", 20, 'class="chev"')}</button>` : "";
      return `<div class="modes">${modes}${disarm}${force}</div>${sensors}`;
    }

    _dotsHtml(k) {
      const n = Math.max(4, k.code.length);
      let out = "";
      for (let i = 0; i < n; i++) out += `<i class="${i < k.code.length ? "on" : ""}"></i>`;
      return out;
    }

    _keypadHtml(k) {
      const keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        .map((d) => `<button class="key" data-act="digit" data-d="${d}">${d}</button>`).join("");
      const placeholder = ADMIN_ACTIONS.includes(k.action) ? this.tr("admin_code") : this.tr("code");
      const placeholder_hint = this.tr(ADMIN_ACTIONS.includes(k.action) ? "hint_admin" : "hint_user");
      const glyph = k.action === "disarm" ? "unlock" : k.action.startsWith("arm_") ? "shield" : "grid";
      return `<div class="kp-head"><span class="dot">${icon(glyph, 24)}</span>
          <span class="mt"><span class="mn">${esc(this._keypadTitle(k))}</span><span class="ms err ${k.error ? "bad" : ""}">${esc(k.error || placeholder_hint)}</span></span></div>
        <div class="dots" aria-label="${esc(placeholder)}">${this._dotsHtml(k)}</div>
        <div class="keys">${keys}
          <button class="key sec" data-act="backspace" aria-label="${esc(this.tr("delete"))}">${icon("erase", 28)}</button>
          <button class="key" data-act="digit" data-d="0">0</button>
          <button class="key ok" data-act="submit" aria-label="${esc(this.tr("ok"))}">${icon("tick", 30, 'style="stroke-width:2.4"')}</button>
        </div>
        <button class="cancel" data-act="cancel">${icon("close", 20)}<span>${esc(this.tr("cancel"))}</span></button>`;
    }

    _sensorsHtml() {
      const rows = this._rows();
      const canBypass = this._bypassAllowed();
      const list = rows.length
        ? rows.map((r, i) => {
          const status = TEXTS.en["st_" + r.status] ? this.tr("st_" + r.status) : r.status;
          const color = r.status === "open" || r.status === "waiting" ? "#F2B84B" : r.status === "unavailable" ? "#F0605D"
            : r.status === "bypassed" || r.status === "bypassed_at_arm" ? "#8A94A6" : "#4CCB8F";
          const btn = canBypass && r.bypassable
            ? `<button class="small" data-act="${r.status === "bypassed" ? "unbypass" : "bypass"}" data-i="${i}">${esc(this.tr(r.status === "bypassed" ? "unbypass" : "bypass"))}</button>` : "";
          return `<div class="row" style="--s:${color}"><span class="sdot"></span><div class="rt"><div class="rname">${esc(r.name)}</div><div class="rstate">${esc(status)}</div></div>${btn}</div>`;
        }).join("")
        : `<div class="empty">${esc(this.tr("no_sensors"))}</div>`;
      return `<div class="sens-head"><button class="back" data-act="back">${icon("back", 22)}<span>${esc(this.tr("back"))}</span></button>
          <span class="kp-title">${esc(this.tr("sensors"))}</span></div>
        <div class="list">${list}</div>`;
    }

    _click(el, ev) {
      ev.stopPropagation();
      this._touch();
      const act = el.dataset.act;
      if (act === "part") {
        this._ui.partition = el.dataset.id;
        this._armReturn();
        this._ui.view = "main";
        this._ui.force = null;
        this._key = "";
        this._render();
      } else if (act === "arm") this._start("arm_" + el.dataset.mode);
      else if (act === "disarm") this._start("disarm");
      else if (act === "force") this._ui.force && this._start(this._ui.force.action, { force: true });
      else if (act === "sensors") {
        if (this._sensorsVisible()) {
          this._ui.view = "sensors";
          this._render();
        } else this._start("unlock");
      } else if (act === "back") {
        this._ui.view = "main";
        this._ui.unlocked = false; // leaving the list forgets the unlock, like the panel does
        this._render();
      } else if (act === "cancel") this._closeKeypad();
      else if (act === "digit") this._digit(el.dataset.d);
      else if (act === "backspace") this._backspace();
      else if (act === "submit") this._submit();
      else if (act === "bypass" || act === "unbypass") {
        const r = this._rows()[Number(el.dataset.i)];
        if (r) this._start(act, { entity: r.entity, name: r.name });
      }
    }
  }

  const STYLE = `
    :host { display: block; }
    ha-card { display: block; box-sizing: border-box; padding: 16px; container-type: inline-size; user-select: none;
      -webkit-user-select: none; color: var(--primary-text-color, #E8ECF2);
      --surface: var(--secondary-background-color, #151A22); --line: var(--divider-color, #2C3542);
      --muted: var(--secondary-text-color, #8A94A6); }
    ha-card.k-triggered { border: 2px solid var(--c);
      background: color-mix(in srgb, var(--c) 12%, var(--ha-card-background, var(--card-background-color, #0E1116))); }
    button { font: inherit; color: inherit; border: 0; cursor: pointer; touch-action: manipulation; background: none; padding: 0; text-align: left; }
    svg { fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
    .top { display: flex; align-items: center; gap: 10px; min-height: 34px; margin-bottom: 12px; }
    .logo { width: 28px; height: 28px; border-radius: 8px; }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; margin: -4px 0 12px; }
    .chip { display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px; min-height: 40px;
      background: var(--surface); border: 1.5px solid var(--line); font-weight: 600; }
    .chip.on { border-color: var(--c); background: color-mix(in srgb, var(--c) 16%, var(--surface)); }
    .one { display: flex; align-items: center; gap: 8px; margin: -4px 0 12px; font-size: 15px; }
    .one span:last-child { color: var(--muted, #9aa4b2); font-size: 13px; }
    .one .cdot { width: 10px; height: 10px; border-radius: 50%; background: var(--c); }
    .chip small { font-size: 11px; font-weight: 400; opacity: .7; }
    .chip .cdot { width: 10px; height: 10px; border-radius: 50%; background: var(--c); }
    .brand { font-size: 18px; font-weight: 700; }
    .pname { margin-left: auto; font-size: 14px; color: var(--muted); }
    .grid { display: grid; gap: 14px; grid-template-columns: minmax(0, 1fr); }
    .grid.has-keypad .status { display: none; }
    .status { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; text-align: center;
      padding: 26px 16px 24px; border-radius: 26px; background: var(--surface); border: 1px solid var(--line); }
    .ring { width: 150px; height: 150px; }
    .ring-track { stroke: var(--line); stroke-width: 8; }
    .ring-arc { stroke: var(--c); stroke-width: 8; }
    .ring-core { fill: color-mix(in srgb, var(--c) 16%, var(--surface)); stroke: none; }
    .ring-icon { stroke: var(--c); stroke-width: 1.4; }
    .ring-num { fill: var(--primary-text-color, #E8ECF2); stroke: none; font-size: 50px; font-weight: 700; }
    .title { font-size: 30px; font-weight: 800; line-height: 1.15; margin-top: 8px; }
    .s1 { font-size: 17px; font-weight: 600; opacity: .9; }
    .s2 { font-size: 14px; color: var(--muted); }
    .side { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .modes { display: flex; flex-direction: column; gap: 12px; }
    .mode, .sensors { display: flex; align-items: center; gap: 14px; min-height: 72px; padding: 0 18px; border-radius: 22px;
      background: var(--surface); border: 1px solid var(--line); }
    .sensors { min-height: 60px; }
    .dot { display: flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: 50%;
      color: var(--m, var(--c)); background: color-mix(in srgb, var(--m, var(--c)) 18%, var(--surface)); flex: none; }
    .dot.s { width: 38px; height: 38px; --m: var(--muted); }
    .mt { flex: 1; display: flex; flex-direction: column; min-width: 0; }
    .mn { font-size: 20px; font-weight: 800; flex: 1; }
    .mt .mn { flex: none; }
    .ms { font-size: 14px; color: var(--muted); }
    .chev { color: var(--muted); opacity: .7; }
    .badge { min-width: 26px; height: 26px; padding: 0 7px; box-sizing: border-box; border-radius: 13px; background: #F2B84B; color: #2A1D00;
      font-size: 14px; font-weight: 800; display: flex; align-items: center; justify-content: center; }
    .disarm { display: flex; align-items: center; justify-content: center; gap: 12px; min-height: 76px; border-radius: 22px;
      background: #4CCB8F; color: #07251A; font-size: 22px; font-weight: 800; }
    .force { display: flex; align-items: center; justify-content: center; gap: 10px; min-height: 60px; border-radius: 20px;
      border: 2px solid #F2B84B; color: #F2B84B; background: transparent; font-size: 19px; font-weight: 800; }
    .kp-head { display: flex; align-items: center; gap: 14px; }
    .kp-head .dot { color: #4CCB8F; background: color-mix(in srgb, #4CCB8F 18%, var(--surface)); --m: #4CCB8F; }
    .err.bad { color: #F0605D; }
    .dots { display: flex; justify-content: center; align-items: center; gap: 16px; height: 30px; }
    .dots i { width: 14px; height: 14px; box-sizing: border-box; border-radius: 50%; border: 2px solid var(--line); }
    .dots i.on { background: var(--primary-text-color, #E8ECF2); border-color: var(--primary-text-color, #E8ECF2); }
    .keys { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
    .key { display: flex; align-items: center; justify-content: center; min-height: 64px; border-radius: 18px; font-size: 28px;
      font-weight: 600; text-align: center; background: var(--surface); border: 1px solid var(--line); }
    .key.ok { background: #4CCB8F; border-color: #4CCB8F; color: #07251A; } .key.sec { color: var(--muted); }
    .cancel, .back { display: flex; align-items: center; justify-content: center; gap: 8px; min-height: 52px; border-radius: 18px;
      font-size: 17px; font-weight: 600; background: var(--surface); border: 1px solid var(--line); }
    .back { padding: 0 18px; }
    .sens-head { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
    .kp-title { font-size: 22px; font-weight: 800; }
    .list { display: grid; gap: 10px; grid-template-columns: minmax(0, 1fr); max-height: 520px; overflow-y: auto; }
    .row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 20px; background: var(--surface); border: 1px solid var(--line); }
    .sdot { width: 12px; height: 12px; border-radius: 50%; background: var(--s); flex: none; }
    .rt { flex: 1; min-width: 0; } .rname { font-size: 18px; font-weight: 700; } .rstate { font-size: 14px; color: var(--s); }
    .small { min-height: 44px; padding: 0 16px; border-radius: 14px; font-weight: 700; background: var(--line); }
    .empty { padding: 20px; text-align: center; color: var(--muted); }
    @container (min-width: 640px) {
      .grid { grid-template-columns: minmax(0, 1fr) minmax(300px, 380px); align-items: stretch; }
      .grid.has-keypad .status { display: flex; }
      .side .modes { flex: 1; } .side .mode, .side .disarm { flex: 1; }
      .list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .title { font-size: 34px; }
      .ring { width: 180px; height: 180px; }
    }
  `;

  customElements.define("vigil-card", VigilCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "vigil-card",
    name: "Vigil",
    description: "The Vigil alarm for a tablet: state, modes, keypad and sensors, following the profile of the tablet.",
  });
})();
