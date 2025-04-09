# TSoN - Trading Strategy Optimizer & Backtester

TSoN è un simulatore per il **backtesting sistematico** di strategie di trading su coppie di valute. Fornisce un'analisi esaustiva di combinazioni Take Profit / Stop Loss su dati storici, con l'obiettivo di identificare parametri ottimali per il profitto.

## 🚀 Funzionalità principali

- Lettura di dati storici da file CSV
- Simulazione di trade con TP/SL variabili
- Griglia automatica di combinazioni TP/SL
- Calcolo dei risultati economici per ogni combinazione
- Supporto per:
  - Capitale iniziale e capitale per trade
  - Fee di transazione
  - Periodicità dei trade
  - Uscita dal trade (a fine finestra o su chiusura)
  - Modalità hedge (long/short multipli)

## 📦 Compilazione

```bash
make
```

Richiede un compilatore C++11 o superiore.

## 🧪 Esecuzione

```bash
./simulatore_trading data/DAT_ASCII_GBPJPY_M1_2021.csv   -W 6000 -PER 10   -TPmin 10 -TPmax 30  -SLmin 0.3 -SLmax 0.4 -P 5  -C 10000 -CPT 70 -FEE 0.1  -exit_mode close -OH
```

### Parametri

| Parametro     | Descrizione |
|---------------|-------------|
| `dati.csv`    | File CSV con i dati (timestamp, open, high, low, close) |
| `-W`          | Finestra temporale in minuti per ogni trade |
| `-TPmin`/`-TPmax` | Range minimo/massimo di Take Profit |
| `-SLmin`/`-SLmax` | Range minimo/massimo di Stop Loss |
| `-P`          | Numero di punti nella griglia TP/SL |
| `-C`          | Capitale iniziale |
| `-CPT`        | Capitale per singolo trade |
| `-FEE`        | Fee percentuale per ogni trade |
| `-PER`        | Intervallo tra un trade e il successivo (in minuti) |
| `-exit_mode`  | Modalità di uscita: `close` (chiude la posizione così com'è alla fine della finestra) o `leave` (la posizione rimane aperta alla fine della finestra) |
| `-OH`         | Only Hedge, non stampa le righe relative ai LONG e agli SHORT |
| `-debug`      | Mostra dettagli interni di simulazione |


## 📁 Struttura del progetto

```
TSoN/
├── src/
│   ├── dataloader.hpp    # Funzioni per caricare e parsare il file CSV dei dati storici
│   ├── main.cpp          # Entry point del programma, gestisce gli argomenti e la simulazione
│   ├── simulator.hpp     # Funzioni di simulazione dei trade e calcolo dei risultati
│   ├── structures.hpp    # Strutture dati principali (candela, trade, risultati, ecc.)
│   ├── tools.hpp         # Funzioni di utilità, generazione griglie TP/SL, output
│
├── Makefile              # Script per la compilazione del progetto
├── .gitignore            # File per escludere build/artifacts da Git
├── esempiorun            # Esempio di comando per avviare una simulazione
```


## 📌 TODO futuri

- Esportazione risultati in CSV
- Multithreading
- Supporto a trailing stop
- Integrazione con dati live
- Web UI con dashboard interattiva

## 📜 Licenza

MIT License

Copyright (c) 2025 Alberto Stabile

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction...


