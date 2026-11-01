# Forza e Mobilità — Test mensili

Batteria di test da fare a casa una volta al mese, in un giorno senza corsa o prima di una corsa facile, a muscoli caldi (5' di camminata veloce o mobilità). Circa 15 minuti. Prima misurazione: settimana di scarico S8 (19-25 ottobre 2026).

La metrica chiave è la **differenza destra/sinistra**: `asimmetria % = (lato migliore − lato peggiore) / lato migliore × 100`. Sopra il 10-15% va corretta con lavoro mirato sul lato debole.

## I test

### Forza
1. **Calf raise su una gamba** (polpaccio, Achille, fascia plantare). In piedi su un gradino con l'avampiede, tallone libero, un dito al muro solo per l'equilibrio. Su e giù per tutta l'escursione, ritmo regolare (1" su, 1" giù). Si conta finché la salita resta completa. Riferimento: 25 o più per lato.
   **Variante sul pavimento** (senza gradino, e più prudente per la fascia plantare): scalzi su pavimento duro, si sale il più in alto possibile e si scende fino a toccare terra col tallone. Per controllare l'altezza si fissa un punto sul muro all'altezza degli occhi alla prima ripetizione: quando la testa non ci arriva più, ci si ferma. **Il segno resta fisso** (matita o nastro sulla porta, con l'altezza in cm da terra annotata nella scheda): ogni test successivo usa lo stesso segno. Primo segno fisso: test del 21/11/2026. Riferimento: 20-25 per lato. Annotare sempre la variante usata ed eseguire il test ogni mese nello stesso modo. Massimo 40 ripetizioni.
2. **Side plank** (gluteo medio, core laterale). Sull'avambraccio, corpo in linea, piedi sovrapposti. Tempo massimo finché il bacino non scende. Riferimento: 60" o più per lato.
3. **Glute bridge su una gamba** (gluteo). Supino, un piede a terra con ginocchio piegato, l'altra gamba tesa in alto. Si sale fino ad allineare spalla, anca e ginocchio. Ripetizioni finché il bacino resta in linea, senza ruotare. Riferimento: 20 o più per lato.

### Controllo
4. **Mezzo squat su una gamba** davanti allo specchio, 5 per lato, lento. Si annota per ciascun lato: *il bacino scende dal lato della gamba sollevata?* e *il ginocchio cade verso l'interno?* (sì/no).
5. **Equilibrio su una gamba a occhi chiusi**, braccia lungo i fianchi. Tempo finché non si apre gli occhi o si appoggia l'altro piede (massimo 30"). Migliore di 2 tentativi per lato.

### Mobilità
6. **Ginocchio al muro** (dorsiflessione della caviglia). Piede perpendicolare al muro, ginocchio che tocca il muro con il tallone a terra. Si allontana il piede finché il tallone resta giù: si misurano i cm tra alluce e muro. Riferimento: 10 cm o più per lato.
7. **Flessori dell'anca (test di Thomas modificato).** Supino sul bordo del letto, si porta un ginocchio al petto: la coscia dell'altra gamba resta appoggiata (ok) o si solleva (rigido)? Per lato.

### Postura in corsa
8. **Video di 10-15"** da dietro e da davanti, nei primi km del lungo e negli ultimi 500 m: c'è un'inclinazione laterale del busto? Da che lato? Peggiora a fine corsa?

## Osservazioni sulla postura in corsa
- **23 ottobre 2026 (moglie, a occhio, alla partenza della corsa, quindi a gambe fresche):** gomito sinistro più alto; tronco spostato di circa 3-5 gradi verso destra. Presente da subito: più probabile un'abitudine motoria o uno squilibrio di base che un cedimento da fatica. Escluse le cause banali: l'atleta usa un marsupio da corsa e non porta nulla in mano o in tasca. Restano: gluteo medio dx (test di sabato), rigidità iniziale (video di domenica, inizio contro fine), differenza di lunghezza delle gambe o postura abituale (solo con un fisioterapista). Ipotesi da verificare, non diagnosi: compenso per un gluteo medio dx debole (il tronco si sposta sopra la gamba d'appoggio per tenere il bacino; il braccio opposto si alza per bilanciare), coerente con il fastidio all'anca dx dell'11 e del 14 ottobre. Verifiche: side plank dx contro sx, mezzo squat su una gamba (il bacino scende?), video del lungo (inizio contro fine).

Dopo ogni test: inserire la riga nella tabella dei risultati e lanciare `python3 .claude/scripts/calculate_strength_mobility.py`, che calcola gli indici FS e MCS (sezione Indici in fondo) usati dal profilo mensile.

Versione stampabile del protocollo con scheda dei risultati: [test-forza-mobilita.pdf](test-forza-mobilita.pdf).

## Risultati

| Data | Calf raise dx | Calf raise sx | Side plank dx | Side plank sx | Bridge 1 gamba dx | Bridge 1 gamba sx | Bacino scende (dx/sx) | Ginocchio dentro (dx/sx) | Equilibrio dx | Equilibrio sx | Ginocchio-muro dx | Ginocchio-muro sx | Thomas dx/sx | Inclinazione in corsa |
| ---- | ------------- | ------------- | ------------- | ------------- | ----------------- | ----------------- | --------------------- | ------------------------ | ------------- | ------------- | ----------------- | ----------------- | ------------ | --------------------- |
| 24/10/2026 | 16 | 13 | 36" | 29" | 32 | 27 | dx no / sx sì | dx no / sx sì | 30" (37") | 18" | 10.5 cm | 9.5 cm | ok / ok | video domenica 25/10 |

Calf raise: variante sul pavimento (ripeterla così ai prossimi test). Riferimento all'altezza degli occhi usato, ma non lasciato segnato: al 21/11 l'altezza potrebbe differire di poco, quindi il confronto con il 24/10 ha un piccolo margine (3-4 ripetizioni di differenza sono comunque un segnale vero). In allenamento il 1/11: 1x20 su una gamba sx, senza riferimento e dopo 3x20: non confrontabile con il test. Equilibrio dx oltre il massimo di 30" (tenuto 37"); per l'asimmetria si usa 30".

### Lettura del 24/10/2026 (prima misurazione)
| Test | dx | sx | Asimmetria | Riferimento | Giudizio |
| ---- | -- | -- | ---------- | ----------- | -------- |
| Calf raise (pavimento) | 16 | 13 | 19% (sx) | 20-25 | entrambi sotto, sx di più |
| Side plank | 36" | 29" | 19% (sx) | 60"+ | entrambi sotto, sx di più |
| Bridge 1 gamba | 32 | 27 | 16% (sx) | 20+ | entrambi sopra, asimmetria al limite |
| Equilibrio occhi chiusi | 30" | 18" | 40% (sx) | 30" | sx scarso |
| Squat 1 gamba | ok | bacino scende + ginocchio dentro | — | — | sx: gluteo medio sx debole |
| Ginocchio-muro | 10.5 cm | 9.5 cm | 10% (sx) | 10 cm+ | nella norma, sx al limite |
| Thomas | ok | ok | — | — | flessori dell'anca non rigidi |

- **Quadro coerente: il lato debole è il sinistro**, in tutti i test, con asimmetrie sopra il 15% (sopra il 40% nell'equilibrio). Una sola misurazione: va confermata al test di novembre.
- **L'ipotesi del gluteo medio dx debole non è confermata; è il sinistro.** Il side plank dx è il migliore dei due, e nello squat su gamba sx il bacino scende e il ginocchio cade dentro (segno classico di gluteo medio debole dal lato d'appoggio). La caviglia sx un po' più rigida (9.5 contro 10.5 cm) può contribuire al ginocchio che entra. Il fastidio all'anca dx (11 e 14/10) potrebbe essere un sovraccarico del lato forte che compensa il sinistro, ma è un'ipotesi, non una diagnosi. Anche l'inclinazione del tronco a destra resta da spiegare (video del lungo).
- **Valori assoluti:** polpacci e side plank sotto il riferimento su entrambi i lati: la capacità del polpaccio è il punto più importante per chi aumenta il volume (Achille, fascia plantare). Glutei buoni. Flessori dell'anca a posto.
- **Lavoro:** esercizi su entrambi i lati, con **una serie in più sul sinistro** (calf raise, side plank, equilibrio su una gamba, mezzo squat su una gamba davanti allo specchio con bacino in bolla e ginocchio sopra il piede). Il lato destro non va allenato meno: va portato su anche lui. Prossimo test: sabato 21 novembre 2026, stesse condizioni e stessa variante.

## Indici

Generato da `.claude/scripts/calculate_strength_mobility.py` dalla tabella dei risultati: rilanciarlo dopo ogni test. Ogni test vale (lato piu debole / riferimento) x 100, con tetto a 100: 100 = adeguato per un runner. Conta solo il lato piu debole, quindi l'indice sale solo se migliora quello. Nel profilo mensile e nel radar entrano come indice 100 = primo test.

- **FS (Forza)**: media di calf raise, side plank e bridge su una gamba. Riferimenti: Calf raise 25, Side plank 60, Bridge 1 gamba 20.
- **MCS (Mobilita e controllo)**: media di ginocchio-muro, equilibrio a occhi chiusi, mezzo squat su una gamba (bacino in bolla + ginocchio sopra il piede, per lato) e test di Thomas. Riferimenti: Ginocchio-muro 10, Equilibrio 30.

| Data | FS | MCS | Calf raise | Side plank | Bridge | Ginocchio-muro | Equilibrio | Squat 1 gamba | Thomas |
| ---------- | --: | --: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-10-24 | 67 | 76 | 13 -> 52 | 29 -> 48 | 27 -> 100 | 9.5 -> 95 | 18 -> 60 | 50 | 100 |
