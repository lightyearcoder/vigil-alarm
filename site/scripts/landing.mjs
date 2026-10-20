// The front page of the site, one per language, built from the texts below.
const T = {
  en: {
    description: "A modular alarm system for Home Assistant: partitions, panels, tablets and a clear log.",
    tagline: "A modular alarm system for Home Assistant: partitions, panels, tablets and a clear log.",
    guide: "Read the user guide", install: "Install and test",
    features: "What Vigil does",
    cards: [
      ["Partitions", "Split the house into areas (house, garage, shed) that arm and trigger on their own, with their own sensors, codes and sirens."],
      ["Panels everywhere", "An ESPHome touch panel on the wall, a tablet or a phone with the Vigil card, or the admin panel in Home Assistant. Each panel sees only what it may."],
      ["A clear log", "Who armed, who disarmed, what triggered, from which panel, and the alarm memory of the last alarm, kept across restarts."],
      ["Honest about failure", "What Vigil does when Home Assistant restarts, a sensor drops out or a siren does not answer is written down and tested."],
    ],
    start: "Where to start",
    links: [
      ["user-guide", "User guide", "Arm, disarm, codes, sensors, the log."],
      ["tablet", "Tablet as keypad", "A tablet on the wall with the Vigil card."],
      ["installation-and-testing", "Install and test", "Install on Home Assistant OS and test it."],
      ["esphome-panel", "ESPHome touch panel", "Build and flash the wall panel."],
      ["failure-behaviour", "When something goes wrong", "What Vigil does, and what it cannot do."],
      ["troubleshooting", "Troubleshooting", "My alarm does not do what I expect."],
    ],
    shot: "The touch panel in its states",
  },
  nl: {
    description: "Een modulair alarmsysteem voor Home Assistant: partities, panelen, tablets en een duidelijk logboek.",
    tagline: "Een modulair alarmsysteem voor Home Assistant: partities, panelen, tablets en een duidelijk logboek.",
    guide: "Lees de handleiding", install: "Installeren en testen",
    features: "Wat Vigil doet",
    cards: [
      ["Partities", "Verdeel het huis in gebieden (huis, garage, schuur) die zelfstandig inschakelen en afgaan, met eigen sensoren, codes en sirenes."],
      ["Panelen overal", "Een ESPHome-touchpaneel aan de muur, een tablet of telefoon met de Vigil-kaart, of het beheerpaneel in Home Assistant. Elk paneel ziet alleen wat het mag."],
      ["Een duidelijk logboek", "Wie schakelde in, wie uit, wat ging af, vanaf welk paneel, en het alarmgeheugen van het laatste alarm, ook na een herstart."],
      ["Eerlijk over storingen", "Wat Vigil doet als Home Assistant herstart, een sensor wegvalt of een sirene niet antwoordt, staat beschreven en is getest."],
    ],
    start: "Waar te beginnen",
    links: [
      ["user-guide", "Handleiding", "In- en uitschakelen, codes, sensoren, het logboek."],
      ["tablet", "Tablet als bediening", "Een tablet aan de muur met de Vigil-kaart."],
      ["installation-and-testing", "Installeren en testen", "Installeren op Home Assistant OS en testen (Engels)."],
      ["esphome-panel", "ESPHome-touchpaneel", "Het wandpaneel bouwen en flashen (Engels)."],
      ["failure-behaviour", "Als er iets misgaat", "Wat Vigil doet, en wat niet kan."],
      ["troubleshooting", "Problemen oplossen", "Mijn alarm doet niet wat ik verwacht."],
    ],
    shot: "Het touchpaneel in zijn toestanden",
  },
  de: {
    description: "Ein modulares Alarmsystem für Home Assistant: Bereiche, Bedienteile, Tablets und ein klares Protokoll.",
    tagline: "Ein modulares Alarmsystem für Home Assistant: Bereiche, Bedienteile, Tablets und ein klares Protokoll.",
    guide: "Zur Anleitung", install: "Installieren und testen",
    features: "Was Vigil kann",
    cards: [
      ["Partitionen", "Teile das Haus in Bereiche (Haus, Garage, Schuppen), die eigenständig scharf werden und auslösen, mit eigenen Sensoren, Codes und Sirenen."],
      ["Bedienteile überall", "Ein ESPHome-Touchpanel an der Wand, ein Tablet oder Handy mit der Vigil-Karte oder das Verwaltungspanel in Home Assistant. Jedes Bedienteil sieht nur, was es darf."],
      ["Ein klares Protokoll", "Wer hat scharf oder unscharf geschaltet, was hat ausgelöst, von welchem Bedienteil, dazu der Alarmspeicher des letzten Alarms, auch nach einem Neustart."],
      ["Ehrlich bei Störungen", "Was Vigil tut, wenn Home Assistant neu startet, ein Sensor ausfällt oder eine Sirene nicht antwortet, ist beschrieben und getestet."],
    ],
    start: "Wo anfangen",
    links: [
      ["user-guide", "Anleitung", "Scharf- und Unscharfschalten, Codes, Sensoren, das Protokoll."],
      ["tablet", "Tablet als Bedienteil", "Ein Tablet an der Wand mit der Vigil-Karte."],
      ["installation-and-testing", "Installieren und testen", "Installation auf Home Assistant OS und Test (Englisch)."],
      ["esphome-panel", "ESPHome-Touchpanel", "Das Wandpanel bauen und flashen (Englisch)."],
      ["failure-behaviour", "Wenn etwas schiefgeht", "Was Vigil tut und was nicht möglich ist."],
      ["troubleshooting", "Fehlersuche", "Mein Alarm tut nicht, was ich erwarte."],
    ],
    shot: "Das Touchpanel in seinen Zuständen",
  },
  fr: {
    description: "Un système d'alarme modulaire pour Home Assistant : zones, claviers, tablettes et un journal clair.",
    tagline: "Un système d'alarme modulaire pour Home Assistant : zones, claviers, tablettes et un journal clair.",
    guide: "Lire le guide", install: "Installer et tester",
    features: "Ce que fait Vigil",
    cards: [
      ["Partitions", "Divisez la maison en zones (maison, garage, abri) qui s'arment et se déclenchent seules, avec leurs propres capteurs, codes et sirènes."],
      ["Des claviers partout", "Un écran tactile ESPHome au mur, une tablette ou un téléphone avec la carte Vigil, ou le panneau d'administration dans Home Assistant. Chaque clavier ne voit que ce qui lui est permis."],
      ["Un journal clair", "Qui a armé, qui a désarmé, ce qui s'est déclenché, depuis quel clavier, et la mémoire d'alarme de la dernière alarme, même après un redémarrage."],
      ["Honnête sur les pannes", "Ce que fait Vigil quand Home Assistant redémarre, qu'un capteur tombe ou qu'une sirène ne répond pas est décrit et testé."],
    ],
    start: "Par où commencer",
    links: [
      ["user-guide", "Guide d'utilisation", "Armer, désarmer, codes, capteurs, le journal."],
      ["tablet", "Tablette comme clavier", "Une tablette au mur avec la carte Vigil."],
      ["installation-and-testing", "Installer et tester", "Installation sur Home Assistant OS et test (en anglais)."],
      ["esphome-panel", "Écran tactile ESPHome", "Construire et flasher le panneau mural (en anglais)."],
      ["failure-behaviour", "Quand quelque chose tourne mal", "Ce que fait Vigil, et ce qu'il ne peut pas faire."],
      ["troubleshooting", "Dépannage", "Mon alarme ne fait pas ce que j'attends."],
    ],
    shot: "L'écran tactile dans ses états",
  },
  it: {
    description: "Un sistema d'allarme modulare per Home Assistant: zone, pannelli, tablet e un registro chiaro.",
    tagline: "Un sistema d'allarme modulare per Home Assistant: zone, pannelli, tablet e un registro chiaro.",
    guide: "Leggi la guida", install: "Installare e provare",
    features: "Cosa fa Vigil",
    cards: [
      ["Partizioni", "Dividi la casa in zone (casa, garage, capanno) che si inseriscono e scattano da sole, con sensori, codici e sirene propri."],
      ["Pannelli ovunque", "Un touch panel ESPHome a parete, un tablet o un telefono con la scheda Vigil, oppure il pannello di amministrazione in Home Assistant. Ogni pannello vede solo ciò che gli è permesso."],
      ["Un registro chiaro", "Chi ha inserito, chi ha disinserito, cosa è scattato, da quale pannello, e la memoria dell'ultimo allarme, anche dopo un riavvio."],
      ["Onesto sui guasti", "Cosa fa Vigil quando Home Assistant si riavvia, un sensore cade o una sirena non risponde è descritto e provato."],
    ],
    start: "Da dove cominciare",
    links: [
      ["user-guide", "Guida per l'utente", "Inserire, disinserire, codici, sensori, il registro."],
      ["tablet", "Tablet come tastiera", "Un tablet a parete con la scheda Vigil."],
      ["installation-and-testing", "Installare e provare", "Installazione su Home Assistant OS e prova (in inglese)."],
      ["esphome-panel", "Touch panel ESPHome", "Costruire e flashare il pannello a parete (in inglese)."],
      ["failure-behaviour", "Quando qualcosa va storto", "Cosa fa Vigil e cosa non può fare."],
      ["troubleshooting", "Risoluzione dei problemi", "Il mio allarme non fa ciò che mi aspetto."],
    ],
    shot: "Il touch panel nei suoi stati",
  },
  es: {
    description: "Un sistema de alarma modular para Home Assistant: zonas, paneles, tabletas y un registro claro.",
    tagline: "Un sistema de alarma modular para Home Assistant: zonas, paneles, tabletas y un registro claro.",
    guide: "Leer la guía", install: "Instalar y probar",
    features: "Qué hace Vigil",
    cards: [
      ["Particiones", "Divide la casa en zonas (casa, garaje, cobertizo) que se activan y saltan por separado, con sus propios sensores, códigos y sirenas."],
      ["Paneles en todas partes", "Un panel táctil ESPHome en la pared, una tableta o un móvil con la tarjeta Vigil, o el panel de administración en Home Assistant. Cada panel ve solo lo que puede."],
      ["Un registro claro", "Quién activó, quién desactivó, qué saltó, desde qué panel, y la memoria de la última alarma, también tras un reinicio."],
      ["Honesto ante los fallos", "Lo que hace Vigil cuando Home Assistant se reinicia, un sensor se cae o una sirena no responde está descrito y probado."],
    ],
    start: "Por dónde empezar",
    links: [
      ["user-guide", "Guía de usuario", "Activar, desactivar, códigos, sensores, el registro."],
      ["tablet", "Tableta como teclado", "Una tableta en la pared con la tarjeta Vigil."],
      ["installation-and-testing", "Instalar y probar", "Instalación en Home Assistant OS y prueba (en inglés)."],
      ["esphome-panel", "Panel táctil ESPHome", "Construir y flashear el panel de pared (en inglés)."],
      ["failure-behaviour", "Cuando algo sale mal", "Qué hace Vigil y qué no puede hacer."],
      ["troubleshooting", "Solución de problemas", "Mi alarma no hace lo que espero."],
    ],
    shot: "El panel táctil en sus estados",
  },
};

const q = (s) => JSON.stringify(s);

export function landing(lang, base) {
  const t = T[lang];
  const pre = `${base}/${lang === "en" ? "" : lang + "/"}`;
  // esphome-panel, installation-and-testing and the changelog exist in English only for most languages
  const page = (name) => (name === "esphome-panel" || (name === "installation-and-testing" && lang !== "nl"))
    ? `${base}/${name}/` : `${pre}${name}/`;
  const logo = lang === "en" ? "../../assets/logo.png" : "../../../assets/logo.png";
  const image = `${base}/images/touch-panel-states-${lang}.png`;
  return `---
title: "Vigil Alarm"
description: ${q(t.description)}
template: splash
hero:
  tagline: ${q(t.tagline)}
  image:
    file: ${logo}
  actions:
    - text: ${q(t.guide)}
      link: ${pre}user-guide/
      icon: right-arrow
    - text: ${q(t.install)}
      link: ${page("installation-and-testing")}
      variant: minimal
---

import { Card, CardGrid, LinkCard } from "@astrojs/starlight/components";

## ${t.features}

<CardGrid>
${t.cards.map(([title, text], i) => `  <Card title=${q(title)} icon=${q(["puzzle", "laptop", "list-format", "approve-check"][i])}>${text}</Card>`).join("\n")}
</CardGrid>

<img src=${q(image)} alt=${q(t.shot)} style="display:block;margin:2rem auto;max-width:100%;border-radius:12px" />

## ${t.start}

<CardGrid>
${t.links.map(([name, title, text]) => `  <LinkCard title=${q(title)} description=${q(text)} href=${q(page(name))} />`).join("\n")}
</CardGrid>
`;
}
