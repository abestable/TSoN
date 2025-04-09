#include "simulator.hpp"
#include "printer.hpp"
#include <iostream>
#include <iomanip>


extern bool DEBUG;

void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE) {
  for (double tp : tp_list) {
    for (double sl : sl_list) {
      for (std::string tipo : {"LONG", "SHORT"}) {
	double capitale = 1000.0, ricavi = 0.0, perdite = 0.0, fee_totali = 0.0;
	int successi = 0, fallimenti = 0, non_chiusi = 0;
	for (size_t i = 0; i + finestra < dati.size(); i += periodo) {
	  double open = dati[i].open;
	  double target_tp = tipo == "LONG" ? open * (1.0 + tp / 100.0) : open * (1.0 - tp / 100.0);
	  double target_sl = tipo == "LONG" ? open * (1.0 - sl / 100.0) : open * (1.0 + sl / 100.0);

	  bool hit_tp = false, hit_sl = false;
	  // if (DEBUG && i < 3) { // solo i primi 3 trade per non affollare
	  //   std::cout << "Trade " << i
	  // 	      << " | tipo = " << tipo
	  // 	      << " | Open = " << open
	  // 	      << " | TP = " << tp
	  // 	      << " | SL = " << sl
	  // 	      << " | Target TP = " << target_tp
	  // 	      << " | Target SL = " << target_sl
	  // 	      << " | Fee = " << std::fixed << std::setprecision(4) << fee
	  // 	      << std::endl;
	  // }

	  for (size_t j = 1; j <= finestra; ++j) {
	    if (tipo == "LONG") {
	      if (dati[i + j].high >= target_tp) { hit_tp = true; break; }
	      if (dati[i + j].low <= target_sl)  { hit_sl = true; break; }
	    } else {
	      if (dati[i + j].low <= target_tp)  { hit_tp = true; break; }
	      if (dati[i + j].high >= target_sl) { hit_sl = true; break; }
	    }
	  }

	  if (hit_tp) {
	    double fee_val = capitale_per_trade * fee;
	    double profit = capitale_per_trade * tp / 100.0;
	    ricavi += profit;
	    fee_totali += fee_val;
	    capitale += (profit - fee_val);
	    successi++;
	  } else if (hit_sl) {
	    double loss = capitale_per_trade * sl / 100.0;
	    double fee_val = capitale_per_trade * fee;
	    perdite += loss;
	    fee_totali += fee_val;
	    capitale -= (loss + fee_val);
	    fallimenti++;
	  } 
	  else {
	    if (EXIT_MODE_CLOSE) {
	      double prezzo_exit = dati[i + finestra].close;
	      double variazione = tipo == "LONG"
		? (prezzo_exit - open) / open
		: (open - prezzo_exit) / open;

	      double fee_val = capitale_per_trade * fee;
	      fee_totali += fee_val;

	      if (variazione > 0) {
		double profit = capitale_per_trade * variazione;
		ricavi += profit;
		capitale += (profit - fee_val);
		successi++;
	      } else {
		double loss = capitale_per_trade * (-variazione);
		perdite += loss;
		capitale -= (loss + fee_val);
		fallimenti++;
	      }
	    } else {
	      non_chiusi++;
	    }
	  }
	}
      }

      double totale = successi + fallimenti + non_chiusi;
      double roi = ((capitale - 1000.0) / 1000.0) * 100.0;
      double percent_success = totale > 0 ? 100.0 * successi / totale : 0.0;

      stampa_riga(tp, sl, tipo, percent_success, ricavi, capitale, perdite, fee_totali, roi, non_chiusi);
    }
  }
}
}
