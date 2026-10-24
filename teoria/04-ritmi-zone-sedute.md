# Ritmi, zone e sedute

Schema di riferimento per capire ritmi, zone e sedute. Nato dalle domande del 22 ottobre 2026, da approfondire man mano. **I valori "per te oggi" sono quelli di ottobre 2026 (VDOT stimato ~30, soglia ~6:15/km, FC max 185)**: si aggiornano dopo ogni gara obiettivo o test.

## 1. I tre punti fissi: le definizioni

L'intensità della corsa è un asse continuo, ma tre punti hanno un significato fisiologico preciso e valgono per tutti. Cambia solo **dove** cadono: a che passo e a che FC.

### ① Soglia aerobica (LT1 / VT1)

**Definizione principale:** l'intensità alla quale il **lattato nel sangue comincia a salire** sopra il valore di riposo. Sotto questa soglia il lattato prodotto viene smaltito subito, l'energia arriva quasi tutta dal sistema aerobico e una buona parte dai grassi: si può correre per ore. È il **tetto del lento**.

**Varianti** (stesso concetto, misurato in modo diverso):
- **LT1 da lattato:** primo aumento stabile sopra il basale, di solito +0.5-1 mmol/L. Alcuni usano un valore fisso, **2 mmol/L** (Kindermann): comodo ma impreciso, perché il basale varia da persona a persona.
- **VT1, prima soglia ventilatoria:** misurata con i gas respiratori (CPET). È il punto in cui la ventilazione e la CO2 emessa cominciano a salire più in fretta dell'ossigeno consumato. In pratica coincide con LT1.
- **Talk test:** l'ultimo ritmo al quale si parla in frasi complete senza affanno. Soggettivo, ma ben correlato a VT1.
- **DFA alfa1 = 0.75:** un indice calcolato dalla variabilità della FC durante la corsa (serve la fascia toracica). Promettente ma ancora discusso.
- **% della FC:** ~75-82% della FC max. Solo una prima stima, con un errore individuale di ±5-10 bpm.

**Per te oggi:** ~7:15/km, FC ~150-153.

### ② Soglia anaerobica (LT2 / VT2)

**Definizione principale:** la **MLSS** (Maximal Lactate Steady State), cioè la velocità più alta alla quale il lattato resta stabile durante 30' a ritmo costante: tanto se ne produce, tanto se ne smaltisce. Sopra questa velocità il lattato si accumula e lo sforzo ha una durata limitata: chi è allenato lo regge ~60', un principiante 15-25'. È il **ritmo T**.

**Varianti:**
- **OBLA, 4 mmol/L** (Mader, Heck): la convenzione storica. Individualmente la MLSS cade tra 2 e 7 mmol/L, quindi i 4 mmol/L sono una media, non una definizione.
- **VT2, seconda soglia ventilatoria** (o punto di compensazione respiratoria): al CPET, il punto in cui il respiro accelera per eliminare la CO2 in eccesso.
- **Velocità critica:** ricavata da 2-3 prove massimali di durata diversa. Cade un po' sopra la MLSS.
- **FC di soglia (Friel):** la FC media degli ultimi 20' di un test di 30' al massimo.
- **Ritmo T di Daniels:** il ritmo che un atleta allenato terrebbe in gara per ~60', ≈88% del VDOT.
- **% della FC:** ~85-90% della FC max.

**Per te oggi:** ~6:15/km, FC ~165. Come misurarla: sezione 7.

### ③ VO2max e vVO2max

**VO2max:** il **consumo massimo di ossigeno** (ml/kg/min). In un test a velocità crescente è il punto in cui il consumo di ossigeno smette di salire anche se la velocità aumenta. È il "motore" e dipende da cuore, sangue, capillari e mitocondri.

**vVO2max** (Billat): la **velocità più bassa alla quale si raggiunge il VO2max**. Si regge 4-8' ed è il riferimento delle ripetute lunghe.

**Varianti e stime:**
- **CPET:** l'unica misura vera. Dà anche la FC max reale e le due soglie ventilatorie.
- **VDOT di Daniels:** una stima ricavata da una gara. Non misura il motore ma quanto del motore arriva in strada, quindi include economia di corsa e resistenza (sezione 8).
- **Stima del dispositivo (Garmin):** calcolata da FC e passo. Utile come andamento, non come valore assoluto.
- **Test da campo** (es. Cooper, 12' al massimo): dipendono molto dal pacing e dalla motivazione.

**Per te oggi:** VO2max ~41 (Garmin), vVO2max ~5:50/km (stima dal VDOT).

## 2. I ritmi: le zone tra i punti fissi

```
 INTENSITÀ        ZONA            DANIELS  SCUOLA ITALIANA     PER TE OGGI    FC
 ▲
 │ ░░░░░░░░░░   Velocità             R     ripetute brevi      5:20-5:40      (non conta)
 │━━━━━━━━━━━━━━━━ ③ vVO2max ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 │ ▓▓▓▓▓▓▓▓▓▓   VO2max               I     ripetute lunghe     ~5:55          175-180+
 │ ▓▓▓▓▓▓▓▓▓▓   (sopra soglia)       —     corto veloce*       6:00-6:05      168-175
 │━━━━━━━━━━━━━━━━ ② SOGLIA ANAEROBICA (LT2/VT2, ~4 mmol) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 │ ▒▒▒▒▒▒▒▒▒▒   Soglia               T     soglia / Tempo      6:05-6:25      160-168
 │ ▒▒▒▒▒▒▒▒▒▒   Medio                M     medio               6:45-7:05      153-160
 │━━━━━━━━━━━━━━━━ ① SOGLIA AEROBICA (LT1/VT1, ~2 mmol) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 │ ··········   Lento                E     lento / lungo       7:20-7:40      138-150
 │ ··········   Recupero             E     rigenerante         >7:55          <138
 └───────────────────────────────────────────────────────────────────────────────────────────────
```

- **Le linee spesse sono fisiologia** e valgono per tutti. **Le fasce tra le linee sono le zone di allenamento.**
- I nomi delle scuole sono etichette diverse per le stesse fasce.
- \* Il **corto veloce** è il ritmo gara 10K: dove cade dipende dal livello (vedi sezione 3).
- **Per lento e recupero comanda la FC**, non il passo (caldo, sonno, fatica alzano la FC a parità di passo). Per soglia e medio il passo è l'obiettivo, la FC il tetto. Nelle ripetute brevi la FC non arriva a regime: contano passo e sensazione.

### Sotto la soglia aerobica

| Zona | Altri nomi | Per te oggi | A cosa serve |
|---|---|---|---|
| **Recupero** | rigenerante, defaticamento; Daniels: parte bassa di **E**, "recovery run"; Garmin Z1-Z2 bassa | >7:55, FC <138 | recupero attivo dopo le sedute dure, riscaldamento, defaticamento |
| **Lento** | fondo lento, lungo; Daniels: **E (Easy)** e **L (Long run)** allo stesso ritmo; Garmin Z2 | 7:20-7:40, FC 138-150 | base aerobica, capillari, mitocondri, tendini. È la gran parte del volume |

Il recupero è **più lento ancora** del lento: non serve ad allenare, serve a muovere le gambe senza aggiungere fatica.

### Tra le due soglie

| Zona | Altri nomi | Per te oggi | A cosa serve |
|---|---|---|---|
| **Medio** | fondo medio; Daniels: **M (Marathon pace)**; Garmin Z3 | 6:45-7:05, FC 153-160 | resistenza a ritmo sostenuto, specifico per mezza e maratona |
| **Soglia** | Tempo, corsa in soglia; Daniels: **T (Threshold)**; Garmin Z3 alta-Z4 | 6:05-6:25, FC 160-168 | alzare la soglia anaerobica, cioè il ritmo che si regge a lungo |

Il ritmo T sta **appena sotto o sulla** linea della soglia anaerobica, non a metà tra le due soglie.

**Daniels distingue due forme di lavoro a ritmo T:**
- **Tempo run (continuo):** ~20' di fila a ritmo T. Allena anche la tenuta mentale.
- **Cruise intervals (a frazioni):** frazioni da 5-15' a ritmo T con un recupero breve, circa 1' ogni 5' di lavoro (es. 3 x 1600 con 1'). Il recupero corto non fa scendere troppo la FC, quindi lo stimolo è lo stesso del continuo. In compenso il volume totale in soglia può essere più alto e la seduta pesa meno. È la forma adatta a chi non regge ancora 20' continui: nel piano, i 3x800 e i 2x1500 delle settimane 5-7, prima del Tempo continuo dalla settimana 9.

### Sopra la soglia anaerobica

| Zona | Altri nomi | Per te oggi | A cosa serve |
|---|---|---|---|
| **Corto veloce** | scuola italiana (es. Pizzolato); in inglese "10K pace"; Daniels: nessuna lettera, sta tra T e I | 6:00-6:05, FC 168-175 | specifico per 5-10K: abituarsi al ritmo gara |
| **Ripetute lunghe** | ripetute da 800-2000 m; Daniels: **I (Interval)**; Garmin Z4-Z5 | ~5:55, FC 175-180+ | il VO2max: più tempo possibile vicino al massimo consumo di ossigeno |

**Corto veloce e I di Daniels non sono la stessa cosa.** L'I di Daniels è il ritmo di 10-12' di gara, cioè circa il ritmo dei 3000 m. Il corto veloce è il ritmo del 10K: più lento, con frazioni più lunghe o in continuo. Per i runner lenti il corto veloce quasi coincide con la soglia (sezione 3).

### Sopra la vVO2max

| Zona | Altri nomi | Per te oggi | A cosa serve |
|---|---|---|---|
| **Velocità** | ripetute brevi (200-400 m), allunghi; Daniels: **R (Repetition)** | 5:20-5:40 | velocità, economia di corsa, tecnica. Si fanno con recupero completo |

### Altri modelli a zone, per orientarsi
- **Garmin, 5 zone sulla FC** (le tue, metodo Karvonen): Z1 120-134, Z2 134-153, Z3 153-166, Z4 166-176, Z5 >176. Sono fasce di FC, non legate direttamente alle soglie: il tetto di Z2 (153) cade vicino alla soglia aerobica, quello di Z3 (166) vicino alla soglia anaerobica, ma per te è una coincidenza.
- **Seiler, 3 zone:** zona 1 sotto LT1, zona 2 tra LT1 e LT2, zona 3 sopra LT2. **Attenzione: la "zona 2" di Seiler (medio e soglia) non è la Z2 di Garmin (lento).** È la confusione più comune nei libri sul polarizzato.

## 3. La regola: ogni ritmo è il ritmo di una gara di una certa durata

| Sforzo massimo sostenibile per... | Ritmo | Per te oggi |
|---|---|---|
| 5-8' (il miglio) | **R** | ~5:35 |
| 10-12' | **I** (VO2max) | ~5:55 |
| ~60' | **T** (soglia) | ~6:15 |
| 2-4 ore | **M** (maratona) | ~6:50 |
| ore, senza fatica | **E** (lento) | ~7:30 |

Regola pratica di Daniels: ogni gradino (T → I → R) è più veloce di ~6"/400 m, cioè ~15"/km; per i runner più lenti lo scarto è un po' più ampio (oggi: T → I −20"/km, I → R −15/20"/km).

**Cosa spiega la regola:**
- **Corto veloce vs Tempo:** il corto veloce è il ritmo del 10K. Se il tuo 10K dura ~60' coincide con la soglia (tu oggi, 10K ~63'); più sei veloce, più il 10K dura meno di un'ora e il suo ritmo sale sopra la soglia (runner da 40': +10-15"/km sopra T).
- **Caselle vuote nelle tabelle di Daniels:** una frazione R non deve superare ~2', una I ~5'. Con VDOT bassi certe distanze durerebbero troppo (es. 1600 a ritmo I ≈ 9'30" per te) e diventerebbero soglia: per quel livello non si fanno. Per questo il 1600 è stato tolto dal piano l'11 ottobre.
- **La soglia del principiante:** esiste anche se non sa tenerla 60'. La definizione "a durata" vale solo per chi ha la resistenza strutturale; il principiante ha la soglia più in basso (50-65% del VO2max contro 80-90% di un allenato) e la regge 15-25'.

## 4. Una seduta = tre parametri

> **seduta = zona × durata della frazione × recupero**

| Seduta | Zona | Frazione | Recupero | Allena |
|---|---|---|---|---|
| 200-400 | R | ≤2' | completo, camminato (2-3× la frazione) | velocità, economia, tecnica |
| 800 | I | 3-5' | jog, ~uguale alla frazione | VO2max |
| 2×1500 (cruise intervals) | T | 5-10' | breve, jog (1' ogni 5' di lavoro) | soglia |
| Tempo continuo | T | 12-20' | — | soglia |
| Medio | M | 30-60' | — | resistenza a ritmo sostenuto (mezza, maratona) |
| Lungo | E | 45'+ | — | base aerobica, capillari, tendini |

Il nome conta poco: ogni allenamento (libro, video, piano) si riconduce a queste tre coordinate.

**Volumi massimi per seduta (Daniels), in proporzione ai km settimanali:** R ~5%, I ~8%, T ~10%. Con volumi bassi si superano facilmente: è uno dei motivi per cui il piano attuale è "intenso in proporzione".

## 5. I recuperi: da fermi, camminando o corricchiando

| Lavoro | Obiettivo | Recupero |
|---|---|---|
| Corti e veloci (sprint, R) | ogni frazione "fresca" | completo, da fermi o camminando. Da fermi si ricarica meglio la fosfocreatina; con 30-60" di recupero il jog non dà vantaggi |
| Intervalli lunghi (I) | tempo al VO2max | corricchiato: il consumo di ossigeno resta alto e la frazione successiva arriva prima al VO2max |
| Soglia a frazioni (T) | tempo in soglia | breve e corricchiato: smaltisce il lattato |

Evitare di stare **completamente fermi per 2'**: la FC crolla e le gambe si irrigidiscono. Meglio camminare.

## 6. Ripetute, interval training e altri nomi

- **"Ripetute"** (italiano) e **"interval training"** (senso largo): qualsiasi alternanza di lavoro e recupero.
- **Daniels** usa i nomi in senso stretto: **Repetition (R)** = frazioni corte veloci con recupero completo (velocità/economia); **Interval (I)** = frazioni di 3-5' al VO2max con recupero jog.
- Le 400 del martedì (~2:11) sono **R**, non intervalli veri: troppo corte per arrivare al VO2max. Gli 800 (~4:40) sono **I**.
- **Medio** e **Tempo** sono sedute diverse: il medio sta tra le due soglie (30-60', "impegnato ma comodo"), il Tempo alla soglia anaerobica (20', "comodamente duro"). In inglese "tempo run" è usato anche in senso generico.
- In primavera 2026 quasi tutte le corse erano a ritmo **medio** senza volerlo (6:50-7:00, FC ~155): la "zona grigia", troppo veloce per la base e troppo lenta per la soglia.

## 7. Come misurare la soglia anaerobica

Definizioni e varianti sono nella sezione 1. Qui i metodi pratici.

| Metodo | Come | Limiti | Adatto a |
|---|---|---|---|
| **MLSS** (lab) | 3-5 corse da 30' a velocità costante, lattato | gold standard, lungo e costoso | — |
| **Lattato a gradini** (lab) | velocità crescente, prelievo a ogni gradino; lettura a 4 mmol, +1 mmol sul basale, Dmax | il risultato dipende da protocollo e lettura | — |
| **CPET** (lab) | gas respiratori: VT1 e VT2 | ottimo; dà anche **VO2max e FC max reali** | tutti, come calibrazione |
| **Lattacidometro portatile** | prelievo al dito sul campo | ~300€ più le strisce, protocollo rigoroso | medi/evoluti appassionati |
| **Test dei 30' (Friel)** | 30' al massimo; FC media ultimi 20' = FC di soglia | bisogna reggere 30' e saperli dosare | medi/evoluti |
| **Gara + VDOT (Daniels)** | T ≈ 88% del VDOT | sottostima con poca resistenza, caldo o pacing sbagliato | evoluti, medi con riserva |
| **Velocità critica** | 2 prove (es. 3' e 9'), relazione distanza-tempo | un po' sopra la MLSS | medi/evoluti |
| **% FC** | 85-90% FC max, ~80-88% FC di riserva | valida solo con FC max vera; ±5-10 bpm individuali | tutti, prima stima |
| **Talk test / RPE** | "frasi brevi, non un discorso", ~7/10 | soggettivo ma sorprendentemente valido | principianti |
| **Stima del dispositivo** (Garmin) | algoritmo su FC, HRV, passo | scatola nera, spesso ottimista | curiosità |
| **Analisi allenamenti** (script) | passo a FC di soglia nei tratti stabili | dipende dalla FC di soglia; ottimista sulle frazioni brevi | tutti, come trend |
| **Test di Conconi** | flessione della FC | screditato | — |

**Per livello:** principiante → talk test, % FC, soglia allenata a frazioni (test e gare sottostimano). Medio → test dei 30', gare 5-10K, velocità critica. Evoluto → gare 10K-mezza, test, laboratorio: i metodi convergono.

**Triangolazione attuale:** Friel dalla Race for the Cure 166 (col caldo, probabilmente alta); script 165 e ~6:15/km; Garmin 173 e 6:04 (ottimista); 85-90% di 185 = 157-167. Verifiche: test continuo 2000 m di S9 (con la fascia), Roma 5K, CPET dopo la 10K.

## 8. VO2max e VDOT

- **VO2max** = il motore (ossigeno massimo utilizzabile). **VDOT** = quanto del motore arriva in strada (include economia e resistenza). Oggi VO2max ~41 contro VDOT ~30: il motore c'è, economia e resistenza sono indietro. Tutto sul VDOT nel capitolo [06](06-vdot.md), tabelle nell'[appendice A](appendice-a-tabelle-vdot.md).
- Il VO2max si muove in mesi; soglia ed EF in 4-6 settimane; resistenza (ES, decoupling) in settimane.

## Da approfondire
- [ ] Economia di corsa: cadenza, contatto al suolo, rapporto verticale e cosa si può allenare
- [ ] Polarizzato vs piramidale: come distribuire l'intensità (80/20 e varianti)
- [ ] Allenamento in salita: perché funziona e come dosarlo
- [ ] Caldo e prestazione: quanto pesa e come adattarsi
- [ ] Corto veloce nella scuola italiana: distanze e ritmi esatti nei testi di Pizzolato e Arcelli (da verificare sui libri)
