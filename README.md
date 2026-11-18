# Alfen Eve Connect – Home Assistant-integratie

Bedien een **Alfen Eve**-laadpaal vanuit Home Assistant via je **lokale netwerk**, zonder cloud en zonder Bluetooth.
De integratie gebruikt dezelfde lokale HTTPS-API als de officiële apps MyEve en Eve Connect.

## Wat je krijgt

| Entiteit | Wat het doet |
|---|---|
| **Laden** (schakelaar) | Uit = laden pauzeren, aan = laden hervatten. Werkt net als de pauzeknop in Eve Connect: de laadpaal krijgt een laadprofiel van 0 A. |
| **Laadmodus** (keuzelijst) | **Normaal (max snelheid)**: zonneladen staat uit en de auto laadt op de ingestelde maximale stroom. **Zonne-energie**: modus *Green* met 100% groen aandeel. De auto laadt dan alleen op overtollige zonnestroom, zonder de minimale 1,4 kW uit het net die *Comfort* zou gebruiken. |
| Vermogen, Geleverde energie | Actueel laadvermogen en de totale meterstand. |
| Maximale stroom, Groen aandeel, Statuscode | Diagnose-informatie. |

Staat de laadpaal in een andere stand, bijvoorbeeld Comfort of een groen aandeel onder 100% ingesteld via de app? Dan toont de keuzelijst geen waarde, tot je zelf een stand kiest.

## Installatie

### Via HACS (aanbevolen)

1. Open in Home Assistant **HACS**, klik rechtsboven op de drie puntjes en kies **Custom repositories**.
2. Plak `https://github.com/frenkel/ha-alfen-eve-connect`, kies type **Integration** en klik op **Add**.
3. Zoek in HACS op **Alfen Eve Connect**, klik op **Download** en herstart Home Assistant.
4. Ga verder bij stap 3 hieronder.

### Handmatig

1. Kopieer de map `custom_components/alfen_eve_connect` naar de map `config/custom_components/` van je Home Assistant. Gebruik daarvoor bijvoorbeeld de add-on *File editor* of *Samba share*.
2. Herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen** en zoek op **Alfen Eve Connect**.
4. Vul in:
   - **Host / IP-adres**: het IP-adres van de laadpaal in je netwerk. Dat vind je in je router of in de MyEve-app. Geef de laadpaal bij voorkeur een vast IP-adres in je router.
   - **Gebruikersnaam**: meestal `admin`.
   - **Wachtwoord**: hetzelfde wachtwoord dat je in de MyEve-app gebruikt om lokaal met de laadpaal te verbinden.

## Belangrijk om te weten

- **Er kan maar één verbinding tegelijk zijn.** De laadpaal accepteert één ingelogde gebruiker. Open je de MyEve- of Eve Connect-app terwijl Home Assistant verbonden is, dan nemen ze elkaars sessie over. De integratie logt daarna vanzelf opnieuw in, maar in de app kun je een melding krijgen.
- **Zonneladen vereist een slimme meter** (P1 of Modbus) die op de laadpaal is aangesloten, en de licentie voor Active Load Balancing. Zonder die twee kan de laadpaal niet weten hoeveel zonnestroom er over is.
- Het pauzeprofiel blijft op de laadpaal staan tot je **Laden** weer aanzet, ook na een herstart van Home Assistant.

## Herkomst van de API

De endpoints en property-ID's komen uit de apps MyEve 2.3.1 en Eve Connect 1.5.4:

- `POST /api/login` met `{"username", "password"}`
- `GET /api/prop?ids=…` en `POST /api/prop` met `{"ID": {"id": "ID", "value": …}}`
- Zonneladen: `3280_1` (modus 0/1/2 = uit/comfort/green), `3280_2` (groen aandeel %), `3280_3` (comfortniveau W), `3280_4` (override/boost socket 1)
- Pauzeren: `POST /api/chargingprofiles?add` met profiel-ID 4282845288 (limiet 0 A). Hervatten: `POST /api/chargingprofiles?clear=-12122008`.

Alle bevindingen staan in [docs/API.md](docs/API.md), inclusief boost, tijdschema en statuscodes. De volledige lijst met properties staat in [docs/properties.md](docs/properties.md).

Dit project staat los van Alfen en is geen officieel product van Alfen.
