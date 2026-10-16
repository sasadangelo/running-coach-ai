# Capacity Score Log

Score di capacita aerobica dei Tempo run: `CS = (velocita m/s / FC) x minuti di blocco x 100 x C x M_drift`.

- **Blocco**: il tratto continuo piu lungo sotto 6:40/km; riscaldamento e defaticamento esclusi. Solo blocchi di almeno 20 minuti: le sedute a ripetute non hanno CS.
- **Passo e FC del blocco**: medie del blocco senza i primi 2 minuti, in cui la FC sta ancora salendo.
- **C (controllo del passo)**: quota del blocco corsa nella fascia Tempo 6:10-6:30/km (passo medio su 30s).
- **M_drift (deriva)**: decoupling passo:FC tra prima e seconda meta del blocco; 1.0 se <= 5%, altrimenti 1 - (decoupling - 5)/100.
- **Da guardare oltre al CS**: la FC del blocco a parita di passo. Se scende nelle settimane, la capacita aerobica sta migliorando.

## Categorie

| Livello            | CS     | Blocco continuo a soglia | Capacita aerobica                                                             |
| ------------------ | ------ | ------------------------ | ----------------------------------------------------------------------------- |
| Soglia iniziale    | 0-35   | 20-22 min                | Primo blocco continuo a soglia: lo sforzo regge, ma e al limite della durata. |
| Soglia in crescita | 35-45  | 22-28 min                | Il blocco si allunga senza crollare di passo; la FC resta governabile.        |
| Soglia consolidata | 45-60  | 28-35 min                | Mezz'ora a soglia in controllo: la base del Tempo classico da 10K.            |
| Soglia avanzata    | 60-75  | 35-45 min                | Blocchi lunghi con deriva contenuta: capacita aerobica da 10K forte o mezza.  |
| Soglia esperta     | 75-100 | 45-60 min                | Quasi un'ora vicino alla soglia: livello da mezza maratona competitiva.       |
| Elite              | >= 100 | > 60 min                 | Oltre l'ora a soglia con FC stabile: ritmo gara da mezza di alto livello.     |

Le durate indicative valgono per circa 1.6-2 punti di CS al minuto: chi e piu efficiente, cioe piu veloce a parita di FC, sale di livello con meno minuti.

## Tempo run

Nessun Tempo con un blocco continuo di almeno 20 minuti finora.
