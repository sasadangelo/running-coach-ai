# VO2max Log

**Stima attuale: 40.8 ml/kg/min** (mediana delle corse degli ultimi 28 giorni).

Stima dalla relazione FC-passo: `VO2 = 0.2 x velocita (m/min) + 3.5` (ACSM, corsa in piano, velocita corretta per la pendenza), `%FCR = (FC - 58) / (185 - 58)`, `VO2max = 3.5 + (VO2 - 3.5) / %FCR` (Swain).

- **Tratti usati:** solo ritmo stabile (passo entro +/-6% per almeno 2 minuti), FC stabile (oscillazione massima 8 bpm), dopo i primi 10 minuti e con FC sopra il 50% della riserva. Recuperi, transizioni, defaticamenti dopo lavori intensi e ripetute brevi restano esclusi, cosi come le corse con piu del 10% di camminata.
- **Per corsa:** mediana dei tratti stabili; servono almeno 5 minuti stabili.
- **FC max 185 e FC a riposo 58** da `.claude/training-zones.yaml`: la stima dipende soprattutto dalla FC max.
- **Limiti:** la formula ACSM presume un'economia di corsa media; caldo, poco sonno e stanchezza alzano la FC e abbassano la stima. Da leggere come trend; l'errore sul valore assoluto e di qualche punto. Verifica indipendente: test dei 7' (VO2max ~ 3.5 x VAM in km/h) o test cardiopolmonare.
- **VO2max Garmin:** calcolato da Garmin con la sua FC max (194 nel profilo Garmin), quindi tendenzialmente piu alto.

| Data       | Attivita                     | Minuti stabili | Passo medio (GAP) | FC media | VO2max stimato | VO2max Garmin |
| ---------- | ---------------------------- | -------------- | ----------------- | -------- | -------------- | ------------- |
| 2026-09-13 | Corsa 4.2 km                 | 21             | 7:34/km           | 158 bpm  | 37.1           | 42            |
| 2026-09-20 | Lungo 4.5 Km                 | 21             | 7:17/km           | 152 bpm  | 40.5           | 42            |
| 2026-09-25 | Corsa Lenta 3.5 Km (scarico) | 15             | 7:02/km           | 154 bpm  | 41.1           | 43            |
| 2026-09-27 | Corsa Lenta (scarico)        | 15             | 7:03/km           | 153 bpm  | 41.5           | 42            |
| 2026-10-02 | Tempo 3x800 m                | 12             | 6:40/km           | 162 bpm  | 40.8           | 43            |
| 2026-10-04 | Corsa Lenta Lunga 5 Km       | 26             | 7:10/km           | 153 bpm  | 40.8           | 43            |
| 2026-10-09 | Tempo 2x1200 m               | 14             | 6:42/km           | 165 bpm  | 39.2           | 43            |
| 2026-10-11 | Corsa (Lungo) 5.7 Km         | 28             | 7:05/km           | 154 bpm  | 40.9           | 43            |
| 2026-10-16 | Tempo 2x1500 m               | 19             | 6:35/km           | 163 bpm  | 40.7           | 43            |
| 2026-10-18 | Lungo 6.4 Km                 | 36             | 7:16/km           | 150 bpm  | 41.8           | 43            |
| 2026-10-23 | Corsa Lenta 4km (Scarico)    | 19             | 7:04/km           | 152 bpm  | 41.5           | 43            |
| 2026-10-25 | Corsa Recupero (Scarico)     | 21             | 8:08/km           | 142 bpm  | 40.4           | 43            |
