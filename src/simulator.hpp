#pragma once
#include "dataloader.hpp"
#include <vector>

// Struttura che tiene traccia dei risultati di una strategia di trading
struct TradeResult {
    double ricavi = 0.0;      // Profitti totali
    double perdite = 0.0;     // Perdite totali
    double fee_totali = 0.0;  // Commissioni totali
    int successi = 0;         // Numero di trade in profitto
    int fallimenti = 0;       // Numero di trade in perdita
    int non_chiusi = 0;       // Numero di trade non chiusi
    double percent_success = 0.0;  // Percentuale di successo
};

// Struttura che rappresenta una posizione di trading
struct Position {
    double open_price;    // Prezzo di apertura della posizione
    double target_tp;     // Livello di take profit
    double target_sl;     // Livello di stop loss
    bool is_long;         // true se posizione long, false se short
};

// Funzioni di supporto
Position calculate_position(const Candela& candle, double tp, double sl, bool is_long);
bool check_exit_conditions(const std::vector<Candela>& dati, size_t start_idx, size_t window, 
                         const Position& pos, bool& hit_tp, bool& hit_sl);
void handle_trade_result(TradeResult& result, double& capitale, double capitale_per_trade, 
                        double fee, double profit_pct, bool is_profit);
void handle_timeout_exit(TradeResult& result, double& capitale, double capitale_per_trade,
                        double fee, const Candela& exit_candle, const Position& pos);

// Funzione principale di simulazione
TradeResult simulate_strategy(const std::vector<Candela>& dati, size_t finestra,
                            double capitale_per_trade, double fee, int periodo,
                            bool EXIT_MODE_CLOSE, double& capitale, double tp, double sl, bool is_long);

// Funzione principale che simula strategie di trading con diversi parametri
void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE, 
            double capitale_iniziale, bool only_hedge);
