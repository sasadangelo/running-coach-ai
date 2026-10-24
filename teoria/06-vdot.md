# Il VDOT: un numero per gare e ritmi

> Bozza, iniziata il 24 ottobre 2026. Tabelle complete in [appendice A](appendice-a-tabelle-vdot.md).

## 1. Il principio

Il **VDOT** è un numero, ricavato da una gara recente, che riassume il livello di un runner. Da quel numero discendono due cose:
- **i tempi equivalenti** sulle altre distanze (chi corre i 5 km in 30:41 "vale" 1:03:49 sui 10 km);
- **i ritmi di allenamento** E, M, T, I, R (capitolo [04](04-ritmi-zone-sedute.md)).

L'idea è di **Jack Daniels** e del matematico **Jimmy Gilbert** (*Oxygen Power*, 1979). Il nome viene da "V̇O2max", con il punto sulla V che indica una portata: ossigeno al minuto.

**Il VDOT non è il VO2max.** È un **VO2max "efficace"**: il VO2max che avrebbe un runner di riferimento con un'economia di corsa media per correre quella gara in quel tempo. Due runner con lo stesso VO2max possono avere VDOT molto diversi, perché il VDOT include anche l'economia di corsa (quanto ossigeno costa ogni metro) e la resistenza (quanta parte del massimo si regge a lungo). Per questo è più utile del VO2max per allenarsi: misura quello che arriva in strada, non solo il motore.

## 2. Come si calcola: due curve

Daniels e Gilbert hanno ricavato due relazioni dai dati di runner allenati.

**Curva 1: il costo in ossigeno di una velocità.** Quanto ossigeno serve per correre a una velocità *v* (in metri al minuto):

> VO2 = −4.60 + 0.182258 · v + 0.000104 · v²

Il costo cresce un po' più che in proporzione alla velocità.

**Curva 2: la frazione del massimo che si regge per un certo tempo.** Per uno sforzo di *t* minuti al massimo:

> %VO2max = 0.8 + 0.1894393 · e^(−0.012778 · t) + 0.2989558 · e^(−0.1932605 · t)

Per circa 10' si regge il 100% del VO2max, per 30' circa il 93%, per un'ora circa l'89%, per tre ore circa l'82%.

**VDOT = costo della velocità di gara ÷ frazione sostenibile per quella durata.**

**Esempio:** 5 km in 30:41.
- Velocità: 5000 / 30.68 = 163 m/min → costo ≈ 27.9 ml/kg/min.
- Frazione sostenibile per 30.7 minuti: ≈ 0.93.
- VDOT = 27.9 / 0.93 ≈ **30**.

**Dal VDOT ai ritmi** (percentuali del VDOT, approssimate: Daniels ha arrotondato le sue tabelle a mano):

| Ritmo | % del VDOT | Logica |
|---|---|---|
| **E** (lento) | ~62-70% | sotto la soglia aerobica |
| **M** (maratona) | — | il ritmo della maratona prevista dalle curve |
| **T** (soglia) | ~88% | ciò che si regge per ~60' |
| **I** (intervalli) | ~97-100% | il VO2max, ciò che si regge per 10-12' |
| **R** (ripetizioni) | I meno ~6"/400 m | circa il ritmo del miglio |

## 3. Cosa dice la scienza

- **Consolidato:** per runner allenati, le equivalenze tra 3 km e mezza maratona funzionano bene, con un errore tipico di pochi punti percentuali. Il VDOT è uno degli strumenti più usati al mondo per fissare i ritmi.
- **Probabile:** **la maratona prevista è ottimista** per chi ha poco volume. Le curve assumono un allenamento adeguato alla distanza: chi corre 20-30 km a settimana non tiene in maratona la frazione prevista, e lo dice Daniels stesso. Lo stesso vale, in misura minore, per la mezza.
- **Probabile:** l'**economia di corsa** varia molto da persona a persona (±10-15%). Il VDOT la incorpora senza misurarla: due runner con lo stesso VDOT possono avere motori diversi.
- **Discusso:** le curve vengono da runner allenati degli anni '70. Per principianti, donne e over 50 i dati sono pochi, e la curva della frazione sostenibile sembra più ripida (si regge meno a lungo).

**Formule alternative:**
- **Riegel** (1977): T₂ = T₁ × (D₂/D₁)^1.06. Più semplice e simile al VDOT tra 5 km e mezza; anche lei ottimista per la maratona dei poco allenati.
- **McMillan:** tabelle e calcolatore costruiti sull'esperienza di allenatore. Distingue i runner "veloci" da quelli "resistenti".

## 4. Come si usa

**Quale gara:**
- una gara vera, corsa al massimo, tra i 5 km e la mezza (i 3 km se non c'è altro);
- **recente**: le ultime 4-6 settimane;
- in condizioni normali. Caldo, vento, salita e pacing sbagliato abbassano il VDOT: o si corregge il risultato o si sceglie un'altra gara.

**Se ci sono più gare:** si usa la migliore delle ultime settimane. Se le distanze danno VDOT diversi, la differenza dice qualcosa: VDOT più alto sulle distanze corte vuol dire che manca resistenza, più alto sulle lunghe che manca velocità.

**Quando aggiornarlo (Daniels):**
- dopo ogni gara, se il VDOT è salito;
- senza gare, **+1 punto non prima di 4-6 settimane**, e solo se i ritmi attuali sono diventati facili;
- mai un aumento sulla base di un solo allenamento andato bene.

**Errori comuni:**
- allenarsi al VDOT che si **vorrebbe** avere (quello dell'obiettivo) invece di quello attuale;
- usare il miglior tempo di anni fa;
- trattare i ritmi come esatti al secondo: sono fasce, e caldo, sonno e fatica le spostano.

## 5. Cosa è successo a me

| Quando | Gara | VDOT | Note |
|---|---|---|---|
| 2017 | 10 km in 53' | **37.4** | il riferimento storico, 9 anni fa |
| 21 marzo 2026 | Acea Water Fun Run, 4.87 km in 31:51 | **27.7** | corsa sotto ritmo (FC media 160): sottostima |
| 10 maggio 2026 | Race for the Cure, 10 km in 1:10:53 | **26.6** grezzo, **~28** corretto | caldo oltre i 24°C e partenza troppo veloce |
| ottobre 2026 | nessuna gara | **~30-31** stimato | dalla soglia (6:15/km ≈ VDOT 31) e dalle 400 (2:11 ≈ VDOT 31) |

**Cosa si vede:**
- **Le due gare di primavera sottostimano.** Una era corsa sotto ritmo, l'altra col caldo. Il VDOT è affidabile quanto la gara da cui viene: la regola "gara vera, in condizioni normali" non è un dettaglio.
- **VO2max ~41 (Garmin) contro VDOT ~30.** Il motore c'è; economia e resistenza sono indietro. È il quadro tipico di chi ricomincia: il VO2max si recupera prima di tendini, economia e capacità di reggere a lungo.
- **Il piano attuale è già "a VDOT 30-31".** Le 400 (5:20-5:40/km) e il Tempo (6:10-6:30/km) cadono tra VDOT 30 e 32 nell'appendice. Il lento del piano (7:20-7:40) è invece più veloce dell'E di Daniels per VDOT 30 (7:39-8:23): per lui il lento dovrebbe essere un po' più lento. La corsa facile (7:35-8:13) è in linea.
- **La prova:** la Roma 5K dell'8 novembre. Ipotesi: 30:30-31:30, cioè VDOT 29-30. Se arriva un VDOT di 31 o più, la stima dalla soglia era giusta; se arriva sotto 29, la stima era ottimista oppure la gara non è andata come doveva.

**Limiti:** sono stime da poche gare, in condizioni diverse; la stima di ottobre non viene da una gara ma da allenamenti. Il confronto vero arriva con la Roma 5K e la 10K di dicembre.

## 6. Cosa vale per tutti

- Il VDOT è uno strumento **per allenarsi al livello di oggi**, non per prevedere il futuro. I tempi equivalenti dicono cosa è possibile **se** si è allenati per quella distanza.
- **Una gara vera vale più di qualsiasi stima** di orologi, app o allenamenti.
- Per chi ricomincia o ha poco volume: fidarsi delle equivalenze fino ai 10 km, essere prudenti sulla mezza, ancora di più sulla maratona.
- La differenza tra VO2max e VDOT è un'informazione: dice quanto c'è da guadagnare in economia e resistenza, cioè con il lento e la continuità, non con le ripetute.

## Da approfondire
- [ ] Le correzioni di Daniels per il caldo e l'altitudine (tabelle del libro)
- [ ] VDOT e età: le tabelle "age-graded" (WMA) e come confrontare un 52enne con sé stesso a 43 anni
- [ ] Il VDOT al femminile e nei principianti: cosa dicono gli studi più recenti
- [ ] Confronto VDOT, Riegel e McMillan sulle mie gare, dopo la Roma 5K e la 10K
