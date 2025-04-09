#include "dataloader.hpp"
#include "printer.hpp"
#include "simulator.hpp"
#include <iostream>
#include <vector>
#include <string>

bool DEBUG = false;

int main(int argc, char* argv[]) {
    if (argc < 15) {
        std::cerr << "Uso: ./simulatore_trading file.csv -W <finestra> -TPmin <x> -TPmax <y> -SLmin <a> -SLmax <b> -P <punti> -C <capitale> -FEE <fee> [-debug]\n";
        return 1;
    }

    std::string filepath = argv[1];
    size_t finestra = 0;
    double capitale_per_trade = 0.0, fee = 0.0, tp_min = 0, tp_max = 0, sl_min = 0, sl_max = 0, capitale = 0;
    int punti = 0;
    int periodo = 1;  // default: un trade ogni minuto
    bool EXIT_MODE_CLOSE = true;
    bool exit_mode_found = false;

    for (int i = 1; i < argc; ++i)
        if (std::string(argv[i]) == "-debug") DEBUG = true;

    for (int i = 2; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-W") finestra = std::stoi(argv[++i]);
        else if (arg == "-TPmin") tp_min = std::stod(argv[++i]);
        else if (arg == "-TPmax") tp_max = std::stod(argv[++i]);
        else if (arg == "-SLmin") sl_min = std::stod(argv[++i]);
        else if (arg == "-SLmax") sl_max = std::stod(argv[++i]);
        else if (arg == "-P") punti = std::stoi(argv[++i]);
        else if (arg == "-CPT") capitale_per_trade = std::stod(argv[++i]);
        else if (arg == "-C") capitale = std::stod(argv[++i]);
        else if (arg == "-FEE") fee = std::stod(argv[++i]) / 100.0;
	else if (arg == "-PER") periodo = std::stoi(argv[++i]);
	else if (arg == "-exit_mode") {
	  std::string mode = argv[++i];
	  if (mode == "close") {
	    EXIT_MODE_CLOSE = true;
	    exit_mode_found = true;
	  } else if (mode == "leave") {
	    EXIT_MODE_CLOSE = false;
	    exit_mode_found = true;
	  } else {
	    std::cerr << "Errore: valore non valido per -exit_mode. Usa 'close' oppure 'leave'.\n";
	    return 1;
	  }
	}
    }
    if (!exit_mode_found) {
      std::cerr << "Errore: l'argomento -exit_mode è obbligatorio (usa 'close' o 'leave').\n";
      return 1;
    }

    bool errore_apertura = false;
    auto dati = leggi_csv(filepath, errore_apertura);
    if (errore_apertura) return -1;

    auto tp_list = genera_range(tp_min, tp_max, punti);
    auto sl_list = genera_range(sl_min, sl_max, punti);

    
    stampa_intestazione_tabella();
    simula(tp_list, sl_list, dati, finestra, capitale_per_trade, fee, periodo, EXIT_MODE_CLOSE, capitale);
    stampa_fine_tabella();

    
    std::cout << "\nDati caricati " << dati.size() - finestra << " minuti di storico\n\n";
    size_t n_trade_simulati = (dati.size() > finestra) ? (dati.size() - finestra) / periodo : 0;
    std::cout << "\nAnalizzati " << n_trade_simulati << " trade (ogni " << periodo << " min)\n\n";

    if (!EXIT_MODE_CLOSE) {
      std::cout << "\n*** ATTENZIONE: Il ROI è calcolato solo sui trade chiusi (TP o SL). "
		<< "I trade non chiusi sono esclusi dai risultati. ***\n\n";
    }


    return 0;
}
