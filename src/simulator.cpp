#include "simulator.hpp"
#include "printer.hpp"
#include <iostream>
#include <iomanip>


extern bool DEBUG;

/**
 * @brief Simulates trading strategies with different take profit (tp) and stop loss (sl) values
 * 
 * This function performs a backtest simulation of trading strategies by testing different
 * combinations of take profit and stop loss values on historical price data.
 * 
 * @param tp_list List of take profit percentages to test
 * @param sl_list List of stop loss percentages to test
 * @param dati Historical price data (candlesticks)
 * @param finestra Maximum number of candles to hold a position
 * @param capitale_per_trade Capital to invest in each trade
 * @param fee Fee percentage for each trade
 * @param periodo Number of candles to skip between trades
 * @param EXIT_MODE_CLOSE If true, close positions at the end of the window if not hit by tp/sl
 * @param capitale_iniziale Initial capital for the simulation
 * @param only_hedge If true, only show hedge strategy results
 */
void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE, double capitale_iniziale, bool only_hedge) {
  // Iterate through all take profit values
  for (double tp : tp_list) {
    // Iterate through all stop loss values
    for (double sl : sl_list) {
      // Initialize variables to track performance metrics for LONG positions
      double  ricaviL = 0.0, perditeL = 0.0, fee_totaliL = 0.0, percent_successiL = 0, non_chiusiL = 0;
      // Initialize variables to track performance metrics for SHORT positions
      double  ricaviS = 0.0, perditeS = 0.0, fee_totaliS = 0.0, percent_successiS = 0, non_chiusiS = 0;
      bool finitocapitale = false;
      
      // Test both LONG and SHORT strategies
      for (std::string tipo : {"LONG", "SHORT"}) {
        // Reset capital for each strategy
        double capitale = capitale_iniziale;
        finitocapitale = false;
        if (DEBUG) std::cout << "reset capitale iniziale: " << capitale_iniziale << std::endl;
        
        // Initialize performance tracking variables
        double ricavi = 0.0, perdite = 0.0, fee_totali = 0.0;
        int successi = 0, fallimenti = 0, non_chiusi = 0;
        
        // Iterate through the price data with the specified period
        for (size_t i = 0; i + finestra < dati.size(); i += periodo) {
          // Check if we have enough capital to open a position
          if (capitale > capitale_per_trade+1) {
            // Get the opening price for the current candle
            double open = dati[i].open;
            if (DEBUG) std::cout << "aperta posizione a: " << dati[i].open << " con capitale disponibile << " << capitale << std::endl ;
            
            // Calculate take profit and stop loss price levels
            double target_tp = tipo == "LONG" ? open * (1.0 + tp / 100.0) : open * (1.0 - tp / 100.0);
            double target_sl = tipo == "LONG" ? open * (1.0 - sl / 100.0) : open * (1.0 + sl / 100.0);
            bool hit_tp = false, hit_sl = false;

            // Check if price hits take profit or stop loss within the window
            for (size_t j = 1; j <= finestra; ++j) {
              if (tipo == "LONG") {
                // For LONG positions: check if high price hits take profit or low price hits stop loss
                if (dati[i + j].high >= target_tp) { hit_tp = true; break; }
                if (dati[i + j].low <= target_sl)  { hit_sl = true; break; }
              } else {
                // For SHORT positions: check if low price hits take profit or high price hits stop loss
                if (dati[i + j].low <= target_tp)  { hit_tp = true; break; }
                if (dati[i + j].high >= target_sl) { hit_sl = true; break; }
              }
            }

            // Handle take profit hit
            if (hit_tp) {
              double fee_val = capitale_per_trade * fee;
              double profit = capitale_per_trade * tp / 100.0;
              ricavi += profit;
              fee_totali += fee_val;
              capitale += (profit - fee_val);
              successi++;
              if (DEBUG) std::cout << "HIT_TP  fee_val " << fee_val <<  std::setw(10) << " profit " << profit << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi << " fails " << fallimenti << std::endl;
            } 
            // Handle stop loss hit
            else if (hit_sl) {
              double loss = capitale_per_trade * sl / 100.0;
              double fee_val = capitale_per_trade * fee;
              perdite += loss;
              fee_totali += fee_val;
              capitale -= (loss + fee_val);
              fallimenti++;
              if (DEBUG) std::cout << "HIT_SL  fee_val " << fee_val << std::setw(10) << " loss " << loss << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
              if (capitale < 0) std::cerr << "Finito il capitale disponibile" << std::endl;
            } 
            // Handle position not closed by tp/sl within the window
            else {
              if (EXIT_MODE_CLOSE) {
                // Close position at the end of the window if EXIT_MODE_CLOSE is true
                double prezzo_exit = dati[i + finestra].close;
                double variazione = tipo == "LONG"
                  ? (prezzo_exit - open) / open
                  : (open - prezzo_exit) / open;

                double fee_val = capitale_per_trade * fee;
                fee_totali += fee_val;

                // Calculate profit or loss based on price change
                if (variazione > 0) {
                  double profit = capitale_per_trade * variazione;
                  ricavi += profit;
                  capitale += (profit - fee_val);
                  successi++;
                  if (DEBUG) std::cout << "timeout fee_val " << fee_val << std::setw(10) << " profit " << profit << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
                } else {
                  double loss = capitale_per_trade * (-variazione);
                  perdite += loss;
                  capitale -= (loss + fee_val);
                  fallimenti++;
                  if (DEBUG) std::cout << "timeout fee_val " << fee_val << std::setw(10) << " loss " << loss << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
                }
              } else {
                // Count positions not closed if EXIT_MODE_CLOSE is false
                non_chiusi++;
              }
            }
          }
          else {
            // Mark that capital has run out
            finitocapitale = true; 
          }
        }
      
        // Calculate performance metrics
        double totale = successi + fallimenti + non_chiusi;
        double roi = ((capitale - capitale_iniziale) / capitale_iniziale) * 100.0;
        double percent_success = totale > 0 ? 100.0 * successi / totale : 0.0;

        // Print results for individual strategy if not only showing hedge
        if (!only_hedge) stampa_riga(tp, sl, tipo, percent_success, ricavi, capitale, perdite, fee_totali, roi, non_chiusi);
        
        // Store results for hedge calculation
        if (tipo == "LONG") {
          ricaviL = ricavi;
          perditeL = perdite;
          fee_totaliL = fee_totali;
          percent_successiL = percent_success;
          non_chiusiL = non_chiusi;
        } else {
          ricaviS = ricavi;
          perditeS = perdite;
          fee_totaliS = fee_totali;
          percent_successiS = percent_success;
          non_chiusiS = non_chiusi;
        }
      }
      
      // Calculate and print hedge strategy results (combining LONG and SHORT)
      double roi_hedge = (ricaviL+ricaviS-perditeL-perditeS-fee_totaliS - fee_totaliL)/capitale_iniziale*100;
      if (!finitocapitale) {
        // Print hedge results if capital hasn't run out
        stampa_riga(tp, sl, "Hedge", (percent_successiL+percent_successiS)/2, ricaviL+ricaviS, 
                   ricaviL+ricaviS-perditeL-perditeS+capitale_iniziale-fee_totaliS-fee_totaliL, 
                   perditeL+perditeS, fee_totaliL+fee_totaliS, roi_hedge, non_chiusiL+non_chiusiS);
      } else {
        // Print message if capital has run out
        std::cout << "finito capitale "<< std::endl;
      }
    }
  }
}
