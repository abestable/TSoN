#include "simulator.hpp"
#include "printer.hpp"
#include <iostream>
#include <iomanip>


extern bool DEBUG;

void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee, int periodo, bool EXIT_MODE_CLOSE, double capitale_iniziale, bool only_hedge) {
  for (double tp : tp_list) {
    for (double sl : sl_list) {
      double  ricaviL = 0.0, perditeL = 0.0, fee_totaliL = 0.0, percent_successiL = 0, non_chiusiL = 0;
      double  ricaviS = 0.0, perditeS = 0.0, fee_totaliS = 0.0, percent_successiS = 0, non_chiusiS = 0;
      for (std::string tipo : {"LONG", "SHORT"}) {
	double capitale = capitale_iniziale;
	if (DEBUG) std::cout << "reset capitale iniziale: " << capitale_iniziale << std::endl;
	double ricavi = 0.0, perdite = 0.0, fee_totali = 0.0;
	int successi = 0, fallimenti = 0, non_chiusi = 0;
	for (size_t i = 0; i + finestra < dati.size(); i += periodo) {
	  // if (capitale > capitale_per_trade+1) {
	  double open = dati[i].open;
	  if (DEBUG) std::cout << "aperta posizione a: " << dati[i].open << " con capitale disponibile << " << capitale << std::endl ;
	  double target_tp = tipo == "LONG" ? open * (1.0 + tp / 100.0) : open * (1.0 - tp / 100.0);
	  double target_sl = tipo == "LONG" ? open * (1.0 - sl / 100.0) : open * (1.0 + sl / 100.0);
	  bool hit_tp = false, hit_sl = false;

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
	    if (DEBUG) std::cout << "HIT_TP  fee_val " << fee_val <<  std::setw(10) << " profit " << profit << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi << " fails " << fallimenti << std::endl;
	  } else if (hit_sl) {
	    double loss = capitale_per_trade * sl / 100.0;
	    double fee_val = capitale_per_trade * fee;
	    perdite += loss;
	    fee_totali += fee_val;
	    capitale -= (loss + fee_val);
	    fallimenti++;
	    if (DEBUG) std::cout << "HIT_SL  fee_val " << fee_val << std::setw(10) << " loss " << loss << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
	    if (capitale < 0) std::cerr << "Finito il capitale disponibile" << std::endl;
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
		if (DEBUG) std::cout << "timeout fee_val " << fee_val << std::setw(10) << " profit " << profit << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
	      } else {
		double loss = capitale_per_trade * (-variazione);
		perdite += loss;
		capitale -= (loss + fee_val);
		fallimenti++;
		if (DEBUG) std::cout << "timeout fee_val " << fee_val << std::setw(10) << " loss " << loss << " ricavi : " << ricavi << " perdite " << perdite << " fee_totali " << fee_totali << " capitale " << capitale << " success " << successi <<  " fails " << fallimenti <<  std::endl;
	      }
	    } else {
	      non_chiusi++;
	    }
	  }
	  
	}
      

      double totale = successi + fallimenti + non_chiusi;
      double roi = ((capitale - capitale_iniziale) / capitale_iniziale) * 100.0;
      double percent_success = totale > 0 ? 100.0 * successi / totale : 0.0;

      if (!only_hedge) stampa_riga(tp, sl, tipo, percent_success, ricavi, capitale, perdite, fee_totali, roi, non_chiusi);
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
      double roi_hedge = (ricaviL+ricaviS-perditeL-perditeS-fee_totaliS - fee_totaliL)/capitale_iniziale*100;
	stampa_riga(tp, sl, "Hedge", (percent_successiL+percent_successiS)/2 , ricaviL+ricaviS, ricaviL+ricaviS-perditeL-perditeS+capitale_iniziale-fee_totaliS-fee_totaliL, perditeL+perditeS, fee_totaliL+fee_totaliS, roi_hedge, non_chiusiL+non_chiusiS);
    }
  }
}
