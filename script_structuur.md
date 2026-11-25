00a: metadata voorbewerken
-	Lees excel
-	Verwijder kolommen die niet gebruikt worden verder in het onderzoek 
-	Bij welk overstromings type hoort welke CID (config)
-	Voeg kolom CID toe op basis van 
o	Overstromings type 
o	Scenario ID
-	Opslaan as parquet bestand 00a_metadata_LIWO

00b_download_overstroming
-	Lees parquet bestand van metadata
-	Define grid voor Nederland 
-	WCs link basis (config)
-	Functie download van wcs
o	Map: data/00b_diepte 

00c_download_pdok 
-	Define zelfde grid als download overstroming
-	WFS service link (config)
o	Selecteer alleen “meer, plas”, “waterloop”, “zee”
-	Resample naar grid
-	Opslaan
o	Map: data/00c_water

00d_download_overig
-	Download 
-	Voorbewerken 
-	Sla op als parquet bestanden


01a_bepaal_overlap
-	Read metadata 00a 
-	Formule berekenen dichtstbijzijnde punten
-	Formule max overlap berekenen -> scenario nr & overlap 
-	Formule schade zelfde berekenen
-	Formule slachtoffers zelfde berekenen
-	Voeg toe aan df: scenario met meeste overlap, overlap, slachtoffers, schade
-	Sla df op als 01a_metadata_LIWO (parquet)

01b_bepaal_overlap_water
-	Read metadata 00a 
-	Formule max overlap berekenen -> scenario nr & overlap 
o	Overlap met water telt alleen als de hele pixel in water licht dus als de hele pixel flood dan en het is water dan wordt ie meegeteld als pixel die niet afgeknipt is. 
-	Formule schade zelfde berekenen
-	Formule slachtoffers zelfde berekenen
-	Voeg toe aan df: scenario met meeste overlap, overlap, slachtoffers, schade
-	Sla df op als 01a_metadata_LIWO (parquet)

01b_kwaliteit_scenario
-	Lees 01ª_metadata_liwo
-	Formule metadata
-	Formule leeftijd 
-	Formule software 
-	Main
o	Apply functies to hele df 
o	Voeg informatiie to aan df met KI_  
-	Sla op als parquet
-	Maak geometrie van en sla op als gpkg


02_kwaliteit bres 
-	Lees .gpkg met kwaliteit per scenario
-	Koppel informatie aan bres met spatial join (of zelfde xy waardes)
-	Spreiding herhalings tijd functie
-	Sla op als gpkg

03_kwaliteit_trajectdeel 
-	Read breslocatie informatie van relevant scenario’s (LIWO primair alleen)
-	Koppel bres informatie aan traject deel
-	Check een breslocatie per traject deel
-	Sla op als gpkg

04_kwaliteit traject
-	Read gpkg traject deel
-	Koppel traject delen aan traject
-	Toevoegen aan dashboard:
o	Beheerder???
o	Traject info???

05_kwaliteit_waterschap
-	Read gpkg scenarios 
-	Groep informatie van scenarios in primair, regionaal en geef samenvatting van die scenarios 
o	Gemiddeldes ofzo???
-	Score

06_maak_dashboard
