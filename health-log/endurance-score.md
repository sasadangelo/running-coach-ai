# Endurance Score Log

Score di resistenza aerobica dei lunghi: `ES = (velocita m/s / FC media) x km x 100 x C x M_dec x H`.

- **C (continuita)**: (tempo di corsa / tempo totale)^2 x max(0.2, 1 - 0.05 x stop). Uno stop e una camminata di almeno 15s sotto ~9:00/km.
- **M_dec (deriva)**: 1.0 se decoupling <= 5%, altrimenti 1 - (decoupling - 5)/100. Decoupling dallo stesso calcolo di `aerobic-decoupling.md`. Quando non e calcolabile (corsa sotto i 30 min o troppo camminata) ES e n/d: senza deriva misurata lo score non e confrontabile. Il lungo conta comunque per H.
- **H (memoria)**: giorni dall'ultimo lungo di almeno l'85% della distanza: <= 14 -> 1.0, 15-30 -> 0.90, oltre o mai -> 0.75.

## Categorie

| Livello         | ES    | Lungo continuo tipico     | Tenuta aerobica                                                                                               |
| --------------- | ----- | ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Avvio           | 0-4   | < 2.5 km o corsa/cammino  | La corsa continua non regge ancora: servono camminate per arrivare in fondo.                                  |
| Primi km        | 4-8   | 2.5-5 km                  | Corsa continua acquisita su distanze brevi; ogni km in piu e un adattamento nuovo.                            |
| Base            | 8-12  | 5-7.5 km                  | Oltre la mezz'ora di corsa senza fermarsi, FC stabile: e gia piu di quanto corra la gran parte delle persone. |
| Base solida     | 12-16 | 7.5-10 km                 | Vicino ai 10 km in corsa continua; la resistenza regge un'ora di sforzo.                                      |
| 10K             | 16-24 | 10-15 km                  | Il 10 km e un allenamento, non piu una gara al limite.                                                        |
| Avanzato        | 24-35 | 15-21 km                  | Lunghi oltre l'ora e mezza, deriva cardiaca contenuta.                                                        |
| Mezzamaratoneta | 35-50 | 21-30 km                  | La mezza maratona e alla portata in allenamento; la maratona e il passo successivo.                           |
| Maratoneta      | 50-70 | 30-42 km                  | Lunghi da maratona con FC contenuta e decoupling sotto il 5%.                                                 |
| Elite / Ultra   | >= 70 | > 42 km o maratona veloce | Volumi da ultra o lunghi molto veloci a FC bassa, in stabilita perfetta.                                      |

Le distanze indicative valgono a ritmo facile (circa 1.5-2 punti di ES per km): chi e piu efficiente, cioe piu veloce a parita di FC, sale di livello con meno km.

## Lunghi

| Data       | Attivita                 | Distanza | Passo   | FC media | % corsa | Stop | C    | Decoupling | M_dec | Giorni da lungo simile | H    | Base | ES   | Livello  |
| ---------- | ------------------------ | -------- | ------- | -------- | ------- | ---- | ---- | ---------- | ----- | ---------------------- | ---- | ---- | ---- | -------- |
| 2026-09-06 | Corsa 4 Km               | 4.01 km  | 7:21/km | 151 bpm  | 81%     | 3    | 0.56 | n/d        | n/d   | nessuno                | 0.75 | 6.0  | n/d  | n/d      |
| 2026-09-13 | Corsa 4.2 km             | 4.21 km  | 7:24/km | 154 bpm  | 100%    | 0    | 1.00 | 3.0%       | 1.00  | 7                      | 1.00 | 6.2  | 6.2  | Primi km |
| 2026-09-20 | Lungo 4.5 Km             | 4.51 km  | 7:19/km | 147 bpm  | 100%    | 0    | 1.00 | 4.8%       | 1.00  | 7                      | 1.00 | 7.0  | 7.0  | Primi km |
| 2026-09-27 | Corsa Lenta (scarico)    | 3.52 km  | 7:11/km | 146 bpm  | 100%    | 0    | 1.00 | n/d        | n/d   | 7                      | 1.00 | 5.6  | n/d  | n/d      |
| 2026-10-04 | Corsa Lenta Lunga 5 Km   | 5.01 km  | 7:10/km | 149 bpm  | 100%    | 0    | 0.99 | 2.1%       | 1.00  | 14                     | 1.00 | 7.8  | 7.8  | Primi km |
| 2026-10-11 | Corsa (Lungo) 5.7 Km     | 5.71 km  | 7:08/km | 149 bpm  | 100%    | 0    | 1.00 | 4.3%       | 1.00  | 7                      | 1.00 | 9.0  | 8.9  | Base     |
| 2026-10-18 | Lungo 6.4 Km             | 6.41 km  | 7:19/km | 146 bpm  | 100%    | 0    | 1.00 | 1.3%       | 1.00  | 7                      | 1.00 | 10.0 | 10.0 | Base     |
| 2026-10-25 | Corsa Recupero (Scarico) | 4.21 km  | 8:03/km | 139 bpm  | 100%    | 0    | 1.00 | 1.3%       | 1.00  | 7                      | 1.00 | 6.3  | 6.3  | Primi km |
