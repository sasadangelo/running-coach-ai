# Running Coach AI

Una squadra di coach AI (corsa, salute, sonno, nutrizione, ORL) che mi accompagna negli allenamenti di corsa con un obiettivo preciso: **migliorare la mia salute**. Le gare vengono dopo, come soddisfazioni in più.

Il progetto gira su [Claude Code](https://claude.com/claude-code). Ogni coach è un agente con il suo ruolo e i suoi dati; i dati arrivano da Garmin Connect, da diari in markdown e dalle mie note dopo ogni seduta.

> **Prima la salute, poi la prestazione.** Quando salute e prestazione sono in conflitto (fascia plantare, sonno, FC a riposo, HRV) vince sempre la salute.

## Da dove partire

| | |
|---|---|
| 🏃 **Il piano attuale** | [training-plan.md](training-plan.md): Roma 5K (8 novembre 2026) + Best Woman 10K (6 dicembre 2026), 14 settimane |
| 🎯 **Gli obiettivi a lungo termine** | [obiettivi-lungo-termine.md](obiettivi-lungo-termine.md): dal 5K sotto 30' alla mezza maratona, con probabilità stimate e tetti realistici |
| 📊 **La dashboard** | [dashboard.html](dashboard.html): volume, sedute, ritmi, resistenza aerobica, profilo mensile, carico di allenamento |
| 📚 **Teoria e appunti** | [teoria/](teoria/README.md): quello che imparo, usando me stesso come cavia (esperimento N=1) |

## I coach

Ogni coach è un agente (in [.claude/agents/](.claude/agents/)) con una skill che ne descrive il flusso di lavoro (in [.claude/skills/](.claude/skills/)). Si attivano con un comando o semplicemente parlando.

| Coach | Di cosa si occupa | Come si attiva |
|---|---|---|
| 🏃 **Running coach** | revisione settimanale e parere dopo ogni seduta: piano contro realtà, ritmi, FC, ripetute, volume, decisioni sul piano | `/running-coach`, "come è andata la settimana?" |
| ❤️ **Health coach** | recupero e benessere generale: FC a riposo, HRV, sintomi, se rallentare | `/health-coach`, "come sto recuperando?" |
| 😴 **Sleep coach** | durata e qualità del sonno, e come incide sull'allenamento | `/sleep-coach`, "come ho dormito?" |
| 🥗 **Nutrition coach** | valutazione iniziale, piano calorico e di macronutrienti, perdita di peso, diario alimentare | `/nutrition-coach` |
| 👂 **ORL coach** | monitoraggio della disfunzione cronica della tuba di Eustachio, udito, esercizi, e i criteri per correre | `/orl-coach` |

## Gli strumenti

| Skill | Cosa fa |
|---|---|
| [garmin-sync](.claude/skills/garmin-sync/SKILL.md) | scarica le corse da Garmin Connect in [training-log/](training-log/) (una pagina per settimana, con giri, corsa/cammino, FC, IF/TSS), la salute giornaliera in [health-log/daily-health.md](health-log/daily-health.md) e calcola tutte le metriche |
| [training-plan](.claude/skills/training-plan/SKILL.md) | crea piani personalizzati per 5K, 10K, mezza maratona e maratona |
| [training-dashboard](.claude/skills/training-dashboard/SKILL.md) | genera la dashboard HTML |

### Le metriche calcolate
Dai dati Garmin, a ogni sincronizzazione:

| Metrica | Cosa misura | Log |
|---|---|---|
| Zone FC (Karvonen) | zone aggiornate con la FC a riposo degli ultimi 7 giorni | [heart-rate-zones.md](health-log/heart-rate-zones.md) |
| Decoupling | tenuta aerobica del lungo (deriva FC/passo) | [aerobic-decoupling.md](health-log/aerobic-decoupling.md) |
| Endurance Score (ES) | resistenza aerobica dei lunghi | [endurance-score.md](health-log/endurance-score.md) |
| Capacity Score (CS) | tenuta alla soglia nei Tempo continui ≥20' | [capacity-score.md](health-log/capacity-score.md) |
| VO2max stimato | dalla relazione FC/passo (ACSM + Swain) | [vo2max.md](health-log/vo2max.md) |
| Passo di soglia | dai Tempo e dalle gare (Friel, VDOT di Daniels) | [threshold.md](health-log/threshold.md) |
| Economia di corsa | EF, meccanica (M) e RES nei lunghi | [running-economy.md](health-log/running-economy.md) |
| CTL / ATL / TSB | forma, fatica e freschezza (modello di Banister) | [training-load.md](health-log/training-load.md) |
| Profilo mensile | tutte le metriche come indice, con un radar | [monthly-profile.md](health-log/monthly-profile.md) |

Le metriche si dividono in **decisionali** (FC, decoupling, fascia plantare, sonno, FC a riposo e HRV, regolarità delle ripetute), che guidano il piano, e **di laboratorio** (le altre), da leggere come trend su 4-8 settimane e mai come base per decidere la seduta di domani.

## Struttura del progetto

```
running-coach-ai/
├── training-plan.md            # il piano attuale
├── obiettivi-lungo-termine.md  # la direzione per i piani successivi
├── dashboard.html              # la dashboard
├── training-log/               # una pagina per settimana (da Garmin)
├── coaching-log/               # le note del coach, settimana per settimana
├── health-log/                 # salute giornaliera, metriche, test di forza e mobilità, ORL
├── nutrition-log/              # profilo, misure, diario alimentare
├── teoria/                     # appunti di teoria (esperimento N=1)
└── .claude/
    ├── agents/                 # i coach
    ├── skills/                 # flussi di lavoro e script (sync Garmin, piani, dashboard)
    ├── scripts/                # zone FC, carico di allenamento
    └── training-zones.yaml     # FC max, FC a riposo, FC e passo di soglia
```

## Come si usa

**Setup (una volta):**
```bash
pip install -r .claude/skills/garmin-sync/requirements.txt
cp .claude/skills/garmin-sync/.env.sample .claude/skills/garmin-sync/.env
# poi inserire GARMIN_EMAIL e GARMIN_PASSWORD nel file .env
```

**Il ciclo di ogni settimana**, in Claude Code:
1. `/garmin-sync` dopo ogni corsa: scarica i dati, aggiorna zone e metriche.
2. Il **running coach** dà un parere sulla seduta; a fine settimana `/running-coach` per la revisione completa.
3. Quando serve, gli altri coach: sonno, salute, nutrizione, ORL.
4. `/training-dashboard` per vedere il quadro d'insieme.

## La teoria

Nella cartella [teoria/](teoria/README.md) raccolgo quello che imparo strada facendo, con un metodo preciso: **il principio, cosa dice la scienza, cosa è successo a me, cosa vale per tutti**. Le osservazioni nascono nel [registro degli esperimenti](teoria/esperimenti.md) e diventano capitoli quando sono solide:

1. [I principi dell'allenamento](teoria/01-principi-allenamento.md)
2. [Da dove viene l'energia (e perché conviene partire piano)](teoria/02-energia-partire-piano.md)
3. [La struttura di una seduta](teoria/03-struttura-seduta.md)
4. [Ritmi, zone e sedute](teoria/04-ritmi-zone-sedute.md)

## Avvertenza

Questo è un progetto personale. I coach sono strumenti AI, non medici: stime e metriche hanno margini di errore, e sintomi come dolore persistente, palpitazioni, capogiri o fastidio al petto vanno sempre valutati da un professionista.
