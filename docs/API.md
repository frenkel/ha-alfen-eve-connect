# Alfen Eve – lokale API (bevindingen)

Dit document bevat alles wat uit de officiële Alfen-apps is gehaald. Je hebt de APK's dus niet meer nodig.

- **Eve Connect 1.5.4** (`com.alfen.maple`): de basis van deze integratie. Hieruit komen start/stop (pauzeren), zonnemodus, boost en tijdschema.
- **MyEve 2.3.1** (`com.alfen.myeve`): de volledige lijst met property-namen, de statusteksten en de login- en commando-calls.

Beide apps zijn React Native-apps met Hermes-bytecode (versie 96). Gedecompileerd met `hermes-dec` (`hbc-decompiler`). Alle communicatie verloopt **lokaal** via HTTPS naar de laadpaal; er gaat niets via de cloud of Bluetooth. Eve Connect vindt de laadpaal via mDNS.

## Verbinding

- Basis-URL: `https://<ip-van-laadpaal>`. Het certificaat is self-signed; de apps gebruiken `skipCertificateValidation`.
- Header: `Content-Type: application/json`.
- De sessie loopt via een cookie. In Python/aiohttp heb je daarvoor `CookieJar(unsafe=True)` nodig, omdat de laadpaal op een IP-adres zit.
- Een login is **5 minuten** geldig: Eve Connect gebruikt `isLoginExpired` met 300000 ms. Daarna moet je opnieuw inloggen.
- De laadpaal accepteert **één sessie tegelijk**. Een app en Home Assistant nemen elkaars sessie dus over.

| Methode | Pad | Body | Opmerking |
|---|---|---|---|
| POST | `/api/login` | `{"username": "...", "password": "..."}` | Gebruikersnaam is normaal `admin`. |
| POST | `/api/logout` | `{"username": "...", "password": "..."}` | MyEve stuurt ook `Connection: close` mee. |
| GET | `/api/info` | – | Werkt zonder login; wordt gebruikt als ping. |
| GET | `/api/prop?ids=ID1,ID2,...` | – | Antwoord: `{"properties": [{"id": "2129_0", "value": 16, ...}], "total": n, "version": 2}` |
| GET | `/api/prop?cat=<categorie>` | – | Hele categorie (MyEve). |
| POST | `/api/prop` | `{"ID": {"id": "ID", "value": X}, ...}` | Meerdere properties in één call kan. |
| POST | `/api/cmd` | `{"command": "reboot"}` | Ook `forcefirmwarepermanent`. Eve Connect gebruikt `/api/cmd` **alleen** voor reboot. |
| GET | `/api/transactions?offset=N` | – | Transactielog. De regels hebben tags als `txstart`, `txstart2`, `txstop`, `mv`, `sn`, `rs`, `dto`, `rss` en `se`. Dit zijn **logregels, geen commando's**. |
| GET | `/api/firmware` | – | Firmwarestatus. |
| POST | `/api/password` | `{"password": "..."}` | Wachtwoord wijzigen. |
| POST | `/api/chargingprofiles?add` | profiel (zie hieronder) | |
| POST | `/api/chargingprofiles?clear=<id>` | – | ID in **signed** int32-vorm. HTTP 400 betekent "bestaat niet" en is geen fout. |
| POST | `/api/chargingprofiles?clear=all` | – | |
| GET | `/api/chargingprofiles?id_list` | – | `{"ChargingProfileIDs": [..]}`, eventueel in een envelop. |
| GET | `/api/chargingprofiles?cpid=<id>` | – | `{"version": 2, "profile": {"connectorId": 0, "csChargingProfiles": {...}}}`; `startPeriod`, `limit` en `numberPhases` komen terug als arrays. |

### Property-ID's

- **Op de lijn** gebruik je `XXXX_Y`: het subindex is hex zonder voorloopnul, bijvoorbeeld `2129_0`, `3280_4` en `2221_16`.
- **MyEve** schrijft ze intern met twee cijfers (`2129_00`). Eve Connect gebruikt de vorm op de lijn.
- De volledige lijst met 745 properties staat in [properties.md](properties.md).

## Zonneladen

| Naam in Eve Connect | ID | Waarden |
|---|---|---|
| `SolarChargingMode` | `3280_1` | 0 = Uit, 1 = Comfort, 2 = Green |
| `SolarGreenShare` | `3280_2` | % (0–100) |
| `SolarComfortLevel` | `3280_3` | W (minimaal 2500) |
| `SolarOverrideSocket1` | `3280_4` | 0/1, boost-override socket 1 |
| – | `3280_5` | 0/1, boost-override socket 2 |
| – | `3278_1` / `3278_2` | Override Charging Profile socket 1/2. MyEve-boost zet hier 4294967295 (MAX_UINT32) in. |

Hoe de modi werken, volgens de teksten in de apps:

- **Green, groen aandeel 100%:** laadt alleen als er minstens 1,4 kW zonne-overschot is. Dit is de stand **Zonne-energie** in de integratie.
- **Green, groen aandeel 0%:** laadt altijd minimaal op 1,4 kW.
- **Comfort:** laadt altijd op het comfortniveau. Is er meer zonne-overschot, dan laadt de auto sneller.

Zonneladen is alleen beschikbaar als aan al deze voorwaarden is voldaan (MyEve, `isSolarChargingAvailable`):

- de laadpaal is geen onderdeel van een netwerk (SCN);
- het is een laadpaal met één socket;
- de property `3280_1` bestaat;
- de licentie `LoadBalancing_Active` is aanwezig;
- er is een slimme meter aangesloten.

## Laadprofielen (Eve Connect)

Elk profiel is een OCPP-achtig `csChargingProfiles` met `connectorId: 0` en `chargingProfilePurpose: "ChargingStationExternalConstraints"`. De eenheid is altijd ampère (`"A"`).

| Constante | Signed | Unsigned |
|---|---|---|
| `USER_PAUSE_PROFILE_ID` | -12122008 | 4282845288 |
| `USER_BOOST_PROFILE_ID` | -19571004 | 4275396292 |
| `USER_MAX_POWER_PROFILE_ID` | -19930828 | 4275036468 |
| `UK_DEFAULT_PROFILE_ID` | -19061964 | 4275905332 |
| `USER_PROFILE_MONDAY` … `SUNDAY` | 234202401 … 234202407 | idem |
| `USER_PROFILE_APPLYSCHEDULE` | 234202408 | idem |

Andere constanten: `NOMINAL_PHASE_VOLTAGE` = 230, `MIN_CHARGE_CURRENT` = 6 A, `DEFAULT_NUMBER_OF_PHASES` = 3, `MIN_POWER_PER_PHASE` = 1,4 kW, `MAX_POSSIBLE_POWER` = 22,1 kW, `MIN_COMFORT_LEVEL` = 2500 W, `ACTIVE_PHASE_VOLTAGE_THRESHOLD` = 80 V, `BOOST_ACTIVE_PERIOD` = 10800 s.

### Pauzeren (laden stoppen)

1. `POST /api/prop {"3280_4": {"id": "3280_4", "value": 0}}`
2. `POST /api/chargingprofiles?clear=-19571004` (boost weg)
3. `POST /api/chargingprofiles?add` met:

```json
{"connectorId": 0, "csChargingProfiles": {
  "chargingProfileId": 4282845288, "chargingProfileKind": "Relative",
  "chargingProfilePurpose": "ChargingStationExternalConstraints",
  "stackLevel": 1000, "useLocalTime": true, "useRandomisedDelay": false,
  "chargingSchedule": {"chargingRateUnit": "A",
    "chargingSchedulePeriod": [{"startPeriod": 0, "limit": 0}]}}}
```

### Hervatten (laden starten)

1. `3280_4` = 0
2. `clear=-19571004` (boost)
3. `clear=-12122008` (pauze)

### Boost (3 uur volle snelheid, ook in zonnemodus)

1. `3280_4` = 1
2. `POST /api/chargingprofiles?add` met:

```json
{"connectorId": 0, "csChargingProfiles": {
  "chargingProfileId": 4275396292, "chargingProfileKind": "Absolute",
  "chargingProfilePurpose": "ChargingStationExternalConstraints",
  "stackLevel": 1000, "useRandomisedDelay": false,
  "chargingSchedule": {"startSchedule": "<nu, ISO-8601>", "chargingRateUnit": "A",
    "duration": 10800,
    "chargingSchedulePeriod": [{"startPeriod": 0, "limit": <A>, "numberPhases": 3}]}}}
```

### Maximaal vermogen (gebruikerslimiet)

`chargingProfileId` 4275036468, `Relative`, `stackLevel` 0, `useLocalTime` true. Er is één periode `{"startPeriod": 0, "limit": <A>, "numberPhases": <n>}`.

### Tijdschema

Per weekdag is er één **wekelijks terugkerend** profiel:

```json
{"connectorId": 0, "csChargingProfiles": {
  "chargingProfileId": 234202400 + dag,          // 1 = maandag … 7 = zondag
  "chargingProfileKind": "Recurring", "recurrencyKind": "Weekly",
  "chargingProfilePurpose": "ChargingStationExternalConstraints",
  "stackLevel": 11 - dag,                          // maandag 10 … zondag 4
  "useLocalTime": true, "useRandomisedDelay": false,
  "chargingSchedule": {
    "chargingRateUnit": "A",
    "startSchedule": "2024-04-<dag> (lokale middernacht, ISO)",   // 1 april 2024 = maandag
    "duration": 86400 als het schema actief is, anders 0,
    "chargingSchedulePeriod": [
      {"startPeriod": <slot.start s>, "limit": <A>, "numberPhases": <n>},
      {"startPeriod": <slot.end s of 1>, "limit": 0, "numberPhases": <n>},
      ...]}}}
```

Zo werkt het schema:

- **Tijdvakken** hebben de vorm `{start, end, maxPower}`. `start` en `end` zijn seconden sinds middernacht (0–86400) en `maxPower` is in kW.
- **Elk vak** levert twee periodes op: vanaf `start` geldt de limiet, en vanaf `end` geldt limiet 0.
- **Middernacht:** begint er geen vak om 0 s, dan voegt de app `{start: 0, maxPower: 0, end: 0}` toe en sorteert de vakken opnieuw.
- **Van kW naar ampère:** `A = round(kW*1000/230)`, gedeeld door het aantal actieve fasen. Komt dat onder 6 A uit, dan gebruikt de app de totale ampère op één fase (`numberPhases` = `MIN_PHASE_REQUIRED`, vermoedelijk 1).
- **Dag zonder vakken:** het profiel van die dag wordt gewist (`clear=<dag-id>`).
- **Schema aan/uit:**
  - Aan: `add` van `USER_PROFILE_APPLYSCHEDULE` (234202408). Dat is `Relative`, `stackLevel` 1, met periodes `[{0, limit 0, 3 fasen}, {1, limit 0, 3 fasen}]`. Daarna stuurt de app alle dagprofielen opnieuw met `duration` 86400.
  - Uit: `clear=234202408`, en de dagprofielen gaan terug naar `duration` 0.

## Statuscodes `2501_1` (Socket 1 – Mainstate)

Teksten uit MyEve (`MainStateDescriptors`). Niet alle codes hebben een tekst in de app. De lijst is mogelijk niet compleet.

| Code | Tekst |
|---|---|
| 4 | Authorization TimeOut |
| 6 | Button Pushed |
| 7 | Card Presented |
| 9 | Wait on Vehicle |
| 11 | Charging Stopped |
| 12 | Waiting for power |
| 13 | Start Charging |
| 16 | Vehicle not Connected |
| 18 | Restart Charging |
| 19 | Disconnect Cable |
| 20 | Present Card |
| 21 | Restart after Outage |
| 24 | Cable not Supported |
| 25 | Illegal Charge mode |
| 26 | Too many retries |
| 29 | HighFrequent Switching |
| 31 | Protective Earth |
| 32 | Relays Errors |
| 33 | Power Failure |
| 34 | Internal Voltage Error |
| 35 | Power Meter Error |
| 36 | Temperature Error |
| 40 | RCD Error |
| 41 | Charging Suspended |
| 43 | Changing Phase |
| 44 | Wait for Start Value |
| 45 | Wait for Stop Value |
| 46 | Socket Motor Error |
| 47–52 | Schuko-statussen |
| 53 | Invalid Card |

Let op: de app-teksten kunnen bij een andere nummering horen (hex of decimaal). Controleer dit tegen een echte laadpaal.

## Overige nuttige properties

| ID | Naam |
|---|---|
| `2129_0` | Socket 1 – Max current (A) |
| `2062_0` | Station maximum current (A) |
| `2221_16` | Socket 1 – Power Real Sum. In de demo-data van Eve Connect staat 1731.45, dus waarschijnlijk W, hoewel MyEve "kW" zegt. |
| `2221_22` | Socket 1 – Energy Delivered Sum. Demo-data 62100, dus waarschijnlijk Wh. |
| `2221_3..5` | Spanning L1–L3 (V) |
| `2221_A..C` | Stroom L1–L3 (A) |
| `2126_0` | Authorization mode |
| `2185_0` | Allow 1- and 3-phased charging (`PhaseSwitchingEnabled`) |
| `2600_0` | Auto Charge – Enabled |
| `216C_0` | Direct external suspend signal |
| `21B2_0` | SSA Enabled |
| `2059_0` | Datum/tijd laadpaal (ms) |
| `206E_0` | Tijdzone |
| `2054_0` | Firmwareversie |
| `2051_0` | Serienummer / ACE-id |
