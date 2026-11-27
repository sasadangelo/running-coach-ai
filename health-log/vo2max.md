# VO2max Log

**Stima attuale: 40.7 ml/kg/min** (al 2026-11-27; controllo: mediana delle singole corse degli ultimi 28 giorni 40.3).

Stima dalla relazione FC-passo: `VO2 = 0.2 x velocita (m/min) + 3.5` (ACSM, corsa in piano, velocita corretta per la pendenza), `%FCR = (FC - FC riposo) / (185 - FC riposo)`, `VO2max = 3.5 + (VO2 - 3.5) / %FCR` (Swain).

- **VO2max stimato:** ogni corsa aggiorna la stima senza sostituirla, come fa Garmin. E la media delle stime delle corse fatte fin li, pesata sui minuti stabili e sull'eta: il peso di una corsa si dimezza ogni 15 giorni (costante di tempo 21 giorni). Un lungo da 36' sposta la stima tre volte piu di un Tempo con 12' utili. La stima attuale e quella dopo l'ultima corsa.
- **Perche non si usa la singola corsa:** con i valori dell'ultima corsa 1 bpm di FC vale 0.34 punti, quindi 2 bpm di variazione giornaliera (sonno, stress, caldo, sensore) sposterebbero la stima di ~0.7, mentre il VO2max vero cambia in settimane o mesi.
- **Tratti usati:** solo ritmo stabile (passo entro +/-6% per almeno 2 minuti), FC stabile (oscillazione massima 8 bpm), dopo i primi 10 minuti e con FC sopra il 50% della riserva. Recuperi, transizioni, defaticamenti dopo lavori intensi e ripetute brevi restano esclusi, cosi come le corse con piu del 10% di camminata.
- **Per corsa:** mediana dei tratti stabili; servono almeno 5 minuti stabili.
- **FC max 185** da `.claude/training-zones.yaml`: la stima dipende soprattutto dalla FC max. **FC a riposo** della settimana della corsa (media dei 7 giorni fino alla corsa da `daily-health.md`, notti senza orologio escluse): cosi le corse passate non cambiano quando cambia la FC a riposo di oggi.
- **Limiti:** la formula ACSM presume un'economia di corsa media; caldo, poco sonno e stanchezza alzano la FC e abbassano la stima. Da leggere come trend; l'errore sul valore assoluto e di qualche punto. Verifica indipendente: test dei 7' (VO2max ~ 3.5 x VAM in km/h) o test cardiopolmonare.
- **VO2max Garmin:** valore con un decimale del giorno della corsa (metriche giornaliere Garmin; se manca, quello intero dell'attivita). Calcolato da Garmin con la sua FC max (194 nel profilo Garmin), quindi tendenzialmente piu alto.

| Data       | Attivita           | Minuti stabili | Passo medio (GAP) | FC media | FC riposo | VO2max stimato | VO2max Garmin |
| ---------- | ------------------ | -------------- | ----------------- | -------- | --------- | -------------- | ------------- |
| 2026-09-13 | S2 Long run 4.2km  | 21             | 7:34/km           | 158 bpm  | 55.7      | 36.9           | 43.7          |
| 2026-09-20 | S3 Long run 4.5km  | 21             | 7:17/km           | 152 bpm  | 57.1      | 39.0           | 43.6          |
| 2026-09-25 | S4 Easy run        | 15             | 7:02/km           | 154 bpm  | 56.5      | 39.6           | 43.4          |
| 2026-09-27 | S4 Long run 3.5km  | 15             | 7:03/km           | 153 bpm  | 56.5      | 40.1           | 43.3          |
| 2026-10-02 | S5 Tempo 3x800m    | 12             | 6:40/km           | 162 bpm  | 56.6      | 40.3           | 43.4          |
| 2026-10-04 | S5 Long run 5km    | 26             | 7:10/km           | 153 bpm  | 56.8      | 40.4           | 43.2          |
| 2026-10-09 | S6 Tempo 2x1200m   | 14             | 6:42/km           | 165 bpm  | 56.7      | 40.2           | 43.2          |
| 2026-10-11 | S6 Long run 5.7km  | 28             | 7:05/km           | 154 bpm  | 56.4      | 40.3           | 43.1          |
| 2026-10-16 | S7 Tempo 2x1500m   | 19             | 6:35/km           | 163 bpm  | 56.9      | 40.4           | 43.3          |
| 2026-10-18 | S7 Long run 6.4km  | 36             | 7:16/km           | 150 bpm  | 57.1      | 40.8           | 43.2          |
| 2026-10-23 | S8 Easy run        | 19             | 7:04/km           | 152 bpm  | 56.1      | 40.9           | 43.2          |
| 2026-10-25 | S8 Long run 4.2km  | 21             | 8:08/km           | 142 bpm  | 56.5      | 40.8           | 43.0          |
| 2026-10-29 | S9 Tempo 2000m     | 15             | 6:34/km           | 163 bpm  | 60.0      | 40.8           | 43.1          |
| 2026-11-01 | S9 Long run 7km    | 38             | 7:13/km           | 155 bpm  | 60.1      | 40.5           | 42.9          |
| 2026-11-08 | Rome 5k            | 14             | 6:13/km           | 168 bpm  | 58.1      | 40.5           | 42.8          |
| 2026-11-10 | S11 Easy run       | 20             | 7:49/km           | 151 bpm  | 59.1      | 40.2           | 42.5          |
| 2026-11-15 | S11 Long run 6.5km | 37             | 7:13/km           | 151 bpm  | 59.3      | 40.5           | 42.4          |
| 2026-11-22 | S12 Long run 7.5km | 43             | 7:13/km           | 150 bpm  | 57.6      | 40.8           | 42.5          |
| 2026-11-27 | S13 Tempo 3000m    | 22             | 6:40/km           | 164 bpm  | 55.2      | 40.7           | 42.7          |
