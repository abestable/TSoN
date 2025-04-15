#include "simulator.hpp"
#include "printer.hpp"
#include <iostream>
#include <iomanip>

extern bool DEBUG;

/**
 * @brief Struttura che tiene traccia dei risultati di una strategia di trading
 * Contiene tutte le metriche di performance come ricavi, perdite, successi, ecc.
 */
struct TradeResult {
    double ricavi = 0.0;      // Profitti totali
    double perdite = 0.0;     // Perdite totali
    double fee_totali = 0.0;  // Commissioni totali
    int successi = 0;         // Numero di trade in profitto
    int fallimenti = 0;       // Numero di trade in perdita
    int non_chiusi = 0;       // Numero di trade non chiusi
    double percent_success = 0.0;  // Percentuale di successo
};

/**
 * @brief Struttura che rappresenta una posizione di trading
 * Contiene i prezzi di apertura e i livelli di take profit e stop loss
 */
struct Position {
    double open_price;    // Prezzo di apertura della posizione
    double target_tp;     // Livello di take profit
    double target_sl;     // Livello di stop loss
    bool is_long;         // true se posizione long, false se short
};

/**
 * @brief Calcola i livelli di take profit e stop loss per una posizione
 * @param candle Candela di apertura della posizione
 * @param tp Percentuale di take profit
 * @param sl Percentuale di stop loss
 * @param is_long Tipo di posizione (true = long, false = short)
 * @return Position con i livelli calcolati
 */
Position calculate_position(const Candela& candle, double tp, double sl, bool is_long) {
    double open = candle.open;
    double target_tp = is_long ? open * (1.0 + tp / 100.0) : open * (1.0 - tp / 100.0);
    double target_sl = is_long ? open * (1.0 - sl / 100.0) : open * (1.0 + sl / 100.0);
    return {open, target_tp, target_sl, is_long};
}

/**
 * @brief Verifica se una posizione ha raggiunto i livelli di take profit o stop loss
 * @param dati Lista delle candele
 * @param start_idx Indice di partenza
 * @param window Finestra di tempo da controllare
 * @param pos Posizione da verificare
 * @param hit_tp Output: true se take profit raggiunto
 * @param hit_sl Output: true se stop loss raggiunto
 * @return true se uno dei livelli è stato raggiunto, false altrimenti
 */
bool check_exit_conditions(const std::vector<Candela>& dati, size_t start_idx, size_t window, 
                         const Position& pos, bool& hit_tp, bool& hit_sl) {
    for (size_t j = 1; j <= window; ++j) {
        if (pos.is_long) {
            if (dati[start_idx + j].high >= pos.target_tp) { hit_tp = true; return true; }
            if (dati[start_idx + j].low <= pos.target_sl)  { hit_sl = true; return true; }
        } else {
            if (dati[start_idx + j].low <= pos.target_tp)  { hit_tp = true; return true; }
            if (dati[start_idx + j].high >= pos.target_sl) { hit_sl = true; return true; }
        }
    }
    return false;
}

/**
 * @brief Gestisce il risultato di un trade (profitto o perdita)
 * @param result Struttura dove salvare i risultati
 * @param capitale Capitale disponibile (viene aggiornato)
 * @param capitale_per_trade Capitale investito per trade
 * @param fee Percentuale di commissione
 * @param profit_pct Percentuale di profitto/perdita
 * @param is_profit true se il trade è in profitto
 */
void handle_trade_result(TradeResult& result, double& capitale, double capitale_per_trade, 
                        double fee, double profit_pct, bool is_profit) {
    double fee_val = capitale_per_trade * fee;
    double amount = capitale_per_trade * profit_pct / 100.0;
    
    if (is_profit) {
        result.ricavi += amount;
        result.successi++;
        capitale += (amount - fee_val);
    } else {
        result.perdite += amount;
        result.fallimenti++;
        capitale -= (amount + fee_val);
    }
    result.fee_totali += fee_val;
}

/**
 * @brief Gestisce la chiusura di una posizione per timeout
 * @param result Struttura dove salvare i risultati
 * @param capitale Capitale disponibile (viene aggiornato)
 * @param capitale_per_trade Capitale investito per trade
 * @param fee Percentuale di commissione
 * @param exit_candle Candela di chiusura
 * @param pos Posizione da chiudere
 */
void handle_timeout_exit(TradeResult& result, double& capitale, double capitale_per_trade,
                        double fee, const Candela& exit_candle, const Position& pos) {
    double variazione = pos.is_long
        ? (exit_candle.close - pos.open_price) / pos.open_price
        : (pos.open_price - exit_candle.close) / pos.open_price;
    
    double fee_val = capitale_per_trade * fee;
    result.fee_totali += fee_val;
    
    if (variazione > 0) {
        double profit = capitale_per_trade * variazione;
        result.ricavi += profit;
        capitale += (profit - fee_val);
        result.successi++;
    } else {
        double loss = capitale_per_trade * (-variazione);
        result.perdite += loss;
        capitale -= (loss + fee_val);
        result.fallimenti++;
    }
}

/**
 * @brief Simula una strategia di trading con parametri specifici
 * @param dati Lista delle candele
 * @param finestra Finestra di tempo per ogni trade
 * @param capitale_per_trade Capitale investito per trade
 * @param fee Percentuale di commissione
 * @param periodo Periodo tra i trade
 * @param EXIT_MODE_CLOSE Se true, chiude le posizioni alla fine della finestra
 * @param capitale Capitale disponibile (viene aggiornato)
 * @param tp Percentuale di take profit
 * @param sl Percentuale di stop loss
 * @param is_long Tipo di strategia (true = long, false = short)
 * @return TradeResult con i risultati della simulazione
 */
TradeResult simulate_strategy(const std::vector<Candela>& dati, size_t finestra,
                            double capitale_per_trade, double fee, int periodo,
                            bool EXIT_MODE_CLOSE, double& capitale, double tp, double sl, bool is_long) {
    TradeResult result;
    
    // Itera attraverso i dati con il periodo specificato
    for (size_t i = 0; i + finestra < dati.size(); i += periodo) {
        // Verifica se c'è capitale sufficiente per aprire una posizione
        if (capitale <= capitale_per_trade + 1) break;
        
        // Calcola i livelli per la nuova posizione
        Position pos = calculate_position(dati[i], tp, sl, is_long);
        bool hit_tp = false, hit_sl = false;
        
        // Verifica se la posizione raggiunge TP o SL
        if (!check_exit_conditions(dati, i, finestra, pos, hit_tp, hit_sl)) {
            if (EXIT_MODE_CLOSE) {
                // Chiude la posizione alla fine della finestra
                handle_timeout_exit(result, capitale, capitale_per_trade, fee, dati[i + finestra], pos);
            } else {
                result.non_chiusi++;
            }
            continue;
        }
        
        // Gestisce il risultato del trade (TP o SL)
        handle_trade_result(result, capitale, capitale_per_trade, fee, 
                          hit_tp ? tp : sl, hit_tp);
    }
    
    // Calcola la percentuale di successo
    double totale = result.successi + result.fallimenti + result.non_chiusi;
    result.percent_success = totale > 0 ? 100.0 * result.successi / totale : 0.0;
    
    return result;
}

/**
 * @brief Funzione principale che simula strategie di trading con diversi parametri
 * @param tp_list Lista dei take profit da testare
 * @param sl_list Lista degli stop loss da testare
 * @param dati Dati storici (candele)
 * @param finestra Finestra di tempo per ogni trade
 * @param capitale_per_trade Capitale investito per trade
 * @param fee Percentuale di commissione
 * @param periodo Periodo tra i trade
 * @param EXIT_MODE_CLOSE Se true, chiude le posizioni alla fine della finestra
 * @param capitale_iniziale Capitale iniziale
 * @param only_hedge Se true, mostra solo i risultati della strategia hedge
 */
void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE, 
            double capitale_iniziale, bool only_hedge) {
    // Itera attraverso tutte le combinazioni di TP e SL
    for (double tp : tp_list) {
        for (double sl : sl_list) {
            TradeResult long_result, short_result;
            bool finitocapitale = false;
            
            // Simula strategia LONG
            double capitale = capitale_iniziale;
            long_result = simulate_strategy(dati, finestra, capitale_per_trade, fee, periodo,
                                         EXIT_MODE_CLOSE, capitale, tp, sl, true);
            finitocapitale = capitale <= capitale_per_trade + 1;
            
            // Stampa risultati LONG se richiesto
            if (!only_hedge) {
                double roi = ((capitale - capitale_iniziale) / capitale_iniziale) * 100.0;
                stampa_riga(tp, sl, "LONG", long_result.percent_success, long_result.ricavi,
                           capitale, long_result.perdite, long_result.fee_totali, roi, long_result.non_chiusi);
            }
            
            // Simula strategia SHORT
            capitale = capitale_iniziale;
            short_result = simulate_strategy(dati, finestra, capitale_per_trade, fee, periodo,
                                          EXIT_MODE_CLOSE, capitale, tp, sl, false);
            finitocapitale |= capitale <= capitale_per_trade + 1;
            
            // Stampa risultati SHORT se richiesto
            if (!only_hedge) {
                double roi = ((capitale - capitale_iniziale) / capitale_iniziale) * 100.0;
                stampa_riga(tp, sl, "SHORT", short_result.percent_success, short_result.ricavi,
                           capitale, short_result.perdite, short_result.fee_totali, roi, short_result.non_chiusi);
            }
            
            // Calcola e stampa risultati della strategia hedge se il capitale non è finito
            if (!finitocapitale) {
                double ricavi_totali = long_result.ricavi + short_result.ricavi;
                double perdite_totali = long_result.perdite + short_result.perdite;
                double fee_totali = long_result.fee_totali + short_result.fee_totali;
                double roi_hedge = (ricavi_totali - perdite_totali - fee_totali) / capitale_iniziale * 100;
                
                stampa_riga(tp, sl, "Hedge", (long_result.percent_success + short_result.percent_success) / 2,
                           ricavi_totali, ricavi_totali - perdite_totali + capitale_iniziale - fee_totali,
                           perdite_totali, fee_totali, roi_hedge, long_result.non_chiusi + short_result.non_chiusi);
            }
        }
    }
}
