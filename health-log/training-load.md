# Training Load (CTL / ATL / TSB)

Stile TrainingPeaks, calcolato dal TSS giornaliero (somma dei TSS per attivita in training-log/week-*.md, a sua volta da NGP/IF in garmin_sync.py). Giorni senza attivita contano 0, non vengono saltati.

- **CTL** (Chronic Training Load, "fitness"): media mobile esponenziale del TSS su 42 giorni.
- **ATL** (Acute Training Load, "fatigue"): media mobile esponenziale del TSS su 7 giorni.
- **TSB** (Training Stress Balance, "form") = CTL - ATL del giorno precedente, cioe la freschezza con cui affronti la giornata, prima del suo stesso carico.
- **ACWR** (Acute:Chronic Workload Ratio) = ATL/CTL - il modo corretto di leggere il rischio dell'ATL: un ATL assoluto non dice nulla senza sapere quanto CTL c'e sotto a sostenerlo.

Fasce TSB (convenzione TrainingPeaks/Coggan): >+25 molto fresco, +5/+25 fresco, -10/+5 zona grigia, -30/-10 zona ottimale di allenamento, <-30 alto rischio.
Fasce ACWR (Gabbett): <0.8 sotto-allenato, 0.8-1.3 basso rischio, 1.3-1.5 attenzione, >1.5 rischio infortunio elevato.
Il rischio si valuta solo dopo 42 giorni di storico, quando il CTL si e assestato: prima l'ACWR e gonfiato da un CTL artificialmente basso. Con 3 sedute a settimana l'ACWR sale nei giorni di seduta e scende nei giorni di riposo: conta la tendenza, non il singolo picco.

**Stato attuale (2026-11-01)**: CTL 17.5 | ATL 25.3 | TSB -2.6 (zona grigia (ne fresco ne in costruzione produttiva)) | ACWR 1.44 (fascia di attenzione)

| Data | TSS | CTL | ATL | TSB | ACWR | Rischio |
| ---------- | ---: | ---: | ---: | ---: | ---: | --- |
| 2026-08-25 | 31 | 0.7 | 4.4 | +0.0 | 6.00 | - |
| 2026-08-26 | 0 | 0.7 | 3.8 | -3.7 | 5.27 | - |
| 2026-08-27 | 34 | 1.5 | 8.1 | -3.1 | 5.36 | - |
| 2026-08-28 | 0 | 1.5 | 7.0 | -6.6 | 4.71 | - |
| 2026-08-29 | 34 | 2.3 | 10.8 | -5.5 | 4.80 | - |
| 2026-08-30 | 0 | 2.2 | 9.3 | -8.6 | 4.22 | - |
| 2026-08-31 | 0 | 2.1 | 7.9 | -7.1 | 3.70 | - |
| 2026-09-01 | 34 | 2.9 | 11.7 | -5.8 | 4.02 | - |
| 2026-09-02 | 0 | 2.8 | 10.0 | -8.8 | 3.53 | - |
| 2026-09-03 | 0 | 2.8 | 8.6 | -7.2 | 3.10 | - |
| 2026-09-04 | 46 | 3.8 | 13.9 | -5.8 | 3.67 | - |
| 2026-09-05 | 0 | 3.7 | 11.9 | -10.1 | 3.22 | - |
| 2026-09-06 | 38 | 4.5 | 15.7 | -8.2 | 3.46 | - |
| 2026-09-07 | 0 | 4.4 | 13.4 | -11.1 | 3.04 | - |
| 2026-09-08 | 38 | 5.2 | 16.9 | -9.0 | 3.25 | - |
| 2026-09-09 | 0 | 5.1 | 14.5 | -11.7 | 2.85 | - |
| 2026-09-10 | 0 | 5.0 | 12.4 | -9.4 | 2.50 | - |
| 2026-09-11 | 35 | 5.7 | 15.7 | -7.5 | 2.76 | - |
| 2026-09-12 | 0 | 5.5 | 13.4 | -10.0 | 2.42 | - |
| 2026-09-13 | 37 | 6.3 | 16.8 | -7.9 | 2.67 | - |
| 2026-09-14 | 0 | 6.1 | 14.4 | -10.5 | 2.34 | - |
| 2026-09-15 | 47 | 7.1 | 19.1 | -8.2 | 2.68 | - |
| 2026-09-16 | 0 | 7.0 | 16.3 | -11.9 | 2.35 | - |
| 2026-09-17 | 0 | 6.8 | 14.0 | -9.4 | 2.06 | - |
| 2026-09-18 | 44 | 7.7 | 18.3 | -7.2 | 2.38 | - |
| 2026-09-19 | 0 | 7.5 | 15.7 | -10.6 | 2.09 | - |
| 2026-09-20 | 48 | 8.5 | 20.3 | -8.2 | 2.40 | - |
| 2026-09-21 | 0 | 8.3 | 17.4 | -11.8 | 2.11 | - |
| 2026-09-22 | 44 | 9.1 | 21.2 | -9.1 | 2.33 | - |
| 2026-09-23 | 0 | 8.9 | 18.2 | -12.1 | 2.04 | - |
| 2026-09-24 | 0 | 8.7 | 15.6 | -9.3 | 1.79 | - |
| 2026-09-25 | 32 | 9.2 | 17.9 | -6.9 | 1.94 | - |
| 2026-09-26 | 0 | 9.0 | 15.4 | -8.7 | 1.70 | - |
| 2026-09-27 | 32 | 9.6 | 17.7 | -6.3 | 1.86 | - |
| 2026-09-28 | 0 | 9.3 | 15.2 | -8.2 | 1.63 | - |
| 2026-09-29 | 54 | 10.4 | 20.7 | -5.9 | 2.00 | - |
| 2026-09-30 | 0 | 10.1 | 17.8 | -10.4 | 1.75 | - |
| 2026-10-01 | 0 | 9.9 | 15.2 | -7.6 | 1.54 | - |
| 2026-10-02 | 48 | 10.8 | 19.9 | -5.3 | 1.84 | - |
| 2026-10-03 | 0 | 10.6 | 17.1 | -9.1 | 1.62 | - |
| 2026-10-04 | 53 | 11.6 | 22.2 | -6.5 | 1.92 | - |
| 2026-10-05 | 0 | 11.3 | 19.0 | -10.6 | 1.69 | rischio infortunio elevato |
| 2026-10-06 | 63 | 12.5 | 25.3 | -7.7 | 2.02 | rischio infortunio elevato |
| 2026-10-07 | 0 | 12.2 | 21.7 | -12.8 | 1.78 | rischio infortunio elevato |
| 2026-10-08 | 0 | 11.9 | 18.6 | -9.5 | 1.56 | rischio infortunio elevato |
| 2026-10-09 | 46 | 12.7 | 22.5 | -6.7 | 1.77 | rischio infortunio elevato |
| 2026-10-10 | 0 | 12.4 | 19.3 | -9.8 | 1.55 | rischio infortunio elevato |
| 2026-10-11 | 60 | 13.6 | 25.1 | -6.9 | 1.85 | rischio infortunio elevato |
| 2026-10-12 | 0 | 13.2 | 21.5 | -11.5 | 1.62 | rischio infortunio elevato |
| 2026-10-13 | 68 | 14.6 | 28.2 | -8.3 | 1.94 | rischio infortunio elevato |
| 2026-10-14 | 0 | 14.2 | 24.1 | -13.6 | 1.70 | rischio infortunio elevato |
| 2026-10-15 | 0 | 13.9 | 20.7 | -9.9 | 1.49 | fascia di attenzione |
| 2026-10-16 | 52 | 14.8 | 25.2 | -6.8 | 1.70 | rischio infortunio elevato |
| 2026-10-17 | 0 | 14.4 | 21.6 | -10.4 | 1.50 | fascia di attenzione |
| 2026-10-18 | 57 | 15.4 | 26.6 | -7.1 | 1.73 | rischio infortunio elevato |
| 2026-10-19 | 0 | 15.1 | 22.8 | -11.2 | 1.51 | rischio infortunio elevato |
| 2026-10-20 | 56 | 16.0 | 27.6 | -7.8 | 1.72 | rischio infortunio elevato |
| 2026-10-21 | 0 | 15.7 | 23.6 | -11.5 | 1.51 | rischio infortunio elevato |
| 2026-10-22 | 0 | 15.3 | 20.3 | -8.0 | 1.32 | fascia di attenzione |
| 2026-10-23 | 37 | 15.8 | 22.6 | -5.0 | 1.43 | fascia di attenzione |
| 2026-10-24 | 0 | 15.4 | 19.4 | -6.8 | 1.26 | fascia a basso rischio |
| 2026-10-25 | 34 | 15.9 | 21.5 | -4.0 | 1.35 | fascia di attenzione |
| 2026-10-26 | 0 | 15.5 | 18.4 | -5.6 | 1.19 | fascia a basso rischio |
| 2026-10-27 | 81 | 17.1 | 27.4 | -2.9 | 1.60 | rischio infortunio elevato |
| 2026-10-28 | 0 | 16.6 | 23.5 | -10.3 | 1.41 | fascia di attenzione |
| 2026-10-29 | 40 | 17.2 | 25.8 | -6.8 | 1.50 | rischio infortunio elevato |
| 2026-10-30 | 0 | 16.8 | 22.1 | -8.6 | 1.32 | fascia di attenzione |
| 2026-10-31 | 0 | 16.4 | 19.0 | -5.3 | 1.16 | fascia a basso rischio |
| 2026-11-01 | 63 | 17.5 | 25.3 | -2.6 | 1.44 | fascia di attenzione |
