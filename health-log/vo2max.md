# VO2max Log

**Stima attuale: 40.8 ml/kg/min** (al 2026-10-29; controllo: mediana delle singole corse degli ultimi 28 giorni 40.8).

Stima dalla relazione FC-passo: `VO2 = 0.2 x velocita (m/min) + 3.5` (ACSM, corsa in piano, velocita corretta per la pendenza), `%FCR = (FC - FC riposo) / (185 - FC riposo)`, `VO2max = 3.5 + (VO2 - 3.5) / %FCR` (Swain).

- **VO2max stimato:** ogni corsa aggiorna la stima senza sostituirla, come fa Garmin. E la media delle stime delle corse fatte fin li, pesata sui minuti stabili e sull'eta: il peso di una corsa si dimezza ogni 15 giorni (costante di tempo 21 giorni). Un lungo da 36' sposta la stima tre volte piu di un Tempo con 12' utili. La stima attuale e quella dopo l'ultima corsa.
- **Perche non si usa la singola corsa:** con i valori dell'ultima corsa 1 bpm di FC vale 0.36 punti, quindi 2 bpm di variazione giornaliera (sonno, stress, caldo, sensore) sposterebbero la stima di ~0.7, mentre il VO2max vero cambia in settimane o mesi.
- **Tratti usati:** solo ritmo stabile (passo entro +/-6% per almeno 2 minuti), FC stabile (oscillazione massima 8 bpm), dopo i primi 10 minuti e con FC sopra il 50% della riserva. Recuperi, transizioni, defaticamenti dopo lavori intensi e ripetute brevi restano esclusi, cosi come le corse con piu del 10% di camminata.
- **Per corsa:** mediana dei tratti stabili; servono almeno 5 minuti stabili.
- **FC max 185** da `.claude/training-zones.yaml`: la stima dipende soprattutto dalla FC max. **FC a riposo** della settimana della corsa (media dei 7 giorni fino alla corsa da `daily-health.md`, notti senza orologio escluse): cosi le corse passate non cambiano quando cambia la FC a riposo di oggi.
- **Limiti:** la formula ACSM presume un'economia di corsa media; caldo, poco sonno e stanchezza alzano la FC e abbassano la stima. Da leggere come trend; l'errore sul valore assoluto e di qualche punto. Verifica indipendente: test dei 7' (VO2max ~ 3.5 x VAM in km/h) o test cardiopolmonare.
- **VO2max Garmin:** valore con un decimale del giorno della corsa (metriche giornaliere Garmin; se manca, quello intero dell'attivita). Calcolato da Garmin con la sua FC max (194 nel profilo Garmin), quindi tendenzialmente piu alto.

| Data       | Attivita                     | Minuti stabili | Passo medio (GAP) | FC media | FC riposo | VO2max stimato | VO2max Garmin |
| ---------- | ---------------------------- | -------------- | ----------------- | -------- | --------- | -------------- | ------------- |
| 2026-09-13 | Corsa 4.2 km                 | 21             | 7:34/km           | 158 bpm  | 55.7      | 36.9           | 43.7          |
| 2026-09-20 | Lungo 4.5 Km                 | 21             | 7:17/km           | 152 bpm  | 57.1      | 39.0           | 43.6          |
| 2026-09-25 | Corsa Lenta 3.5 Km (scarico) | 15             | 7:02/km           | 154 bpm  | 56.5      | 39.6           | 43.4          |
| 2026-09-27 | Corsa Lenta (scarico)        | 15             | 7:03/km           | 153 bpm  | 56.5      | 40.1           | 43.3          |
| 2026-10-02 | Tempo 3x800 m                | 12             | 6:40/km           | 162 bpm  | 56.6      | 40.3           | 43.4          |
| 2026-10-04 | Corsa Lenta Lunga 5 Km       | 26             | 7:10/km           | 153 bpm  | 56.8      | 40.4           | 43.2          |
| 2026-10-09 | Tempo 2x1200 m               | 14             | 6:42/km           | 165 bpm  | 56.7      | 40.2           | 43.2          |
| 2026-10-11 | Corsa (Lungo) 5.7 Km         | 28             | 7:05/km           | 154 bpm  | 56.4      | 40.3           | 43.1          |
| 2026-10-16 | Tempo 2x1500 m               | 19             | 6:35/km           | 163 bpm  | 56.9      | 40.4           | 43.3          |
| 2026-10-18 | Lungo 6.4 Km                 | 36             | 7:16/km           | 150 bpm  | 57.1      | 40.8           | 43.2          |
| 2026-10-23 | Corsa Lenta 4km (Scarico)    | 19             | 7:04/km           | 152 bpm  | 56.1      | 40.9           | 43.2          |
| 2026-10-25 | Corsa Recupero (Scarico)     | 21             | 8:08/km           | 142 bpm  | 56.5      | 40.8           | 43.0          |
| 2026-10-29 | Tempo 2Km                    | 15             | 6:34/km           | 163 bpm  | 60.0      | 40.8           | 43.1          |
