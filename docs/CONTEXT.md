# Vigil Alarm: overdracht voor een nieuw gesprek

Dit bestand is bedoeld voor een nieuw Claude-gesprek (bijvoorbeeld in VS Code) dat verder werkt aan
dit project. Lees eerst dit bestand, daarna `README.md`, `CHANGELOG.md` en de handleidingen in `docs/`.
Het volledige ontwerp staat in `alarmsysteem-plan-en-functioneel-ontwerp.md` (staat niet in de repo;
vraag de eigenaar om het mee te geven).

## Wat is het
Vigil Alarm (domein `vigil`) is een modulair alarmsysteem als HACS-integratie voor Home Assistant.
Repo: `lightyearcoder/vigil-alarm`, licentie GPL-3.0-or-later, minimaal Home Assistant 2026.2.3.
Eigenaar spreekt Nederlands; antwoord in het Nederlands, code en repo-teksten in het Engels.

- **R1** (nu): volledig alarm binnen Home Assistant. **R2**: Guition-aanraakpaneel (ESPHome). **R3**: veilige terugvalstand.
- De kern beslist en publiceert events; ze roept zelf geen services aan. Alleen meldingen en sirenes zijn ingebouwd.
- Instellen alleen door HA-beheerders, via het eigen zijbalkpaneel (geen standaard HA-formulieren).
- Apparaten worden gekoppeld via rollen, niet via apparaatspecifieke code. Een sensor die `unavailable` wordt is een storing.

## Opbouw
```
custom_components/vigil/
  vigil_core/        pure Python kern, geen HA-afhankelijkheden (statusmodel, sensoren, regels, klok)
  manager.py         koppeling kern <-> HA (timers, persistentie, commando's, build_config)
  items.py           opslag van de onderdelen in entry.options["items"] (zie hieronder)
  editing.py         validatie bij opslaan; panel.py = websocket-API voor het paneel
  frontend/vigil-panel.js   paneel (vanilla web component, nl/en)
  notifier.py, sirens.py, supervisor.py   meldingen, sirenes, zelfbewaking
  presets.py         voorinstelling Sonoff SNZB-09P via Zigbee2MQTT
  migration.py       entry-versie 3; v1->v2 sensorgroepen, v2->v3 subentries -> options
blueprints/automation/vigil/   zes blueprints
examples/dashboard.yaml        voorbeelddashboard
docs/                          handleidingen (en/nl), testplan voor HAOS, testpakket
tests/                         kerntests, scenario's, HA-tests
```

## Belangrijke beslissingen
- **Onderdelen staan in `entry.options["items"]`**, niet als config subentries. HA toont elke subentry op
  Apparaten en diensten; de gebruiker wilde die lijst weg. `Item` houdt de attribuutnamen van een subentry
  (`subentry_id`, `subentry_type`, `title`, `data`) zodat de rest van de code gelijk bleef.
- Opgeslagen typenamen blijven historisch: sensor = `zone`, bevestigingsregel = `group`, sensorgroep = `sensor_group`.
- Bij het verwijderen van een sensor ruimt `_remove_orphans` (`__init__.py`) entiteiten en apparaat op.
- Per sensor een apparaat met statussensor en bypass-schakelaar (geen bypass voor brand en gas).
  Bewust zo gelaten (ook de gebruiker wil geen wijziging nu); apparaten groeperen op soort kan niet in HA's UI.
- Vigil heeft geen eigen MQTT-toegang nodig; alles loopt via HA-entiteiten.
- Geen ZHA- of Hue-preset (gebruiker werkt met Zigbee2MQTT).
- Tags op gebruikers worden opgeslagen maar hebben nog geen functie (komt met de tag-lezer in R2).
- Prioriteit van oorzaken: brand > gas > sabotage > storing > inbraak.

## Tests draaien
Er is een venv nodig met Home Assistant 2026.2.3 en `pytest-homeassistant-custom-component` (0.13.316):
```
python3.13 -m venv .venv && . .venv/bin/activate
pip install homeassistant==2026.2.3 pytest-homeassistant-custom-component==0.13.316 pyyaml
python -m pytest tests -q
```
Stand: 299 tests slagen. Valkuilen: tests met automatiseringen met eindeloze `delay`-lussen hebben een
`_pump` (herhaald `await asyncio.sleep(0)`) nodig; de standaardtijdzone van hass in tests is US/Pacific
(zet UTC voor tijdtriggers); `changed_by` wordt pas bij `armed` gezet.

## Stand van zaken
- Gebouwd en getest: alles tot en met M4 (R1) in de testomgeving.
- **Open**: testrun door de eigenaar op echte HAOS (25 testen in `docs/installatie-en-testen.nl.md`),
  test met echte hardware (SNZB-09P, lamp), GitHub-repo publiceren (workflows `tests.yml` en `hacs.yml`
  hebben nog nooit gedraaid), release `v0.1.0` maken.
- **Later**: apparaten groeperen of samenvoegen (na de testrun beslissen), R2 en R3.

## Werkafspraken
- Wijzigingen altijd met tests, en controleer met een mutatie (breek de code even) dat de test echt faalt.
- Bij elke versie: `version` in `manifest.json` en `pyproject.toml` en een regel in `CHANGELOG.md`.
- Pull requests van anderen worden alleen door de eigenaar samengevoegd; issues zijn welkom (formulieren in `.github/ISSUE_TEMPLATE/`).
