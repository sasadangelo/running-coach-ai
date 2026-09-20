# Training Load (CTL / ATL / TSB)

Stile TrainingPeaks, calcolato dal TSS giornaliero (somma dei TSS per attivita in training-log/week-*.md, a sua volta da NGP/IF in garmin_sync.py). Giorni senza attivita contano 0, non vengono saltati.

- **CTL** (Chronic Training Load, "fitness"): media mobile esponenziale del TSS su 42 giorni.
- **ATL** (Acute Training Load, "fatigue"): media mobile esponenziale del TSS su 7 giorni.
- **TSB** (Training Stress Balance, "form") = CTL - ATL del giorno precedente, cioe la freschezza con cui affronti la giornata, prima del suo stesso carico.
- **ACWR** (Acute:Chronic Workload Ratio) = ATL/CTL - il modo corretto di leggere il rischio dell'ATL: un ATL assoluto non dice nulla senza sapere quanto CTL c'e sotto a sostenerlo.

Fasce TSB (convenzione TrainingPeaks/Coggan): >+25 molto fresco, +5/+25 fresco, -10/+5 zona grigia, -30/-10 zona ottimale di allenamento, <-30 alto rischio.
Fasce ACWR (Gabbett): <0.8 sotto-allenato, 0.8-1.3 basso rischio, 1.3-1.5 attenzione, >1.5 rischio infortunio elevato.

**Stato attuale (2026-09-20)**: CTL 8.0 | ATL 19.1 | TSB -7.6 (zona grigia (ne fresco ne in costruzione produttiva)) | ACWR 2.40 (rischio infortunio elevato)
- Solo 27 giorni di storico su 42 necessari perche il CTL converga del tutto (~64% del transitorio) - i numeri (TSB e soprattutto ACWR, che dipende direttamente dal CTL) sono ancora in fase di costruzione: un CTL artificialmente basso gonfia l'ACWR rispetto a quello che sara una volta assestato. Non prenderli come plateau stabile.

| Data | TSS | CTL | ATL | TSB | ACWR |
| ---------- | ---: | ---: | ---: | ---: | ---: |
| 2026-08-25 | 29 | 0.7 | 4.1 | +0.0 | 6.00 |
| 2026-08-26 | 0 | 0.7 | 3.6 | -3.5 | 5.27 |
| 2026-08-27 | 32 | 1.4 | 7.6 | -2.9 | 5.36 |
| 2026-08-28 | 0 | 1.4 | 6.5 | -6.2 | 4.71 |
| 2026-08-29 | 32 | 2.1 | 10.2 | -5.1 | 4.81 |
| 2026-08-30 | 0 | 2.1 | 8.7 | -8.1 | 4.22 |
| 2026-08-31 | 0 | 2.0 | 7.5 | -6.6 | 3.71 |
| 2026-09-01 | 32 | 2.7 | 11.0 | -5.5 | 4.02 |
| 2026-09-02 | 0 | 2.7 | 9.4 | -8.2 | 3.53 |
| 2026-09-03 | 0 | 2.6 | 8.1 | -6.7 | 3.10 |
| 2026-09-04 | 44 | 3.6 | 13.2 | -5.5 | 3.68 |
| 2026-09-05 | 0 | 3.5 | 11.3 | -9.6 | 3.23 |
| 2026-09-06 | 36 | 4.3 | 14.8 | -7.8 | 3.47 |
| 2026-09-07 | 0 | 4.2 | 12.7 | -10.6 | 3.05 |
| 2026-09-08 | 36 | 4.9 | 16.0 | -8.5 | 3.25 |
| 2026-09-09 | 0 | 4.8 | 13.8 | -11.1 | 2.86 |
| 2026-09-10 | 0 | 4.7 | 11.8 | -8.9 | 2.51 |
| 2026-09-11 | 33 | 5.4 | 14.8 | -7.1 | 2.76 |
| 2026-09-12 | 0 | 5.2 | 12.7 | -9.4 | 2.42 |
| 2026-09-13 | 35 | 6.0 | 15.9 | -7.5 | 2.67 |
| 2026-09-14 | 0 | 5.8 | 13.6 | -9.9 | 2.34 |
| 2026-09-15 | 43 | 6.7 | 17.8 | -7.8 | 2.66 |
| 2026-09-16 | 0 | 6.5 | 15.3 | -11.1 | 2.34 |
| 2026-09-17 | 0 | 6.4 | 13.1 | -8.7 | 2.05 |
| 2026-09-18 | 41 | 7.2 | 17.1 | -6.7 | 2.37 |
| 2026-09-19 | 0 | 7.0 | 14.6 | -9.9 | 2.08 |
| 2026-09-20 | 46 | 8.0 | 19.1 | -7.6 | 2.40 |
