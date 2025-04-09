#include "simulator.hpp"
#include "printer.hpp"

extern bool DEBUG;

void simula(const std::vector<double>& tp_list, const std::vector<double>& sl_list,
            const std::vector<Candela>& dati, size_t finestra,
            double capitale_per_trade, double fee) {
    for (double tp : tp_list) {
        for (double sl : sl_list) {
            for (std::string tipo : {"LONG", "SHORT"}) {
                double capitale = 1000.0, ricavi = 0.0, perdite = 0.0, fee_totali = 0.0;
                int successi = 0, fallimenti = 0, non_chiusi = 0;

                for (size_t i = 0; i + finestra < dati.size(); ++i) {
                    double open = dati[i].open;
                    double target_tp = tipo == "LONG" ? open * (1.0 + tp) : open * (1.0 - tp);
                    double target_sl = tipo == "LONG" ? open * (1.0 - sl) : open * (1.0 + sl);
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
                        double profit = capitale_per_trade * tp;
                        double fee_val = capitale_per_trade * fee;
                        ricavi += profit;
                        fee_totali += fee_val;
                        capitale += (profit - fee_val);
                        successi++;
                    } else if (hit_sl) {
                        double loss = capitale_per_trade * sl;
                        double fee_val = capitale_per_trade * fee;
                        perdite += loss;
                        fee_totali += fee_val;
                        capitale -= (loss + fee_val);
                        fallimenti++;
                    } else {
                        non_chiusi++;
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
