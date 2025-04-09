#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <iomanip>
#include <cstdlib>
#include <map>
#include <regex>

struct Candela {
    std::string datetime;
    double open;
    double high;
    double low;
};

bool DEBUG = false;

std::vector<double> parse_range_or_list(int start_idx, int end_idx, char* argv[]) {
    std::vector<double> result;
    std::regex range_pattern(R"((\d*\.?\d*):(\d*\.?\d*):(\d*\.?\d*))");

    for (int i = start_idx; i < end_idx; ++i) {
        std::cmatch match;
        if (std::regex_match(argv[i], match, range_pattern)) {
            double from = std::stod(match[1]);
            double step = std::stod(match[2]);
            double to = std::stod(match[3]);
            for (double val = from; val <= to + 1e-9; val += step) {
                result.push_back(val / 100.0);
            }
        } else {
            result.push_back(std::stod(argv[i]) / 100.0);
        }
    }
    return result;
}

std::vector<Candela> leggi_csv(const std::string& filepath, bool& errore_apertura) {
    std::vector<Candela> dati;
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Errore: impossibile aprire il file '" << filepath << "'\n";
        errore_apertura = true;
        return dati;
    }

    std::string line;
    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string datetime, open, high, low, close, volume;
        std::getline(ss, datetime, ';');
        std::getline(ss, open, ';');
        std::getline(ss, high, ';');
        std::getline(ss, low, ';');
        std::getline(ss, close, ';');
        std::getline(ss, volume, ';');

        try {
            dati.push_back({datetime, std::stod(open), std::stod(high), std::stod(low)});
        } catch (...) {
            continue;
        }
    }
    if (DEBUG) std::cout << "DEBUG: Letti " << dati.size() << " record dal file " << filepath << "\n";
    return dati;
}

void stampa_intestazione_tabella() {
    std::cout << "+------------+------------+------------+--------------+--------------+--------------+--------------+--------------+--------------+--------------+\n";
    std::cout << "| TP %       | SL %       | Direzione  | % Successi   | Ricavi €     | Saldo €      | Perdite €    | Fee €        | ROI netto    | Non chiusi  |\n";
    std::cout << "+------------+------------+------------+--------------+--------------+--------------+--------------+--------------+--------------+--------------+\n";
}

void stampa_riga(double tp, double sl, const std::string& direzione, double percent_success, double ricavi, double capitale, double perdite, double fee_totali, double roi, int non_chiusi) {
    std::cout << "| " << std::setw(10) << std::right << std::fixed << std::setprecision(5) << tp * 100 << "% "
              << "| " << std::setw(10) << sl * 100 << "% "
              << "| " << std::setw(10) << direzione << " "
              << "| " << std::setw(12) << std::setprecision(2) << percent_success << "% "
              << "| " << std::setw(12) << std::fixed << std::setprecision(2) << ricavi << " € "
              << "| " << std::setw(12) << capitale << " € "
              << "| " << std::setw(12) << perdite << " € "
              << "| " << std::setw(12) << fee_totali << " € "
              << "| " << std::setw(10) << roi << "% "
              << "| " << std::setw(10) << non_chiusi << " |" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 9) {
        std::cerr << "Uso: ./simulatore_trading file.csv -W <finestra> -TP <tp1> [tp2 ...] -SL <sl1> [sl2 ...] -C <capitale> -FEE <fee> [-debug]\n";
        return 1;
    }

    std::string filepath = argv[1];
    size_t finestra = 0;
    std::vector<double> tp_list;
    std::vector<double> sl_list;
    double capitale_per_trade = 0.0;
    double fee = 0.0;

    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "-debug") DEBUG = true;
    }

    std::map<std::string, int> flags = { {"-W", 0}, {"-TP", 0}, {"-SL", 0}, {"-C", 0}, {"-FEE", 0} };

    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (flags.count(arg)) {
            flags[arg] = i;
        }
    }

    finestra = std::stoi(argv[flags["-W"] + 1]);
    capitale_per_trade = std::stod(argv[flags["-C"] + 1]);
    fee = std::stod(argv[flags["-FEE"] + 1]) / 100.0;

    int nextFlag = argc;
    for (const auto& [flag, pos] : flags) {
        if (pos > flags["-TP"] && pos < nextFlag && flag != "-TP") {
            nextFlag = pos;
        }
    }
    tp_list = parse_range_or_list(flags["-TP"] + 1, nextFlag, argv);

    nextFlag = argc;
    for (const auto& [flag, pos] : flags) {
        if (pos > flags["-SL"] && pos < nextFlag && flag != "-SL") {
            nextFlag = pos;
        }
    }
    sl_list = parse_range_or_list(flags["-SL"] + 1, nextFlag, argv);

    if (tp_list.size() != sl_list.size()) {
        std::cerr << "Errore: il numero di TP deve corrispondere al numero di SL.\n";
        return 1;
    }

    bool errore_apertura = false;
    std::vector<Candela> dati = leggi_csv(filepath, errore_apertura);
    if (errore_apertura) return -1;

    std::cout << "\nAnalizzati " << dati.size() - finestra << " trade\n\n";
    stampa_intestazione_tabella();

    for (size_t k = 0; k < tp_list.size(); ++k) {
        double tp = tp_list[k];
        double sl = sl_list[k];

        for (std::string tipo : {"LONG", "SHORT"}) {
            double capitale = 1000.0;
            double ricavi = 0.0, perdite = 0.0, fee_totali = 0.0;
            int successi = 0, fallimenti = 0, non_chiusi = 0;

            for (size_t i = 0; i + finestra < dati.size(); ++i) {
                double open = dati[i].open;
                double target_tp = tipo == "LONG" ? open * (1.0 + tp) : open * (1.0 - tp);
                double target_sl = tipo == "LONG" ? open * (1.0 - sl) : open * (1.0 + sl);
                bool hit_tp = false, hit_sl = false;

                for (size_t j = 1; j <= finestra; ++j) {
                    if (tipo == "LONG") {
                        if (dati[i + j].high >= target_tp) { hit_tp = true; break; }
                        if (dati[i + j].low <= target_sl) { hit_sl = true; break; }
                    } else {
                        if (dati[i + j].low <= target_tp) { hit_tp = true; break; }
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
            double percent_success = totale > 0 ? (100.0 * successi / totale) : 0.0;

            stampa_riga(tp, sl, tipo, percent_success, ricavi, capitale, perdite, fee_totali, roi, non_chiusi);
        }
    }

    std::cout << "+------------+------------+------------+--------------+--------------+--------------+--------------+--------------+--------------+--------------+\n";
    return 0;
}
