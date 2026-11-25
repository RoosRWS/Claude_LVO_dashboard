"""Centrale configuratie voor het LVO-dashboard (kleuren, paden, KI-kolommen)."""

from pathlib import Path  # Pad-object voor platformonafhankelijke paden

# ---------------------------------------------------------------- soort beoordeling
# "3_klassen": matig / gemiddeld / goed                      (grenzen uit data/Grenzen_3.csv)
# "sterren":   0 tot 5 sterren                              (grenzen uit data/Grenzen_5.csv)
# Na het wisselen: python scripts/run_pipeline.py (de pipeline ziet dat config.py veranderd is)
BEOORDELING = "3_klassen"

# ---------------------------------------------------------------- paden
BASIS_MAP = Path(__file__).resolve().parent  # Map waarin dit bestand staat
DATA_MAP = BASIS_MAP / "data"  # Map met de ruwe shapefiles
VERWERKT_MAP = DATA_MAP / "processed"  # Map voor de voorbewerkte parquet-bestanden

# Ruwe bronbestanden
SHP_BRES = DATA_MAP / "resultaten_bres.shp"  # Scenario's per breslocatie
KANSEN_PRIMAIR_2019 = DATA_MAP / "overstromingskansen_actueel_2019_faalkans_primair.gpkg"  # Primaire trajecten (download via WFS)
KANSEN_PRIMAIR_LIMBURG = DATA_MAP / "overstromingskansen_actueel_2025_faalkans_primair_limburg.gpkg"  # Limburg (download via WFS)
KANSEN_NIET_PRIMAIR = DATA_MAP / "overstromingskansen_actueel_faalkans_niet_primair.gpkg"  # Regionale keringen (download via WFS)

# Invoer van het kwaliteitsscript (scripts/00_kwaliteit_per_scenario.py)
XLSX_METADATA_INFO = DATA_MAP / "metadata_info.xlsx"  # Welke metadatakolommen verplicht/optioneel zijn
XLSX_BODEMHOOGTE = DATA_MAP / "Bodemhoogte.xlsx"  # Sterren per bodemhoogtemodel
XLSX_SOFTWARE = DATA_MAP / "Software.xlsx"  # Sterren per modelleersoftware
# Klassegrenzen per indicator: welk bestand hangt af van de soort beoordeling
CSV_GRENZEN = DATA_MAP / ("Grenzen_3.csv" if BEOORDELING == "3_klassen" else "Grenzen_5.csv")
# Opvulwaarden in de LIWO-metadata die als "leeg" tellen bij de KI metadata (naast echt lege cellen)
METADATA_LEEG_TEKST = ["", "-"]  # Tekst (na weghalen van spaties); alleen spaties telt dus ook als leeg
METADATA_LEEG_GETAL = [-999, -9999]  # Codes voor "geen waarde"

# Download van de overstromingskansen via de WFS van LIWO (scripts/00a_download_overstromingskansen.py)
WFS_BASIS = "https://basisinformatie-overstromingen.nl/geoserver/LIWO_Basis/wfs"  # WFS-adres
WFS_KANSEN = {  # WFS-laagnaam -> lokaal GeoPackage-bestand
    "LIWO_Basis:overstromingskansen_actueel_2019_faalkans_primair": KANSEN_PRIMAIR_2019,  # Primair 2019
    "LIWO_Basis:overstromingskansen_actueel_2025_faalkans_primair_Limburg": KANSEN_PRIMAIR_LIMBURG,  # Limburg (hoofdletter L)
    "LIWO_Basis:overstromingskansen_actueel_faalkans_niet_primair": KANSEN_NIET_PRIMAIR,  # Niet-primair
}

# Pipeline (scripts/run_pipeline.py)
MAX_LEEFTIJD_DAGEN = 30  # Kwaliteitsstap opnieuw draaien als de uitvoer ouder is (leeftijd-KI hangt af van vandaag)

# Voorbewerkte uitvoerbestanden
SCENARIOS_BESTAND = VERWERKT_MAP / "scenarios.parquet"  # Tabel met alle scenario's
BRESLOCATIES_BESTAND = VERWERKT_MAP / "breslocaties.parquet"  # Unieke breslocaties (punten)
TRAJECTEN_BESTAND = VERWERKT_MAP / "trajecten_primair.parquet"  # Primaire trajecten (lijnen)
KERINGEN_BESTAND = VERWERKT_MAP / "keringen_niet_primair.parquet"  # Niet-primaire keringen (lijnen)

# Kopieën om zelf te controleren (in Excel te openen); worden bij elke run overschreven
CONTROLE_MAP = BASIS_MAP / "temp"
SCENARIOS_EXCEL = CONTROLE_MAP / "scenarios.xlsx"  # Zelfde inhoud als SCENARIOS_BESTAND

# ---------------------------------------------------------------- coördinaten
CRS_RD = "EPSG:28992"  # Rijksdriehoekstelsel (bronbestanden)
CRS_WGS84 = "EPSG:4326"  # WGS84 (folium/leaflet)

# ---------------------------------------------------------------- RWS-kleuren
KLEUREN = {
    "lintblauw": "#154273",  # Header
    "donkerblauw": "#01689B",  # Accenten en knoppen
    "hemelblauw": "#007BC7",  # Links en hover
    "geel": "#F9E11E",  # Sterren en mock-badge
    "lichtgrijs": "#F3F3F3",  # Achtergrond van panelen
    "tekst": "#000000",  # Hoofdtekst
    "tekst_grijs": "#535353",  # Secundaire tekst
}

# ---------------------------------------------------------------- sterren (KI = kwaliteitsindicator)
MAX_STERREN = 5  # Maximaal aantal sterren

# Per KI: kolomnaam in scenarios.parquet en het label voor in de UI
# Alleen deze indicatoren worden in het dashboard getoond (en tellen mee in de totaalscore).
# Bodemhoogte en software worden nog wel berekend, maar staan hier (nu) niet in.
KI_KOLOMMEN = {
    "ki_metadata": "Metadata",
    "ki_leeftijd": "Leeftijd scenario",
    "ki_resolutie": "Resolutie",
    "ki_frequentie": "Spreiding herhalingstijd",
}
# Niet tonen in de scenariotabel van het overzicht per breslocatie: deze is voor alle scenario's op een locatie gelijk
KI_NIET_IN_OVERZICHTTABEL = ["ki_frequentie"]
# Bij sterren is er (nog) geen grens voor de herhalingstijd in Grenzen_5.csv: dan niet tonen
if BEOORDELING == "sterren":
    del KI_KOLOMMEN["ki_frequentie"]

# ---------------------------------------------------------------- kolomnamen bres-shapefile
# Mapping van de afgekapte shapefile-namen naar leesbare namen
BRES_KOLOMMEN = {
    "Scenario": "scenario_id",  # Uniek scenario-ID
    "Scenarioda": "scenario_datum",  # Datum van het scenario
    "Naam buite": "buitenwater",  # Naam buitenwater
    "Naam doorb": "naam",  # Naam doorbraaklocatie
    "Gebiedsnaa": "gebied",  # Dijkring/gebied
    "Duur": "duur",  # Duur van de berekening
    "Bodemhoogt": "bodemhoogte",  # Gebruikt bodemhoogtemodel
    "Modelleers": "software",  # Gebruikte software
    "X (RD_new)": "x_rd",  # X-coördinaat in RD
    "Y (RD_new)": "y_rd",  # Y-coördinaat in RD
    "KI_metadat": "ki_metadata",  # Sterren metadata
    "aantal_ban": "aantal_banden",  # Aantal rasterbanden (geen score)
    "Leeftijd": "leeftijd",  # Leeftijd scenario in jaren
    "KI_leeftij": "ki_leeftijd",  # Sterren leeftijd
    "KI_bodemho": "ki_bodemhoogte",  # Sterren bodemhoogte
    "KI_softwar": "ki_software",  # Sterren software
    "KI_resolut": "ki_resolutie",  # Sterren resolutie
    "KI_frequen": "ki_frequentie",  # Sterren herhalingstijd
    "Factor_her": "factor_herhalingstijd",  # Hoogste / laagste herhalingstijd op de breslocatie
}

# ---------------------------------------------------------------- vereenvoudiging (meters, in RD)
SIMPLIFY_TRAJECTEN = 5  # Tolerantie primaire trajecten
SIMPLIFY_KERINGEN = 10  # Tolerantie niet-primaire keringen (12k lijnen)

# ---------------------------------------------------------------- kaartlagen
# Per laag: label, bestand, kolom met het item-ID en kolom met de weergavenaam
LAGEN = {
    "breslocaties": {"label": "Breslocaties", "bestand": BRESLOCATIES_BESTAND, "id": "locatie_id", "naam": "naam"},
    "trajecten": {"label": "Primaire dijktrajecten", "bestand": TRAJECTEN_BESTAND, "id": "traject_id", "naam": "traject_id"},
    "keringen": {"label": "Niet-primaire keringen", "bestand": KERINGEN_BESTAND, "id": "kering_id", "naam": "naam"},
}

# ---------------------------------------------------------------- achtergrondkaarten (PDOK BRT)
ACHTERGRONDEN = {
    "Grijs": "grijs",  # Rustige grijze kaart
    "Standaard": "standaard",  # Standaard BRT-kaart
    "Pastel": "pastel",  # Pastelkleuren
}
PDOK_URL = "https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/{laag}/EPSG:3857/{{z}}/{{x}}/{{y}}.png"  # WMTS-sjabloon
KAART_CENTRUM = (52.15, 5.3)  # Midden van Nederland
KAART_ZOOM = 8  # Startzoom

# ---------------------------------------------------------------- scoreklassen (rood = laag, groen = hoog)
# Ondergrens telt mee in de klasse; bij de laatste klasse telt ook de bovengrens mee
SCORE_KLASSEN_STERREN = [
    {"van": 0, "tot": 1, "label": "0 tot 1 ster", "kleur": "#D7191C"},  # Rood
    {"van": 1, "tot": 2, "label": "1 tot 2 sterren", "kleur": "#FDAE61"},  # Oranje
    {"van": 2, "tot": 3, "label": "2 tot 3 sterren", "kleur": "#FFE066"},  # Geel
    {"van": 3, "tot": 4, "label": "3 tot 4 sterren", "kleur": "#A6D96A"},  # Lichtgroen
    {"van": 4, "tot": 5, "label": "4 tot 5 sterren", "kleur": "#1A9641"},  # Groen
]
# Bij 3 klassen wordt een gemiddelde afgerond: onder 1,5 = matig, vanaf 2,5 = goed
SCORE_KLASSEN_3 = [
    {"van": 0, "tot": 1.5, "label": "Matig", "kleur": "#EE9A8A"},  # Zacht rood
    {"van": 1.5, "tot": 2.5, "label": "Gemiddeld", "kleur": "#F6DC85"},  # Zacht geel
    {"van": 2.5, "tot": 3, "label": "Goed", "kleur": "#93CC98"},  # Zacht groen
]
SCORE_KLASSEN = SCORE_KLASSEN_3 if BEOORDELING == "3_klassen" else SCORE_KLASSEN_STERREN

# ---------------------------------------------------------------- prestaties
COORD_PRECISIE = 1e-5  # Afronden van coördinaten in graden (~1 m)
ZOOM_LAGEN_PAS_VANAF = {"keringen": 11}  # Laag pas getekend vanaf dit zoomniveau, en dan alleen wat in beeld is

# ---------------------------------------------------------------- waterdiepte-kaartje (WMS van LIWO)
XLSX_METADATA = DATA_MAP / "metadata_LIWO.xlsx"  # Bevat per scenario de werkruimte (hulp) en de kaartuitsnede (RD)
WMS_BASIS = "https://basisinformatie-overstromingen.nl/geoserver"  # {werkruimte}/scenario_{id}/wms

# ---------------------------------------------------------------- uitleg per indicator (i-knop in het dashboard)
# LET OP: deze teksten zijn afgeleid uit de data van resultaten_bres.shp en dus nog niet bevestigd.
# Controleer ze en pas ze aan; zet daarna INDICATOR_INFO_CONCEPT op False om de concept-melding te verbergen.
INDICATOR_INFO_CONCEPT = False  # Toon "concept" bij de uitleg zolang de teksten niet bevestigd zijn

# Uitleg bij 3 klassen. Getal = klasse: 3 = goed, 2 = gemiddeld, 1 = matig, 0 = onbekend
INDICATOR_INFO_3 = {
    "ki_metadata": {
        "wat": ("Welk deel van de verplichte metadatavelden in LIWO is ingevuld. "
                "Opvulwaarden (alleen een spatie, '-', -999 of -9999) tellen als leeg."),
        "schaal": [
            ("3", "85% of meer van de verplichte velden ingevuld"),
            ("2", "55 tot 85%"),
            ("1", "Minder dan 55%"),
        ],
    },
    "ki_leeftijd": {
        "wat": "De leeftijd van het scenario: het aantal jaren sinds de scenariodatum.",
        "schaal": [
            ("3", "Maximaal 10 jaar oud"),
            ("2", "11 tot en met 20 jaar"),
            ("1", "Ouder dan 20 jaar"),
            ("0", "Leeftijd onbekend"),
        ],
    },
    "ki_resolutie": {
        "wat": ("De rekenresolutie van het model (grootte van een rekencel), uit de LIWO-metadata. "
                "Let op: deze waarde klopt niet altijd met het gepubliceerde raster."),
        "schaal": [
            ("3", "10 meter of fijner"),
            ("2", "Fijner dan of gelijk aan 25 meter"),
            ("1", "Grover dan 25 meter"),
            ("0", "Resolutie onbekend"),
        ],
    },
    "ki_frequentie": {
        "wat": ("Spreiding van de herhalingstijden op deze breslocatie: de hoogste herhalingstijd gedeeld door "
                "de laagste (bijv. 10.000 en 100 jaar = factor 100). Meer spreiding is beter. "
                "Alle scenario's op dezelfde breslocatie krijgen dezelfde beoordeling."),
        "schaal": [
            ("3", "Factor 100 of meer"),
            ("2", "Factor 30 tot 100"),
            ("1", "Factor kleiner dan 30"),
            ("0", "Onbekend: maar één herhalingstijd op deze breslocatie"),
        ],
    },
    "ki_bodemhoogte": {
        "wat": "De kwaliteit van het bodemhoogtemodel (score uit Bodemhoogte.xlsx, omgezet naar 3 klassen).",
        "schaal": [
            ("3", "Score 4 of 5 (o.a. AHN2, AHN3)"),
            ("2", "Score 3"),
            ("1", "Score 1 of 2 (o.a. AHN1)"),
            ("0", "Model onbekend of niet vastgelegd"),
        ],
    },
    "ki_software": {
        "wat": "De kwaliteit van de modelleersoftware (score uit Software.xlsx, omgezet naar 3 klassen).",
        "schaal": [
            ("0", "Nog niet beoordeeld: Software.xlsx bevat alleen nullen"),
        ],
    },
}

# Uitleg bij sterren (grenzen uit Grenzen_5.csv)
INDICATOR_INFO_STERREN = {
    "ki_metadata": {
        "wat": ("Welk deel van de verplichte metadatavelden in LIWO is ingevuld. "
                "Opvulwaarden (alleen een spatie, '-', -999 of -9999) tellen als leeg."),
        "schaal": [
            ("5", "Meer dan 85% van de verplichte velden ingevuld"),
            ("4", "70 tot en met 85%"),
            ("3", "55 tot 70%"),
            ("2", "40 tot 55%"),
            ("1", "Minder dan 40%"),
        ],
    },
    "ki_leeftijd": {
        "wat": "De leeftijd van het scenario: het aantal jaren sinds de scenariodatum.",
        "schaal": [
            ("5", "Maximaal 5 jaar oud"),
            ("4", "6 tot en met 10 jaar"),
            ("3", "11 tot en met 15 jaar"),
            ("2", "16 tot en met 20 jaar"),
            ("1", "Ouder dan 20 jaar"),
            ("0", "Leeftijd onbekend"),
        ],
    },
    "ki_resolutie": {
        "wat": ("De rekenresolutie van het model, uit de LIWO-metadata. Primaire scenario's (type B) "
                "hebben andere grenzen dan de rest."),
        "schaal": [
            ("5", "Type B: 25 m of fijner / overige: 5 m of fijner"),
            ("4", "Type B: tot en met 50 m / overige: tot en met 10 m"),
            ("3", "Type B: tot en met 100 m / overige: tot en met 25 m"),
            ("2", "Type B: grover dan 100 m / overige: tot en met 50 m"),
            ("1", "Overige: grover dan 50 m"),
            ("0", "Resolutie onbekend"),
        ],
    },
    "ki_bodemhoogte": {
        "wat": "De kwaliteit van het bodemhoogtemodel (score uit Bodemhoogte.xlsx).",
        "schaal": [
            ("5", "AHN3"),
            ("4", "AHN2"),
            ("2", "AHN1"),
            ("0", "Model onbekend of niet vastgelegd"),
        ],
    },
    "ki_software": {
        "wat": "De kwaliteit van de gebruikte modelleersoftware (score uit Software.xlsx).",
        "schaal": [
            ("0", "Nog niet beoordeeld: Software.xlsx bevat alleen nullen"),
        ],
    },
}
INDICATOR_INFO = INDICATOR_INFO_3 if BEOORDELING == "3_klassen" else INDICATOR_INFO_STERREN

# ---------------------------------------------------------------- filter op overstromingstype en gemiddelden
# Overstromingstype uit de metadata (kolom 'Type overstroming'); valt samen met de LIWO-werkruimte
OVERSTROMINGSTYPEN = {
    "A": "A - Buitendijks",  # LIWO_Buitendijks
    "B": "B - Primaire keringen",  # LIWO_Primair
    "C": "C - Regionale keringen",  # LIWO_Regionaal
    "D": "D - Regionaal systeem",  # LIWO_RegionaalSysteem
    "G": "G - Bovenregionale stresstest",  # LIWO_BovenRegionaleStresstest
}
KOPPEL_AFSTAND_M = 500  # Een breslocatie telt mee voor de dichtstbijzijnde lijn binnen deze afstand (m)
# Welke typen scenario's tellen mee bij de gemiddelden van een kaartlaag met lijnen
KOPPEL_TYPEN = {"trajecten": ["B"], "keringen": ["C", "D"]}

# ---------------------------------------------------------------- stap 00a: metadata voorbewerken
CSV_METADATA = DATA_MAP / "complete_scenariolist.csv"  # Invoer van stap 00a (LIWO-metadata)
# Per overstromingstype het begin van de CID (coverage-ID) van de WCS; CID = begin + scenarionummer
CID_BEGIN_PER_TYPE = {
    "A": "LIWO_Buitendijks__scenario_",  # Buitendijks
    "B": "LIWO_Primair__scenario_",  # Primaire keringen
    "C": "LIWO_Regionaal__scenario_",  # Regionale keringen
    "D": "LIWO_RegionaalSysteem__scenario_",  # Regionaal systeem
    "BRS": "LIWO_BovenRegionaleStresstest__scenario_",  # Bovenregionale stresstest
}
METADATA_00A = DATA_MAP / "00a_metadata_LIWO.parquet"  # Uitvoer van stap 00a

# ---------------------------------------------------------------- stap 00b: download overstromingsrasters
WCS_URL = "https://geodata.basisinformatie-overstromingen.nl/geoserver/wcs"  # WCS van LIWO
# Vast grid voor heel Nederland (RD, EPSG:28992); ook gebruikt door stap 00c
GRID_CEL = 25  # Celgrootte in meter
GRID_X0 = -10000  # X-coördinaat linkerrand van het grid
GRID_Y0 = 650000  # Y-coördinaat bovenrand van het grid
GRID_KOLOMMEN = 12800  # Aantal kolommen van het grid
MIN_NAT_PCT = 50  # Een cel telt alleen mee als meer dan dit % van de cel nat is
SCHAAL_TOT_RESOLUTIE = 10  # Rasters met een Modelresolutie t/m dit aantal meter worden door de WCS verkleind naar 25 m (sneller, maar minder nauwkeurig)
DIEPTE_MAP = DATA_MAP / "00b_diepte"  # Uitvoer van stap 00b: één parquet per scenario
