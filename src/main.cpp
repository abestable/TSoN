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
    double capitale_per_trade = 0.0, fee = 0.0, tp_min = 0, tp_max = 0, sl_min = 0, sl_max = 0;
    int punti = 0;

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
        else if (arg == "-C") capitale_per_trade = std::stod(argv[++i]);
        else if (arg == "-FEE") fee = std::stod(argv[++i]) / 100.0;
    }
std::cout << "DEBUG: TPmin = " << tp_min << "  TPmax = " << tp_max << "  SLmin = " << sl_min << "  SLmax = " << sl_max << std::endl;

    bool errore_apertura = false;
    auto dati = leggi_csv(filepath, errore_apertura);
    if (errore_apertura) return -1;

    auto tp_list = genera_range(tp_min, tp_max, punti);
    auto sl_list = genera_range(sl_min, sl_max, punti);

    
    std::cout << "\nAnalizzati " << dati.size() - finestra << " trade\n\n";
    stampa_intestazione_tabella();
    simula(tp_list, sl_list, dati, finestra, capitale_per_trade, fee);
    stampa_fine_tabella();


    return 0;
}
